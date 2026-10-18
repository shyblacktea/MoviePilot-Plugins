from __future__ import annotations

import re
import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.db import db_query, db_update
from app.db.oper.site import Site
from app.schemas.types import EventType, NotificationType
from app.sdk.browser import launch_browser_context
from app.sdk.config import settings
from app.sdk.events import Event, eventmanager
from app.sdk.logging import logger
from app.sdk.plugin import _PluginBase


class AudiencesKeeper(_PluginBase):
    """
    观众站守护者：自动模拟过 Cloudflare 盾更新 Cookie 及自动签到。
    """

    plugin_name = "观众站守护者"
    plugin_desc = "观众站（audiences.me）自动模拟过 CF 盾更新 Cookie 及自动签到。"
    plugin_icon = "https://raw.githubusercontent.com/shyblacktea/MoviePilot-Plugins/main/icons/cloudflare.jpg"
    plugin_version = "0.0.3"
    plugin_author = "shyblacktea"
    author_url = "https://github.com/shyblacktea"
    plugin_config_prefix = "audienceskeeper_"
    plugin_order = 80
    auth_level = 1

    # 运行配置
    _enabled: bool = False
    _site_id: int = 0
    _site_url: str = "https://audiences.me/"
    _signin_enabled: bool = True
    _signin_cron: str = "0 9 * * *"
    _cf_enabled: bool = True
    _cf_cron: str = "0 */2 * * *"
    _notify: bool = True
    _onlyonce: bool = False

    def init_plugin(self, config: dict | None = None) -> None:
        """
        初始化插件配置与运行状态。
        """
        config = config or {}
        self._enabled = bool(config.get("enabled", False))
        self._site_id = int(config.get("site_id") or 0)
        self._site_url = str(config.get("site_url") or "https://audiences.me/").strip()
        self._signin_enabled = bool(config.get("signin_enabled", True))
        self._signin_cron = str(config.get("signin_cron") or "0 9 * * *").strip()
        self._cf_enabled = bool(config.get("cf_enabled", True))
        self._cf_cron = str(config.get("cf_cron") or "0 */2 * * *").strip()
        self._notify = bool(config.get("notify", True))
        self._onlyonce = bool(config.get("onlyonce", False))

        if self._enabled and self._onlyonce:
            logger.info("【观众站守护者】保存配置后触发立即运行一次...")
            self._onlyonce = False
            config["onlyonce"] = False
            self.update_config(config)
            import threading
            threading.Thread(target=self._run_all, daemon=True).start()

    def get_state(self) -> bool:
        """
        返回插件启用状态。
        """
        return self._enabled

    def stop_service(self) -> None:
        """
        停止服务并释放资源。
        """
        self._enabled = False

    def get_service(self) -> list[dict]:
        """
        注册周期定时服务。
        """
        if not self._enabled:
            return []

        services = []
        if self._signin_enabled and self._signin_cron:
            try:
                services.append({
                    "id": f"{self.__class__.__name__}.SignIn",
                    "name": "观众站每日自动签到",
                    "trigger": CronTrigger.from_crontab(self._signin_cron),
                    "func": self.run_signin_job,
                    "kwargs": {},
                })
            except Exception as e:
                logger.error(f"【观众站守护者】注册签到定时任务失败: {e}")

        if self._cf_enabled and self._cf_cron:
            try:
                services.append({
                    "id": f"{self.__class__.__name__}.RefreshCF",
                    "name": "观众站自动过盾更新Cookie",
                    "trigger": CronTrigger.from_crontab(self._cf_cron),
                    "func": self.run_cf_job,
                    "kwargs": {},
                })
            except Exception as e:
                logger.error(f"【观众站守护者】注册过盾定时任务失败: {e}")

        return services

    def get_command(self) -> list[dict[str, Any]]:
        """
        注册远程命令。
        """
        return [
            {
                "cmd": "/audiences_signin",
                "event": EventType.PluginAction,
                "desc": "立即执行观众站自动签到",
                "category": "站点管理",
                "data": {"action": "audiences_signin"},
            },
            {
                "cmd": "/audiences_cookie",
                "event": EventType.PluginAction,
                "desc": "立即模拟过 CF 盾并刷新观众站 Cookie",
                "category": "站点管理",
                "data": {"action": "audiences_cookie"},
            },
        ]

    @eventmanager.register(EventType.PluginAction)
    def handle_command(self, event: Event) -> None:
        """
        处理远程命令事件。
        """
        if not self._enabled:
            return
        action = (event.event_data or {}).get("action")
        if action == "audiences_signin":
            logger.info("【观众站守护者】收到远程命令，立即执行签到...")
            self.run_signin_job()
        elif action == "audiences_cookie":
            logger.info("【观众站守护者】收到远程命令，立即过盾更新 Cookie...")
            self.run_cf_job()

    def get_api(self) -> list[dict[str, Any]]:
        """
        注册插件动态后端 API。
        """
        return [
            {
                "path": "/status",
                "endpoint": self.api_status,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取观众站守护状态",
            },
            {
                "path": "/signin",
                "endpoint": self.api_signin,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "立即执行观众站签到",
            },
            {
                "path": "/refresh_cookie",
                "endpoint": self.api_refresh_cookie,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "立即过盾并更新 Cookie",
            },
        ]

    def api_status(self) -> dict[str, Any]:
        """
        API: 获取状态
        """
        data = self.get_data("state") or {}
        site = self._get_site()
        has_cf = False
        cookie_len = 0
        if site and site.get("cookie"):
            cookie_len = len(site["cookie"])
            has_cf = "cf_clearance=" in site["cookie"]
        return {
            "success": True,
            "data": {
                **data,
                "site_configured": site is not None,
                "site_name": site.get("name") if site else "",
                "site_id": site.get("id") if site else 0,
                "cookie_length": cookie_len,
                "has_cf_clearance": has_cf,
                "current_ua": site.get("ua", "") if site else "",
            }
        }

    def api_signin(self) -> dict[str, Any]:
        """
        API: 立即签到
        """
        success, msg = self.do_signin()
        return {"success": success, "message": msg}

    def api_refresh_cookie(self) -> dict[str, Any]:
        """
        API: 立即过盾刷新
        """
        success, msg = self.do_refresh_cf()
        return {"success": success, "message": msg}

    def _run_all(self) -> None:
        """
        立即执行全部任务（先过盾刷新 Cookie，再签到）。
        """
        self.run_cf_job()
        self.run_signin_job()

    def run_signin_job(self) -> None:
        """
        执行签到任务包装。
        """
        success, msg = self.do_signin()
        logger.info(f"【观众站守护者】签到任务执行结果: {msg}")
        if self._notify:
            self._send_notify(
                title="🎬 观众站每日签到" + ("成功" if success else "未完成"),
                text=f"状态：{'✅ 成功' if success else '⚠️ 需关注'}\n结果反馈：{msg}\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

    def run_cf_job(self) -> None:
        """
        执行过盾与刷新 Cookie 任务包装。
        """
        success, msg = self.do_refresh_cf()
        logger.info(f"【观众站守护者】过盾与刷新 Cookie 结果: {msg}")
        if self._notify:
            self._send_notify(
                title="🛡️ 观众站 CF 盾更新" + ("成功" if success else "失败"),
                text=f"状态：{'✅ 成功' if success else '❌ 失败'}\n详情：{msg}\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

    def do_signin(self) -> tuple[bool, str]:
        """
        核心方法：打开浏览器模拟过 Turnstile 签到。
        """
        site = self._get_site()
        if not site:
            msg = "未找到观众站站点配置（自动匹配 audiences.me 失败），请确认是否已在站点管理中添加观众站。"
            self._append_history("每日签到", False, msg)
            return False, msg

        raw_cookie = site.get("cookie") or ""
        if not raw_cookie:
            msg = f"观众站（ID: {site['id']}）尚未配置基础 Cookie，请先在站点管理填入 Cookie。"
            self._append_history("每日签到", False, msg)
            return False, msg

        cookies = self._parse_cookie_list(raw_cookie, site.get("url") or self._site_url)
        target_url = urllib.parse.urljoin(site.get("url") or self._site_url, "attendance.php")

        logger.info(f"【观众站守护者】启动浏览器访问 {target_url} 执行签到（站点 ID: {site['id']}）...")
        try:
            with launch_browser_context(headless=True) as ctx:
                ctx.add_cookies(cookies)
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
                page.goto(target_url, wait_until="domcontentloaded", timeout=35000)
                page.wait_for_timeout(2000)

                already_keywords = [
                    "您今天已经签到过了",
                    "您今日已经签到过了",
                    "今日已签到",
                    "今天已签到",
                    "已签到",
                    "请勿重复刷新",
                    "明天再来吧",
                ]

                success_keywords = [
                    "签到成功",
                    "本次签到奖励",
                    "获得",
                    "粒爆米花",
                    "点魔力",
                    "奖励已发放",
                ]

                # 1. 检查是否已经签到过
                init_html = page.content()
                if any(k in init_html for k in already_keywords):
                    msg = "您今日已经签到过了，无需重复签到。"
                    self._save_cookies_from_context(ctx, site)
                    self._update_signin_state(True, msg)
                    self._append_history("每日签到", True, msg)
                    return True, msg

                # 2. 若未签到，尝试寻找并点击 Turnstile
                for _ in range(3):
                    if self._click_turnstile_if_present(page):
                        logger.info("【观众站守护者】已检测到并点击 Cloudflare Turnstile 验证框，等待验证提交...")
                        break
                    page.wait_for_timeout(1500)

                # 3. 轮询等待验证结果
                final_msg = ""
                success = False
                for _ in range(8):
                    page.wait_for_timeout(2000)
                    html = page.content()
                    if any(k in html for k in success_keywords):
                        success = True
                        final_msg = "签到成功！本次签到奖励已发放到账户。"
                        break
                    if any(k in html for k in already_keywords):
                        success = True
                        final_msg = "今日已签到（已确认）。"
                        break
                    if "人机验证未通过" in html or "验证失败" in html:
                        final_msg = "人机验证提交失败，请稍后重试。"
                        break

                if not final_msg:
                    # 最后兜底检查一次页面文本
                    html = page.content()
                    if any(k in html for k in already_keywords):
                        success = True
                        final_msg = "今日已签到（已确认）。"
                    else:
                        final_msg = "签到结果未在限定时间内明确确认，请查看网页端。"

                # 提取并回存最新 Cookies
                self._save_cookies_from_context(ctx, site)

                self._update_signin_state(success, final_msg)
                self._append_history("每日签到", success, final_msg)
                return success, final_msg
        except Exception as e:
            err = f"执行签到异常: {str(e)}"
            logger.error(f"【观众站守护者】{err}")
            self._append_history("每日签到", False, err)
            return False, err

    def do_refresh_cf(self) -> tuple[bool, str]:
        """
        核心方法：打开浏览器访问列表页，穿透 CF 盾拿新 clearance，并洗白搜索防刷频次。
        """
        site = self._get_site()
        if not site:
            msg = "未找到观众站站点配置（自动匹配 audiences.me 失败）。"
            self._append_history("过盾与刷新", False, msg)
            return False, msg

        raw_cookie = site.get("cookie") or ""
        cookies = self._parse_cookie_list(raw_cookie, site.get("url") or self._site_url)
        target_url = urllib.parse.urljoin(site.get("url") or self._site_url, "torrents.php")

        logger.info(f"【观众站守护者】启动浏览器访问种子列表页 {target_url} 穿透 CF 并洗白搜索限制（站点 ID: {site['id']}）...")
        try:
            with launch_browser_context(headless=True) as ctx:
                if cookies:
                    ctx.add_cookies(cookies)
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
                page.goto(target_url, wait_until="domcontentloaded", timeout=35000)
                page.wait_for_timeout(2500)

                # 检查并穿透 Turnstile
                for _ in range(3):
                    if self._click_turnstile_if_present(page):
                        break
                    page.wait_for_timeout(1000)

                page.wait_for_timeout(2500)

                # 提取 Cookie 与 UA
                new_cookie_str, new_ua, has_cf = self._save_cookies_from_context(ctx, site)

                title = page.title()
                logger.info(f"【观众站守护者】列表页加载完成，标题: {title}，包含 cf_clearance: {has_cf}")

                msg = f"已访问种子列表页洗白防刷计数；Cookie 已更新（长度 {len(new_cookie_str)}，包含 CF 凭据: {'是' if has_cf else '否'}）。"
                self._update_cf_state(True, msg, has_cf)
                self._append_history("过盾与刷新", True, msg)
                return True, msg
        except Exception as e:
            err = f"过盾与刷新 Cookie 异常: {str(e)}"
            logger.error(f"【观众站守护者】{err}")
            self._append_history("过盾与刷新", False, err)
            return False, err

    def _click_turnstile_if_present(self, page: Any) -> bool:
        """
        遍历各 Frame 定位并点击 Turnstile 复选框。
        """
        for frame in page.frames:
            if "challenges.cloudflare.com" in frame.url or "turnstile" in frame.url:
                try:
                    cb = frame.locator("input[type=checkbox], .ctp-checkbox-label, body")
                    if cb.count() > 0:
                        cb.first.click(timeout=3000)
                        return True
                except Exception as e:
                    logger.debug(f"点击 Turnstile 略过: {e}")
        return False

    def _save_cookies_from_context(self, ctx: Any, site: dict) -> tuple[str, str, bool]:
        """
        从浏览器上下文中抓取全部 Cookie 并热更新到 MoviePilot Site 表。
        """
        domain = urllib.parse.urlparse(site.get("url") or self._site_url).netloc or "audiences.me"
        all_cookies = ctx.cookies()
        page = ctx.pages[0] if ctx.pages else None
        current_ua = page.evaluate("() => navigator.userAgent") if page else ""

        # 合并已有与新获取的 Cookie
        cookie_map: dict[str, str] = {}
        for item in (site.get("cookie") or "").split(";"):
            if "=" in item:
                k, v = item.strip().split("=", 1)
                cookie_map[k] = v

        has_cf = False
        for c in all_cookies:
            c_name = c["name"]
            c_val = c["value"]
            if domain in c.get("domain", "") or not c.get("domain"):
                cookie_map[c_name] = c_val
            if c_name == "cf_clearance":
                has_cf = True

        new_cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_map.items()])
        self._update_site(db=None, site_id=site["id"], cookie=new_cookie_str, ua=current_ua or None)
        return new_cookie_str, current_ua, has_cf

    def _parse_cookie_list(self, raw_cookie: str, base_url: str) -> list[dict[str, str]]:
        """
        把字符串 Cookie 解析为 Playwright 注入格式。
        """
        domain = urllib.parse.urlparse(base_url).netloc or "audiences.me"
        cookies = []
        for item in raw_cookie.split(";"):
            if "=" in item:
                k, v = item.strip().split("=", 1)
                cookies.append({
                    "name": k,
                    "value": v,
                    "domain": domain,
                    "path": "/",
                })
        return cookies

    @db_query
    def _get_site(self, db: Session = None) -> Optional[dict[str, Any]]:
        """
        自动识别并获取观众站点信息：优先全量扫描识别 audiences.me 或观众站点；
        若未扫描到则使用配置的 _site_id。
        """
        site = None
        # 1. 优先自动扫描所有站点
        all_sites = db.query(Site).all()
        for s in all_sites:
            domain = (s.domain or "").lower()
            url = (s.url or "").lower()
            name = (s.name or "").lower()
            if "audiences.me" in domain or "audiences.me" in url or "观众" in name or "audiences" in name:
                site = s
                break

        # 2. 如果自动匹配未找到，尝试用配置的 _site_id
        if not site and self._site_id:
            site = db.query(Site).filter(Site.id == self._site_id).first()

        if not site:
            return None

        return {
            "id": site.id,
            "name": site.name,
            "url": site.url,
            "cookie": site.cookie or "",
            "ua": site.ua or "",
        }

    @db_update
    def _update_site(self, db: Session = None, site_id: int = 0, cookie: str = None, ua: str = None) -> bool:
        """
        热更新观众站点 Cookie 与 UA。
        """
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            return False
        if cookie:
            site.cookie = cookie
        if ua:
            site.ua = ua
        db.flush()
        return True

    def _update_signin_state(self, success: bool, msg: str) -> None:
        state = self.get_data("state") or {}
        state["last_signin_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state["last_signin_success"] = success
        state["last_signin_message"] = msg
        state["last_signin_date"] = datetime.now().strftime("%Y-%m-%d")
        self.save_data("state", state)

    def _update_cf_state(self, success: bool, msg: str, has_cf: bool) -> None:
        state = self.get_data("state") or {}
        state["last_cf_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state["last_cf_success"] = success
        state["last_cf_message"] = msg
        state["has_cf_clearance"] = has_cf
        self.save_data("state", state)

    def _append_history(self, op_type: str, success: bool, detail: str) -> None:
        histories = self.get_data("history") or []
        histories.insert(0, {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": op_type,
            "success": success,
            "detail": detail,
        })
        self.save_data("history", histories[:15])

    def _send_notify(self, title: str, text: str) -> None:
        try:
            self.post_message(
                mtype=NotificationType.SiteMessage,
                title=title,
                text=text,
            )
        except Exception as e:
            logger.warning(f"【观众站守护者】发送通知异常: {e}")

    def get_form(self) -> tuple[list[dict], dict[str, Any]]:
        """
        配置表单。
        """
        return [
            {
                "component": "VForm",
                "content": [
                    {
                        "component": "VAlert",
                        "props": {
                            "type": "info",
                            "variant": "tonal",
                            "class": "mb-4",
                            "text": "本插件针对观众站（audiences.me）设计：自动识别观众站点，模拟穿透 Cloudflare Turnstile 挑战，自动更新 cf_clearance 与真实 UA，解除搜索频次防刷限制，并提供每日自动签到功能。",
                        },
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "enabled",
                                            "label": "启用插件",
                                        },
                                    },
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "notify",
                                            "label": "发送通知",
                                        },
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "site_id",
                                            "label": "观众站点 ID (自动识别)",
                                            "type": "number",
                                            "hint": "默认 0 为自动识别观众站，无需手动指定",
                                        },
                                    },
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "site_url",
                                            "label": "观众站地址",
                                            "hint": "默认 https://audiences.me/",
                                        },
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VDivider",
                        "props": {"class": "my-3"},
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "signin_enabled",
                                            "label": "启用自动每日签到",
                                        },
                                    },
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "signin_cron",
                                            "label": "每日签到时间 (Cron)",
                                            "hint": "默认 0 9 * * * (每天 09:00)",
                                        },
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "cf_enabled",
                                            "label": "启用自动过盾与洗白搜索",
                                        },
                                    },
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "cf_cron",
                                            "label": "过盾与洗白周期 (Cron)",
                                            "hint": "默认 0 */2 * * * (每 2 小时执行一次)",
                                        },
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "onlyonce",
                                            "label": "保存配置后立即运行一次",
                                        },
                                    },
                                ],
                            },
                        ],
                    },
                ],
            }
        ], {
            "enabled": False,
            "site_id": 0,
            "site_url": "https://audiences.me/",
            "signin_enabled": True,
            "signin_cron": "0 9 * * *",
            "cf_enabled": True,
            "cf_cron": "0 */2 * * *",
            "notify": True,
            "onlyonce": False,
        }

    def get_page(self) -> list[dict]:
        """
        插件详情页（展示运行状态与历史）。
        """
        state = self.get_data("state") or {}
        today = datetime.now().strftime("%Y-%m-%d")
        is_today_signed = state.get("last_signin_date") == today and state.get("last_signin_success")

        site = self._get_site()
        has_cf = False
        cookie_len = 0
        site_desc = "未找到观众站"
        if site:
            site_desc = f"{site.get('name', '观众')} (ID: {site.get('id')})"
            if site.get("cookie"):
                cookie_len = len(site["cookie"])
                has_cf = "cf_clearance=" in site["cookie"]

        history = self.get_data("history") or []
        history_rows = []
        for h in history:
            history_rows.append({
                "component": "tr",
                "content": [
                    {"component": "td", "text": h.get("time", "-")},
                    {"component": "td", "text": h.get("type", "-")},
                    {
                        "component": "td",
                        "content": [
                            {
                                "component": "VChip",
                                "props": {
                                    "size": "x-small",
                                    "color": "success" if h.get("success") else "error",
                                    "text": "成功" if h.get("success") else "失败",
                                },
                            }
                        ],
                    },
                    {"component": "td", "text": h.get("detail", "-")},
                ],
            })

        return [
            {
                "component": "VRow",
                "content": [
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 6},
                        "content": [
                            {
                                "component": "VCard",
                                "props": {"variant": "tonal", "class": "pa-4 mb-3"},
                                "content": [
                                    {
                                        "component": "div",
                                        "props": {"class": "d-flex justify-space-between align-center mb-2"},
                                        "content": [
                                            {"component": "h3", "text": "📅 观众每日签到"},
                                            {
                                                "component": "VChip",
                                                "props": {
                                                    "color": "success" if is_today_signed else "warning",
                                                    "size": "small",
                                                    "text": "今日已签到" if is_today_signed else "今日未签到",
                                                },
                                            },
                                        ],
                                    },
                                    {
                                        "component": "div",
                                        "props": {"class": "text-caption text-medium-emphasis mb-1"},
                                        "text": f"绑定站点：{site_desc}",
                                    },
                                    {
                                        "component": "div",
                                        "props": {"class": "text-caption text-medium-emphasis mb-1"},
                                        "text": f"最近签到时间：{state.get('last_signin_time', '暂无记录')}",
                                    },
                                    {
                                        "component": "div",
                                        "props": {"class": "text-body-2"},
                                        "text": f"最近结果：{state.get('last_signin_message', '尚未执行')}",
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 6},
                        "content": [
                            {
                                "component": "VCard",
                                "props": {"variant": "tonal", "class": "pa-4 mb-3"},
                                "content": [
                                    {
                                        "component": "div",
                                        "props": {"class": "d-flex justify-space-between align-center mb-2"},
                                        "content": [
                                            {"component": "h3", "text": "🛡️ CF 盾与 Cookie 状态"},
                                            {
                                                "component": "VChip",
                                                "props": {
                                                    "color": "success" if has_cf else "default",
                                                    "size": "small",
                                                    "text": "含 cf_clearance" if has_cf else "基础 Cookie",
                                                },
                                            },
                                        ],
                                    },
                                    {
                                        "component": "div",
                                        "props": {"class": "text-caption text-medium-emphasis mb-1"},
                                        "text": f"最近刷新时间：{state.get('last_cf_time', '暂无记录')}",
                                    },
                                    {
                                        "component": "div",
                                        "props": {"class": "text-body-2"},
                                        "text": f"Cookie 字符数：{cookie_len} 字符",
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                "component": "VCard",
                "props": {"variant": "outlined", "class": "pa-4 mt-2"},
                "content": [
                    {"component": "h4", "props": {"class": "mb-3"}, "text": "📜 最近执行记录"},
                    {
                        "component": "VTable",
                        "props": {"density": "compact"},
                        "content": [
                            {
                                "component": "thead",
                                "content": [
                                    {
                                        "component": "tr",
                                        "content": [
                                            {"component": "th", "text": "时间"},
                                            {"component": "th", "text": "动作"},
                                            {"component": "th", "text": "状态"},
                                            {"component": "th", "text": "详情"},
                                        ],
                                    }
                                ],
                            },
                            {
                                "component": "tbody",
                                "content": history_rows if history_rows else [
                                    {
                                        "component": "tr",
                                        "content": [
                                            {"component": "td", "props": {"colspan": 4, "class": "text-center text-medium-emphasis"}, "text": "暂无执行记录"}
                                        ]
                                    }
                                ],
                            },
                        ],
                    },
                ],
            },
        ]
