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
    plugin_version = "0.0.6"
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
    _proxy: str = ""

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
        self._proxy = str(config.get("proxy") or "").strip()

        if bool(config.get("clear_history", False)):
            logger.info("【观众站守护者】收到清空历史记录请求，正在清空...")
            self.save_data("cf_history", [])
            self.save_data("signin_history", [])
            self.save_data("history", [])
            config["clear_history"] = False
            self.update_config(config)

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

    @eventmanager.register(EventType.MessageAction)
    def message_action(self, event: Event) -> None:
        """
        处理通知里的按钮回调：原消息原地刷新结果，不新增消息。
        """
        data = event.event_data or {}
        pid = str(data.get("plugin_id") or "")
        if pid not in (self.__class__.__name__, self.plugin_config_prefix):
            return
        if not self._enabled:
            return

        action = str(data.get("text") or "").strip().lower()
        if action not in ("signin", "cf"):
            return

        channel = data.get("channel")
        source = data.get("source")
        userid = data.get("userid")
        msg_id = data.get("original_message_id")
        chat_id = data.get("original_chat_id")
        logger.info(f"【观众站守护者】收到按钮回调：{action}（来自 {userid}）")

        def _run() -> None:
            doing = "📅 正在签到" if action == "signin" else "🛡️ 正在刷新 CF 盾"
            try:
                self._send_notify(
                    title=doing + "…",
                    text=f"已收到指令，正在启动浏览器执行，请稍候。\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    channel=channel,
                    source=source,
                    userid=userid,
                    original_message_id=msg_id,
                    original_chat_id=chat_id,
                )
            except Exception:
                pass

            if action == "signin":
                success, msg = self.do_signin()
                title = "🎬 观众站每日签到" + ("成功" if success else "未完成")
                body = f"状态：{'✅ 成功' if success else '⚠️ 需关注'}\n结果反馈：{msg}"
                key = "signin"
            else:
                success, msg = self.do_refresh_cf()
                title = "🛡️ 观众站 CF 盾更新" + ("成功" if success else "失败")
                body = f"状态：{'✅ 成功' if success else '❌ 失败'}\n详情：{msg}"
                key = "cf"

            self._send_notify(
                title=title,
                text=f"{body}\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                buttons=self._action_buttons(key),
                channel=channel,
                source=source,
                userid=userid,
                original_message_id=msg_id,
                original_chat_id=chat_id,
            )

        import threading
        threading.Thread(target=_run, daemon=True).start()

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
            {
                "path": "/clear_history",
                "endpoint": self.api_clear_history,
                "methods": ["GET", "POST"],
                "auth": "bear",
                "summary": "清空执行记录",
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
        API: 立即签到（与定时任务一致，会推送带按钮的通知）
        """
        self.run_signin_job()
        state = self.get_data("state") or {}
        return {
            "success": bool(state.get("last_signin_success")),
            "message": state.get("last_signin_message") or "",
        }

    def api_refresh_cookie(self) -> dict[str, Any]:
        """
        API: 立即过盾刷新（与定时任务一致，会推送带按钮的通知）
        """
        self.run_cf_job()
        state = self.get_data("state") or {}
        return {
            "success": bool(state.get("last_cf_success")),
            "message": state.get("last_cf_message") or "",
        }

    def api_clear_history(self) -> dict[str, Any]:
        """
        API: 清空历史
        """
        self.save_data("cf_history", [])
        self.save_data("signin_history", [])
        self.save_data("history", [])
        return {"success": True, "message": "历史记录已全部清空"}

    def _run_all(self) -> None:
        """
        立即执行全部任务（先过盾刷新 Cookie，再签到）。
        """
        self.run_cf_job()
        self.run_signin_job()

    def _action_buttons(self, primary: str) -> list[list[dict]]:
        """
        构造交互按钮：主操作 + 另一项操作，点击后即时执行。
        """
        pid = self.__class__.__name__
        pairs = {
            "signin": [("🔁 重新签到", "signin"), ("🛡️ 刷新CF盾", "cf")],
            "cf": [("🛡️ 重新过盾", "cf"), ("📅 立即签到", "signin")],
        }
        return [[
            {"text": text, "callback_data": f"[PLUGIN]{pid}|{action}"}
            for text, action in pairs.get(primary, [])
        ]]

    def run_signin_job(self) -> None:
        """
        执行签到任务包装。
        """
        success, msg = self.do_signin()
        logger.info(f"【观众站守护者】签到任务执行结果: {msg}")
        if self._notify:
            self._send_notify(
                title="🎬 观众站每日签到" + ("成功" if success else "未完成"),
                text=f"状态：{'✅ 成功' if success else '⚠️ 需关注'}\n结果反馈：{msg}\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                buttons=self._action_buttons("signin"),
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
                text=f"状态：{'✅ 成功' if success else '❌ 失败'}\n详情：{msg}\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                buttons=self._action_buttons("cf"),
            )

    def do_signin(self) -> tuple[bool, str]:
        """
        核心方法：打开浏览器模拟过 Turnstile 签到，严格基于 DOM 元素卡片状态验证结果。
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

        logger.info(f"【观众站守护者】启动仿真浏览器访问 {target_url} 执行签到（站点 ID: {site['id']}）...")
        try:
            with launch_browser_context(headless=True, **self._browser_kwargs()) as ctx:
                ctx.add_cookies(cookies)
                self._harden_page(ctx)
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
                nav_ok, nav_msg = self._goto_robust(page, target_url)
                if not nav_ok:
                    msg = f"打开签到页失败（{nav_msg}），请检查网络或填写浏览器专用代理。"
                    self._append_history("每日签到", False, msg)
                    return False, msg
                page.wait_for_timeout(1500)

                # 1. 精准检查是否已经签到过（基于卡片类名与顶部用户栏状态，杜绝匹配静态文字）
                is_attended_userbar = page.locator(".site-userbar__compact-tool--attended").count() > 0
                has_done_card = page.locator(".attendance-card--done, .attendance-card__icon--done").count() > 0

                card_title = (
                    page.locator(".attendance-card__title").first.inner_text().strip()
                    if page.locator(".attendance-card__title").count() > 0
                    else ""
                )
                card_desc = (
                    page.locator(".attendance-card__desc").first.inner_text().strip()
                    if page.locator(".attendance-card__desc").count() > 0
                    else ""
                )

                if is_attended_userbar or has_done_card or "今天已签到" in card_title or "已签到" in card_title:
                    msg = card_desc or "您今天已经签到过了，请勿重复刷新。"
                    self._save_cookies_from_context(ctx, site)
                    self._update_signin_state(True, msg)
                    self._append_history("每日签到", True, msg)
                    return True, msg

                # 2. 尚未签到：执行 Turnstile 求解（多策略点击 + 长轮询令牌）
                logger.info("【观众站守护者】检测到尚未签到，开始求解 Turnstile 人机验证...")
                ts_ok, ts_diag = self._solve_turnstile(page)

                # 3. 等待表单提交后的结果（DOM 卡片状态为准）
                final_msg = ""
                success = False
                for _ in range(10):
                    page.wait_for_timeout(1500)
                    has_success = page.locator(".attendance-card__icon--success").count() > 0
                    has_done = page.locator(".attendance-card--done, .attendance-card__icon--done").count() > 0
                    is_now_attended = page.locator(".site-userbar__compact-tool--attended").count() > 0
                    cur_title = (
                        page.locator(".attendance-card__title").first.inner_text().strip()
                        if page.locator(".attendance-card__title").count() > 0
                        else ""
                    )
                    cur_desc = (
                        page.locator(".attendance-card__desc").first.inner_text().strip()
                        if page.locator(".attendance-card__desc").count() > 0
                        else ""
                    )
                    if has_success or "签到成功" in cur_title:
                        success = True
                        final_msg = cur_desc or "签到成功！本次签到奖励已发放到账户。"
                        break
                    if has_done or is_now_attended or "今天已签到" in cur_title or "已签到" in cur_title:
                        success = True
                        final_msg = cur_desc or "今日已签到（已确认）。"
                        break

                if not final_msg:
                    final_msg = f"签到未完成：{ts_diag}"

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
            with launch_browser_context(headless=True, **self._browser_kwargs()) as ctx:
                if cookies:
                    ctx.add_cookies(cookies)
                self._harden_page(ctx)
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
                nav_ok, nav_msg = self._goto_robust(page, target_url)
                if not nav_ok:
                    msg = f"打开种子列表页失败（{nav_msg}），请检查网络或填写浏览器专用代理。"
                    self._append_history("过盾与刷新", False, msg)
                    return False, msg
                page.wait_for_timeout(1500)

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

    def _browser_kwargs(self) -> dict:
        """
        组装浏览器启动参数：可选代理 + 固定中文环境。
        """
        kw: dict[str, Any] = {
            "locale": "zh-CN",
            "timezone": "Asia/Shanghai",
            "viewport": {"width": 1600, "height": 1000},
        }
        if self._proxy:
            kw["proxy"] = self._proxy
        return kw

    def _harden_page(self, ctx: Any) -> None:
        """
        屏蔽图片/字体/媒体等非必要资源，显著缩短观众站大页面加载时间。
        """
        try:
            ctx.route(
                "**/*",
                lambda route: route.abort()
                if route.request.resource_type in ("image", "font", "media")
                else route.continue_(),
            )
        except Exception as e:
            logger.debug(f"【观众站守护者】资源拦截设置失败（不影响功能）: {e}")

    def _goto_robust(self, page: Any, url: str, rounds: int = 3) -> tuple[bool, str]:
        """
        健壮导航：先 commit 抢到达，再给 DOM 就绪留时间；失败自动重试。

        观众站列表页体积大且依赖外链资源，`domcontentloaded` 在网络抖动时极易 35s 超时，
        但这不代表页面真的打不开。故采用 commit 优先 + 多轮重试 + 软成功判定。

        :return: (是否可用, 说明)
        """
        last_err = ""
        for i in range(rounds):
            try:
                page.goto(url, wait_until="commit", timeout=20000)
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=12000)
                except Exception:
                    pass
                page.wait_for_timeout(1200)
                title = ""
                try:
                    title = page.title() or ""
                except Exception:
                    pass
                if "Audiences" in title or page.url.startswith(url.split("/torrents.php")[0]):
                    return True, f"页面已就绪（第 {i + 1} 次尝试）"
                last_err = f"页面标题异常：{title!r}"
            except Exception as e:
                last_err = f"{type(e).__name__}: {str(e)[:80]}"
            logger.warning(f"【观众站守护者】导航第 {i + 1} 次未完成（{url}）：{last_err}")
            try:
                page.wait_for_timeout(1500)
            except Exception:
                pass

        # 软成功：虽然导航超时，但可能已拿到响应并写入 Cookie
        try:
            if page.url and url.split("/")[2] in page.url:
                return True, "导航超时但已进入目标站点，按部分成功继续"
        except Exception:
            pass
        return False, last_err

    def _get_cf_token(self, page: Any) -> str:
        """
        读取 Turnstile 当前令牌（兼容 cf-token 隐藏域与标准 response 输入）。
        """
        try:
            token = page.evaluate(
                "() => {"
                "  const a = document.getElementById('cf-token');"
                "  if (a && a.value) return a.value;"
                "  const b = document.querySelector('[name=cf-turnstile-response]');"
                "  if (b && b.value) return b.value;"
                "  return '';"
                "}"
            )
            return token or ""
        except Exception:
            return ""

    def _click_turnstile_if_present(self, page: Any) -> bool:
        """
        尝试点击 Turnstile 复选框：iframe 内 checkbox → 坐标点击 → 组件点击。
        """
        # 策略 1：frame 内真实 checkbox
        try:
            fl = page.frame_locator("iframe[src*='challenges.cloudflare.com']")
            cb = fl.locator("input[type=checkbox]")
            if cb.count() > 0:
                cb.first.click(timeout=2500, force=True)
                logger.debug("【观众站守护者】Turnstile: iframe checkbox 已点击")
                return True
        except Exception as e:
            logger.debug(f"【观众站守护者】Turnstile iframe checkbox 点击失败: {e}")

        # 策略 2：按真实鼠标坐标点击组件左侧（checkbox 所在区域）
        try:
            widget = page.locator(".cf-turnstile")
            if widget.count() > 0:
                widget.first.scroll_into_view_if_needed(timeout=2000)
                page.wait_for_timeout(300)
                box = widget.first.bounding_box()
                if box:
                    x = box["x"] + 30
                    y = box["y"] + box["height"] / 2
                    page.mouse.move(x, y, steps=8)
                    page.wait_for_timeout(150)
                    page.mouse.click(x, y)
                    logger.debug("【观众站守护者】Turnstile: 已按坐标点击复选框区域")
                    return True
        except Exception as e:
            logger.debug(f"【观众站守护者】Turnstile 坐标点击失败: {e}")

        # 策略 3：直接点击组件容器
        try:
            page.locator(".cf-turnstile").first.click(timeout=2500, force=True)
            logger.debug("【观众站守护者】Turnstile: 已点击组件容器")
            return True
        except Exception as e:
            logger.debug(f"【观众站守护者】Turnstile 组件点击失败: {e}")
        return False

    def _turnstile_state(self, page: Any) -> str:
        """
        读取 Turnstile iframe 当前状态文本，用于失败诊断。
        """
        for frame in page.frames:
            if "challenges.cloudflare.com" in frame.url:
                try:
                    txt = frame.evaluate(
                        "() => document.body ? document.body.innerText.replace(/\\s+/g,' ').trim().slice(0,80) : ''"
                    )
                    if txt:
                        return txt
                    if "Checking your Browser" in (frame.content() or ""):
                        return "Checking your Browser"
                except Exception:
                    continue
        return ""

    def _solve_turnstile(self, page: Any, timeout_s: int = 60) -> tuple[bool, str]:
        """
        求解 Turnstile：多策略点击 + 长轮询令牌，返回 (是否成功, 诊断描述)。

        失败诊断可区分三类原因：
        - 当前网络出口被 Cloudflare 风控（长期停在 Checking your Browser）；
        - 组件未渲染 / 页面结构异常；
        - 点击后仍未下发令牌（需人工介入）。
        """
        import time as _time

        # 等组件渲染；若组件不存在，先判定是否其实已签到 / 页面未渲染
        try:
            page.wait_for_selector(".cf-turnstile", timeout=12000)
        except Exception:
            try:
                title_now = page.locator(".attendance-card__title").all_text_contents()
                joined = "".join(title_now)
                if "已签到" in joined or "签到成功" in joined:
                    return True, "页面已显示签到完成"
                if not title_now:
                    # 连签到卡片都没有：页面没真正渲染出来
                    return False, "签到页未完成渲染（可能是网络抖动或 Cloudflare 拦截），请重试"
            except Exception:
                pass
            return False, "页面上未找到 Turnstile 组件（页面结构可能已变更）"

        deadline = _time.time() + timeout_s
        clicks = 0
        stuck_rounds = 0
        last_state = ""

        while _time.time() < deadline:
            token = self._get_cf_token(page)
            if token:
                logger.info("【观众站守护者】Turnstile 令牌已获取，等待表单自动提交...")
                return True, "已获取 Turnstile 令牌"

            state = self._turnstile_state(page)
            if state:
                last_state = state
                if "Checking your Browser" in state:
                    stuck_rounds += 1

            # 仍在人机验证环节且点击次数未用尽 → 继续尝试点击
            if clicks < 3:
                if self._click_turnstile_if_present(page):
                    clicks += 1
                    logger.info(f"【观众站守护者】第 {clicks} 次尝试点击 Turnstile 复选框...")

            page.wait_for_timeout(2000)

        # 超时诊断
        if stuck_rounds >= 5 or "Checking your Browser" in last_state:
            return False, (
                "Turnstile 长时间停留在『Checking your Browser』，说明当前网络的出口 IP 被 "
                "Cloudflare 判定为高风险（常见于机房/VPN/被标记的代理节点）。请在插件配置里"
                "填写一条能过盾的代理，或让 MoviePilot 所在网络直连后再试。"
            )
        if not last_state:
            return False, "Turnstile 组件存在但未返回任何状态，可能被浏览器插件或网络中间设备拦截。"
        return False, f"Turnstile 未在 {timeout_s} 秒内下发令牌（组件状态：{last_state[:40]}）。"

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
        record = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": op_type,
            "success": success,
            "detail": detail,
        }
        # 综合记录
        histories = self.get_data("history") or []
        histories.insert(0, record)
        self.save_data("history", histories[:20])

        # 分类独立记录
        if "签到" in op_type:
            signin_hist = self.get_data("signin_history") or []
            signin_hist.insert(0, record)
            self.save_data("signin_history", signin_hist[:15])
        else:
            cf_hist = self.get_data("cf_history") or []
            cf_hist.insert(0, record)
            self.save_data("cf_history", cf_hist[:15])

    def _send_notify(self, title: str, text: str,
                     buttons: Optional[list[list[dict]]] = None, **kwargs: Any) -> None:
        """
        发送通知；buttons 传按钮矩阵，kwargs 可带 original_message_id 等用于原地编辑。
        """
        try:
            self.post_message(
                mtype=NotificationType.Plugin,
                title=title,
                text=text,
                buttons=buttons,
                **kwargs,
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
                            {
                                "component": "VCol",
                                "props": {"cols": 12},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "proxy",
                                            "label": "浏览器专用代理（可选）",
                                            "hint": "形如 http://192.168.0.x:7890 或 socks5://ip:port。Turnstile 一直卡在 Checking your Browser 时填写可解决",
                                            "clearable": True,
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
                                "props": {"cols": 12, "md": 6},
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
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "clear_history",
                                            "label": "清空执行历史记录",
                                            "hint": "开启后保存配置即可清空所有过盾和签到记录",
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
            "clear_history": False,
            "proxy": "",
        }

    def get_page(self) -> list[dict]:
        """
        插件详情页（展示运行状态与清晰分类的历史记录）。
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

        def _make_table_rows(records: list) -> list:
            rows = []
            for h in records:
                is_cf = "过盾" in h.get("type", "")
                rows.append({
                    "component": "tr",
                    "content": [
                        {"component": "td", "text": h.get("time", "-")},
                        {
                            "component": "td",
                            "content": [
                                {
                                    "component": "VChip",
                                    "props": {
                                        "size": "x-small",
                                        "color": "warning" if is_cf else "primary",
                                        "variant": "tonal",
                                        "text": "🛡️ 过盾" if is_cf else "📅 签到",
                                    },
                                }
                            ],
                        },
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
            return rows

        clear_url = (
            f"/api/v1/plugin/{self.__class__.__name__}/clear_history"
            f"?apikey={settings.API_TOKEN}"
        )
        clear_btn = {
            "component": "VBtn",
            "props": {
                "size": "x-small",
                "color": "error",
                "variant": "tonal",
                "href": clear_url,
                "text": "清空记录",
                "prepend-icon": "mdi-delete-sweep",
            },
        }

        cf_history = self.get_data("cf_history") or []
        signin_history = self.get_data("signin_history") or []

        # 兼容旧单列表
        if not cf_history and not signin_history:
            old_h = self.get_data("history") or []
            for item in old_h:
                if "签到" in item.get("type", ""):
                    signin_history.append(item)
                else:
                    cf_history.append(item)

        cf_rows = _make_table_rows(cf_history[:10])
        signin_rows = _make_table_rows(signin_history[:10])

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
                "component": "VRow",
                "content": [
                    {
                        "component": "VCol",
                        "props": {"cols": 12, "md": 6},
                        "content": [
                            {
                                "component": "VCard",
                                "props": {"variant": "outlined", "class": "pa-3"},
                                "content": [
                                    {
                                        "component": "div",
                                        "props": {"class": "d-flex align-center justify-space-between mb-2"},
                                        "content": [
                                            {"component": "h4", "text": "📅 每日签到记录"},
                                            clear_btn,
                                        ],
                                    },
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
                                                            {"component": "th", "text": "类型"},
                                                            {"component": "th", "text": "状态"},
                                                            {"component": "th", "text": "反馈"},
                                                        ],
                                                    }
                                                ],
                                            },
                                            {
                                                "component": "tbody",
                                                "content": signin_rows if signin_rows else [
                                                    {
                                                        "component": "tr",
                                                        "content": [
                                                            {"component": "td", "props": {"colspan": 4, "class": "text-center text-medium-emphasis"}, "text": "暂无签到记录"}
                                                        ]
                                                    }
                                                ],
                                            },
                                        ],
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
                                "props": {"variant": "outlined", "class": "pa-3"},
                                "content": [
                                    {
                                        "component": "div",
                                        "props": {"class": "d-flex align-center justify-space-between mb-2"},
                                        "content": [
                                            {"component": "h4", "text": "🛡️ CF 过盾与 Cookie 更新记录"},
                                            clear_btn,
                                        ],
                                    },
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
                                                            {"component": "th", "text": "类型"},
                                                            {"component": "th", "text": "状态"},
                                                            {"component": "th", "text": "反馈"},
                                                        ],
                                                    }
                                                ],
                                            },
                                            {
                                                "component": "tbody",
                                                "content": cf_rows if cf_rows else [
                                                    {
                                                        "component": "tr",
                                                        "content": [
                                                            {"component": "td", "props": {"colspan": 4, "class": "text-center text-medium-emphasis"}, "text": "暂无过盾记录"}
                                                        ]
                                                    }
                                                ],
                                            },
                                        ],
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ]
