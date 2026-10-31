from __future__ import annotations

import re
import urllib.parse
from datetime import datetime
from typing import Any, Optional

from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.db import db_query, db_update
from app.db.oper.site import Site
from app.schemas.types import EventType, NotificationType
from app.sdk.browser import launch_browser_context
from app.sdk.events import Event, eventmanager
from app.sdk.logging import logger
from app.sdk.plugin import _PluginBase


class AudiencesKeeper(_PluginBase):
    """
    人人人守护者：自动模拟过 Cloudflare 盾，更新 Cookie 并洗白搜索防刷计数。

    站点已下线签到页（attendance.php 返回 404），本插件自 0.0.9 起只保留
    过盾 / Cookie 维护能力，不再包含任何签到逻辑。
    """

    plugin_name = "人人人守护者"
    plugin_desc = "人人人自动模拟过 CF 盾、更新 Cookie 并洗白搜索防刷计数。"
    plugin_icon = "https://raw.githubusercontent.com/shyblacktea/MoviePilot-Plugins/main/icons/cloudflare.jpg"
    plugin_version = "0.0.9"
    plugin_author = "shyblacktea"
    author_url = "https://github.com/shyblacktea"
    plugin_config_prefix = "audienceskeeper_"
    plugin_order = 80
    auth_level = 1

    # 运行配置
    _enabled: bool = False
    _site_id: int = 0
    _site_url: str = "https://audiences.me/"
    _cf_enabled: bool = True
    _cf_cron: str = "0 */2 * * *"
    _notify: bool = True
    _onlyonce: bool = False

    # CF 盾时间限制
    _cf_start_hour: Optional[int] = None
    _cf_end_hour: Optional[int] = None

    def init_plugin(self, config: dict | None = None) -> None:
        """
        初始化插件配置与运行状态。
        """
        config = config or {}
        self._enabled = bool(config.get("enabled", False))
        self._site_id = int(config.get("site_id") or 0)
        self._site_url = str(config.get("site_url") or "https://audiences.me/").strip()

        # CF 盾刷新周期（默认 0 */2 * * * 每 2 小时）
        self._cf_enabled = bool(config.get("cf_enabled", True))
        self._cf_cron = str(config.get("cf_cron") or "0 */2 * * *").strip()

        self._notify = bool(config.get("notify", True))
        self._onlyonce = bool(config.get("onlyonce", False))

        # 解析 CF 盾周期的时间范围（例如 2/9-23）
        self._cf_start_hour = None
        self._cf_end_hour = None
        if self._cf_cron and "/" in self._cf_cron:
            try:
                parts = self._cf_cron.split("/")
                if len(parts) == 2 and "-" in parts[1]:
                    time_range = parts[1].split("-")
                    self._cf_start_hour = int(time_range[0])
                    self._cf_end_hour = int(time_range[1])
            except Exception as e:
                logger.error(f"【人人人守护者】解析CF盾时间范围异常: {e}")

        if bool(config.get("clear_history", False)):
            logger.info("【人人人守护者】收到清空历史记录请求，正在清空...")
            self.save_data("cf_history", [])
            self.save_data("history", [])
            # 0.0.9 起不再有签到功能，顺手清掉历史遗留的签到记录
            self.save_data("signin_history", [])
            config["clear_history"] = False
            self.update_config(config)

        if self._enabled and self._onlyonce:
            logger.info("【人人人守护者】保存配置后触发立即运行一次...")
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
        注册周期定时服务：仅保留 CF 盾与洗白搜索。
        """
        if not self._enabled:
            return []

        services = []

        if self._cf_enabled and self._cf_cron:
            cf_str = self._cf_cron.strip()
            try:
                if cf_str.count(" ") == 4:
                    services.append({
                        "id": f"{self.__class__.__name__}.RefreshCF",
                        "name": "人人人自动过盾与洗白搜索",
                        "trigger": CronTrigger.from_crontab(cf_str),
                        "func": self.run_cf_job,
                        "kwargs": {},
                    })
                elif "/" in cf_str:
                    parts = cf_str.split("/")
                    hours = float(parts[0].strip())
                    services.append({
                        "id": f"{self.__class__.__name__}.RefreshCF",
                        "name": "人人人自动过盾与洗白搜索",
                        "trigger": "interval",
                        "func": self.run_cf_job,
                        "kwargs": {"hours": hours},
                    })
                else:
                    hours = float(cf_str)
                    services.append({
                        "id": f"{self.__class__.__name__}.RefreshCF",
                        "name": "人人人自动过盾与洗白搜索",
                        "trigger": "interval",
                        "func": self.run_cf_job,
                        "kwargs": {"hours": hours},
                    })
            except Exception as e:
                logger.error(f"【人人人守护者】注册过盾定时任务失败 ({cf_str}): {e}")

        return services

    def run_cf_job(self, is_manual: bool = False) -> None:
        """
        过盾与洗白搜索任务入口（独立周期调度）。
        """
        if not self._enabled:
            return

        now = datetime.now()
        if not is_manual and self._cf_start_hour is not None and self._cf_end_hour is not None:
            if now.hour < self._cf_start_hour or now.hour > self._cf_end_hour:
                logger.info(
                    f"【人人人守护者】当前时间 {now.hour} 不在过盾时间范围 {self._cf_start_hour}-{self._cf_end_hour} 内，跳过执行"
                )
                return

        success, msg = self.do_refresh_cf()
        logger.info(f"【人人人守护者】过盾与刷新 Cookie 结果: {msg}")

        # 手动执行或失败时推送通知（定期自动过盾成功保持静默，避免每两小时刷屏）
        if is_manual:
            self._notify_job_result(
                key="cf",
                success=success,
                title="🛡️ 人人人 CF 盾更新" + ("成功" if success else "失败"),
                body=f"状态：{'✅ 成功' if success else '❌ 失败'}\n详情：{msg}",
                is_manual=True,
            )
        elif not success:
            self._notify_job_result(
                key="cf",
                success=False,
                title="🛡️ 人人人 CF 盾更新失败",
                body=f"状态：❌ 失败\n详情：{msg}",
                is_manual=False,
            )

    def _notify_job_result(self, key: str, success: bool, title: str, body: str,
                           is_manual: bool = False, **kwargs: Any) -> None:
        """
        通知分发与防刷规则：
        1. 成功通知：每天只通知一次（除非手动触发）；
        2. 失败通知：支持用户点击「今天不再通知」后当天完全静默。
        """
        if not self._notify and not is_manual:
            return

        today = datetime.now().strftime("%Y-%m-%d")
        state = self.get_data("state") or {}

        if success:
            if not is_manual:
                if state.get("last_success_notify_date") == today:
                    logger.info("【人人人守护者】今日已发送过成功通知，本次执行成功保持静默，不再重复打扰。")
                    return
                state["last_success_notify_date"] = today
                self.save_data("state", state)

            self._send_notify(
                title=title,
                text=f"{body}\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                buttons=self._action_buttons(key, is_failed=False),
                **kwargs,
            )
        else:
            if not is_manual:
                if state.get("mute_fail_date") == today:
                    logger.info("【人人人守护者】用户已设置今日静默失败通知，本次重试失败保持静默。")
                    return

            self._send_notify(
                title=title,
                text=f"{body}\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                buttons=self._action_buttons(key, is_failed=True),
                **kwargs,
            )

    def get_command(self) -> list[dict[str, Any]]:
        """
        注册远程命令。
        """
        return [
            {
                "cmd": "/audiences_cookie",
                "event": EventType.PluginAction,
                "desc": "立即模拟过 CF 盾并刷新人人人 Cookie",
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
        if action == "audiences_cookie":
            logger.info("【人人人守护者】收到远程命令，立即过盾更新 Cookie...")
            self.run_cf_job(is_manual=True)

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
        channel = data.get("channel")
        source = data.get("source")
        userid = data.get("userid")
        msg_id = data.get("original_message_id")
        chat_id = data.get("original_chat_id")
        today = datetime.now().strftime("%Y-%m-%d")

        # 1. 响应「🔕 今天不再通知」
        if action == "mute_fail_today":
            logger.info(f"【人人人守护者】用户设置今日不再接收失败通知（来自 {userid}）")
            state = self.get_data("state") or {}
            state["mute_fail_date"] = today
            self.save_data("state", state)
            self._send_notify(
                title="🔕 今日失败通知已静默",
                text=f"已设置今日不再推送失败告警通知，今日后续重试失败将保持静默，次日自动恢复。\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                buttons=[[
                    {"text": "🔔 恢复通知", "callback_data": f"[PLUGIN]{self.__class__.__name__}|unmute_fail_today"}
                ]],
                channel=channel,
                source=source,
                userid=userid,
                original_message_id=msg_id,
                original_chat_id=chat_id,
            )
            return

        # 2. 响应「🔔 恢复通知」
        if action == "unmute_fail_today":
            logger.info(f"【人人人守护者】用户取消今日静默，恢复失败通知（来自 {userid}）")
            state = self.get_data("state") or {}
            state["mute_fail_date"] = ""
            self.save_data("state", state)
            self._send_notify(
                title="🔔 今日失败通知已恢复",
                text=f"已恢复正常推送失败告警通知。\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                buttons=self._action_buttons("cf", is_failed=True),
                channel=channel,
                source=source,
                userid=userid,
                original_message_id=msg_id,
                original_chat_id=chat_id,
            )
            return

        if action != "cf":
            return

        logger.info(f"【人人人守护者】收到按钮回调：刷新 CF 盾（来自 {userid}）")

        def _run() -> None:
            try:
                self._send_notify(
                    title="🛡️ 正在刷新 CF 盾…",
                    text=f"已收到指令，正在启动浏览器执行，请稍候。\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    channel=channel,
                    source=source,
                    userid=userid,
                    original_message_id=msg_id,
                    original_chat_id=chat_id,
                )
            except Exception:
                pass

            success, msg = self.do_refresh_cf()
            title = "🛡️ 人人人 CF 盾更新" + ("成功" if success else "失败")
            body = f"状态：{'✅ 成功' if success else '❌ 失败'}\n详情：{msg}"

            self._send_notify(
                title=title,
                text=f"{body}\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                buttons=self._action_buttons("cf", is_failed=not success),
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
                "summary": "获取人人人守护状态",
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
                "site_name": "人人人" if site else "",
                "site_id": site.get("id") if site else 0,
                "cookie_length": cookie_len,
                "has_cf_clearance": has_cf,
                "current_ua": site.get("ua", "") if site else "",
            }
        }

    def api_refresh_cookie(self) -> dict[str, Any]:
        """
        API: 立即过盾刷新（带按钮的通知，属于手动触发）
        """
        self.run_cf_job(is_manual=True)
        state = self.get_data("state") or {}
        return {
            "success": bool(state.get("last_cf_success")),
            "message": state.get("last_cf_message") or "",
        }

    def api_clear_history(self) -> dict[str, Any]:
        """
        API: 清空历史（通过 MoviePilot 前端内置 events 异步事件触发，不进行页面跳转）
        """
        self.save_data("cf_history", [])
        self.save_data("history", [])
        self.save_data("signin_history", [])
        return {"success": True, "message": "历史记录已全部清空"}

    def _run_all(self) -> None:
        """
        立即执行全量任务（手动全量）：当前只剩过盾与洗白。
        """
        self.run_cf_job(is_manual=True)

    def _action_buttons(self, primary: str, is_failed: bool = False) -> list[list[dict]]:
        """
        构造交互按钮：主操作 + 辅助操作；失败时附带「🔕 今天不再通知」。
        """
        pid = self.__class__.__name__
        pairs = {
            "cf": [("🛡️ 重新过盾", "cf")],
        }
        buttons = [[
            {"text": text, "callback_data": f"[PLUGIN]{pid}|{action}"}
            for text, action in pairs.get(primary, [])
        ]]
        if is_failed:
            buttons.append([
                {"text": "🔕 今天不再通知", "callback_data": f"[PLUGIN]{pid}|mute_fail_today"}
            ])
        return buttons

    def do_refresh_cf(self) -> tuple[bool, str]:
        """
        核心方法：打开浏览器访问列表页，穿透 CF 盾拿新 clearance，并洗白搜索防刷频次。
        """
        site = self._get_site()
        if not site:
            msg = "未找到人人人站点配置。"
            self._append_history("过盾与刷新", False, msg)
            return False, msg

        raw_cookie = site.get("cookie") or ""
        cookies = self._parse_cookie_list(raw_cookie, site.get("url") or self._site_url)
        target_url = urllib.parse.urljoin(site.get("url") or self._site_url, "torrents.php")

        logger.info(f"【人人人守护者】启动浏览器访问种子列表页穿透 CF 并洗白搜索限制（站点 ID: {site['id']}）...")
        try:
            with launch_browser_context(headless=True, **self._browser_kwargs()) as ctx:
                if cookies:
                    ctx.add_cookies(cookies)
                self._harden_page(ctx)
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
                nav_ok, nav_msg = self._goto_robust(page, target_url)
                if not nav_ok:
                    msg = f"打开种子列表页失败（{nav_msg}），请检查网络连接。"
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
                logger.info(f"【人人人守护者】列表页加载完成，标题: {title}，包含 cf_clearance: {has_cf}")

                msg = f"已访问种子列表页洗白防刷计数；Cookie 已更新（长度 {len(new_cookie_str)}，包含 CF 凭据: {'是' if has_cf else '否'}）。"
                self._update_cf_state(True, msg, has_cf)
                self._append_history("过盾与刷新", True, msg)
                return True, msg
        except Exception as e:
            err = f"过盾与刷新 Cookie 异常: {str(e)}"
            logger.error(f"【人人人守护者】{err}")
            self._append_history("过盾与刷新", False, err)
            return False, err

    def _browser_kwargs(self) -> dict:
        """
        组装浏览器启动参数：固定中文环境直连。
        """
        return {
            "locale": "zh-CN",
            "timezone": "Asia/Shanghai",
            "viewport": {"width": 1600, "height": 1000},
        }

    def _harden_page(self, ctx: Any) -> None:
        """
        屏蔽图片/字体/媒体等非必要资源，显著缩短大页面加载时间。
        """
        try:
            ctx.route(
                "**/*",
                lambda route: route.abort()
                if route.request.resource_type in ("image", "font", "media")
                else route.continue_(),
            )
        except Exception as e:
            logger.debug(f"【人人人守护者】资源拦截设置失败（不影响功能）: {e}")

    def _goto_robust(self, page: Any, url: str, rounds: int = 3) -> tuple[bool, str]:
        """
        健壮导航：先 commit 抢到达，再给 DOM 就绪留时间；失败自动重试。
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
                if "NexusPHP" in title or "种子" in title or "Audiences" in title or page.url.startswith(url.split("/torrents.php")[0]):
                    return True, f"页面已就绪（第 {i + 1} 次尝试）"
                last_err = f"页面标题异常：{title!r}"
            except Exception as e:
                last_err = f"{type(e).__name__}: {str(e)[:80]}"
            logger.warning(f"【人人人守护者】导航第 {i + 1} 次未完成：{last_err}")
            try:
                page.wait_for_timeout(1500)
            except Exception:
                pass

        try:
            if page.url and url.split("/")[2] in page.url:
                return True, "导航超时但已进入目标站点，按部分成功继续"
        except Exception:
            pass
        return False, last_err

    def _get_cf_token(self, page: Any) -> str:
        """
        读取 Turnstile 当前令牌。
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
                logger.debug("【人人人守护者】Turnstile: iframe checkbox 已点击")
                return True
        except Exception as e:
            logger.debug(f"【人人人守护者】Turnstile iframe checkbox 点击失败: {e}")

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
                    logger.debug("【人人人守护者】Turnstile: 已按坐标点击复选框区域")
                    return True
        except Exception as e:
            logger.debug(f"【人人人守护者】Turnstile 坐标点击失败: {e}")

        # 策略 3：直接点击组件容器
        try:
            page.locator(".cf-turnstile").first.click(timeout=2500, force=True)
            logger.debug("【人人人守护者】Turnstile: 已点击组件容器")
            return True
        except Exception as e:
            logger.debug(f"【人人人守护者】Turnstile 组件点击失败: {e}")
        return False

    def _turnstile_state(self, page: Any) -> str:
        """
        读取 Turnstile iframe 当前状态文本。
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

    def _save_cookies_from_context(self, ctx: Any, site: dict) -> tuple[str, str, bool]:
        """
        从浏览器上下文中抓取全部 Cookie 并热更新到 MoviePilot Site 表。
        """
        domain = urllib.parse.urlparse(site.get("url") or self._site_url).netloc or "audiences.me"
        all_cookies = ctx.cookies()
        page = ctx.pages[0] if ctx.pages else None
        current_ua = page.evaluate("() => navigator.userAgent") if page else ""

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
        自动全量匹配识别对应站点。
        """
        site = None
        all_sites = db.query(Site).all()
        for s in all_sites:
            domain = (s.domain or "").lower()
            url = (s.url or "").lower()
            name = (s.name or "").lower()
            if "audiences.me" in domain or "audiences.me" in url or "观众" in name or "audiences" in name or "人人人" in name:
                site = s
                break

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
        热更新站点 Cookie 与 UA。
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
        # 综合记录保留 50 条
        histories = self.get_data("history") or []
        histories.insert(0, record)
        self.save_data("history", histories[:50])

        # 过盾/刷新分类记录
        cf_hist = self.get_data("cf_history") or []
        cf_hist.insert(0, record)
        self.save_data("cf_history", cf_hist[:50])

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
            logger.warning(f"【人人人守护者】发送通知异常: {e}")

    def get_form(self) -> tuple[list[dict], dict[str, Any]]:
        """
        配置表单：全自动识别站点（隐藏ID和地址），只保留过盾与洗白配置。
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
                            "text": "本插件针对人人人设计：全自动识别站点，模拟穿透 Cloudflare Turnstile 挑战，自动更新 cf_clearance 与真实 UA，解除搜索频次防刷限制。当前仅保留过盾与 Cookie 维护能力。",
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
                                            "hint": "成功通知每日仅首次推送一次；失败通知可一键设为今日不再提醒。",
                                            "persistent-hint": True,
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
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "cf_enabled",
                                            "label": "启用过盾与洗白搜索",
                                        },
                                    },
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 8},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "cf_cron",
                                            "label": "过盾与洗白执行周期",
                                            "placeholder": "默认 0 */2 * * * (每 2 小时执行一次)",
                                            "hint": "支持：1、5位cron表达式（默认 0 */2 * * *）；2、配置间隔小时（如 2 或 3 表示每隔N小时）；3、留空默认每 2 小时。定期访问列表页刷新 cf_clearance 并重置搜索防刷频次。",
                                            "persistent-hint": True,
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
                                            "hint": "开启后保存配置即可清空过盾与 Cookie 更新记录",
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
            "cf_enabled": True,
            "cf_cron": "0 */2 * * *",
            "notify": True,
            "onlyonce": False,
            "clear_history": False,
        }

    def get_page(self) -> list[dict]:
        """
        插件详情页：CF 盾状态 + 支持独立滚动的过盾记录面板。
        清空操作走内置 events 异步事件，杜绝页面跳转。
        """
        state = self.get_data("state") or {}

        site = self._get_site()
        has_cf = False
        cookie_len = 0
        site_desc = "未找到站点"
        if site:
            site_desc = f"人人人 (ID: {site.get('id')})"
            if site.get("cookie"):
                cookie_len = len(site["cookie"])
                has_cf = "cf_clearance=" in site["cookie"]

        def _make_table_rows(records: list) -> list:
            rows = []
            for h in records:
                rows.append({
                    "component": "tr",
                    "content": [
                        {"component": "td", "props": {"class": "text-no-wrap"}, "text": h.get("time", "-")},
                        {
                            "component": "td",
                            "props": {"class": "text-no-wrap"},
                            "content": [
                                {
                                    "component": "VChip",
                                    "props": {
                                        "size": "x-small",
                                        "color": "warning",
                                        "variant": "tonal",
                                        "text": "🛡️ 过盾",
                                    },
                                }
                            ],
                        },
                        {
                            "component": "td",
                            "props": {"class": "text-no-wrap"},
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

        # 原生异步清空按钮：使用 MoviePilot 前端内置 events 机制，杜绝浏览器跳转
        clear_event = {
            "api": f"plugin/{self.__class__.__name__}/clear_history",
            "method": "post",
        }
        clear_btn = {
            "component": "VBtn",
            "props": {
                "size": "x-small",
                "color": "error",
                "variant": "tonal",
                "text": "清空记录",
                "prepend-icon": "mdi-delete-sweep",
            },
            "events": {
                "click": clear_event,
            },
        }

        cf_history = self.get_data("cf_history") or []

        # 兼容旧历史（仅取过盾类记录；签到记录已随功能下线不再展示）
        if not cf_history:
            for item in self.get_data("history") or []:
                if "签到" not in item.get("type", "") and "登录" not in item.get("type", ""):
                    cf_history.append(item)

        cf_rows = _make_table_rows(cf_history[:30])

        return [
            {
                "component": "VRow",
                "content": [
                    {
                        "component": "VCol",
                        "props": {"cols": 12},
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
                                        "text": f"绑定站点：{site_desc}",
                                    },
                                    {
                                        "component": "div",
                                        "props": {"class": "text-caption text-medium-emphasis mb-1"},
                                        "text": f"最近刷新时间：{state.get('last_cf_time', '暂无记录')}",
                                    },
                                    {
                                        "component": "div",
                                        "props": {"class": "text-caption text-medium-emphasis mb-1"},
                                        "text": f"Cookie 字符数：{cookie_len} 字符",
                                    },
                                    {
                                        "component": "div",
                                        "props": {"class": "text-body-2"},
                                        "text": f"最近结果：{state.get('last_cf_message', '尚未执行')}",
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
                        "props": {"cols": 12},
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
                                        "props": {
                                            "density": "compact",
                                            "height": "320px",
                                            "fixed-header": True,
                                            "style": "overflow-y: auto;",
                                        },
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
                                                            {
                                                                "component": "td",
                                                                "props": {"colspan": 4, "class": "text-center text-medium-emphasis"},
                                                                "text": "暂无过盾记录",
                                                            }
                                                        ],
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
