from unittest.mock import patch

from plugins.v3.audienceskeeper import AudiencesKeeper


def _new_plugin(**cfg) -> AudiencesKeeper:
    """
    构造插件实例：绕过需要 MoviePilot 启动组合根才能初始化的 PluginChain，
    只替换测试会触达的基础设施方法（数据存取 / 通知 / 配置回写）。
    """
    plugin = AudiencesKeeper.__new__(AudiencesKeeper)
    plugin.get_data = lambda key, *a, **k: {}
    plugin.save_data = lambda key, val: None
    plugin.update_config = lambda conf: None
    plugin.post_message = lambda **kw: None
    plugin._enabled = False
    plugin._site_id = 0
    plugin._site_url = "https://audiences.me/"
    plugin._cf_enabled = True
    plugin._cf_cron = "0 */2 * * *"
    plugin._notify = True
    plugin._onlyonce = False
    plugin._cf_start_hour = None
    plugin._cf_end_hour = None
    if cfg:
        plugin.init_plugin(cfg)
    return plugin


def test_audienceskeeper_init_and_state():
    plugin = _new_plugin()
    plugin.init_plugin({"enabled": True, "site_id": 12})
    assert plugin.get_state() is True
    assert plugin._site_id == 12

    plugin.stop_service()
    assert plugin.get_state() is False


def test_audienceskeeper_form_has_no_signin():
    plugin = _new_plugin()
    form, defaults = plugin.get_form()
    assert isinstance(form, list)
    assert isinstance(defaults, dict)
    assert defaults["enabled"] is False
    assert defaults["cf_enabled"] is True
    assert defaults["cf_cron"] == "0 */2 * * *"
    assert defaults["clear_history"] is False
    # 签到功能已下线，配置项必须彻底消失
    assert "signin_enabled" not in defaults
    assert "signin_cron" not in defaults
    # 前端输入框已彻底去掉敏感字段
    assert "site_id" not in defaults
    assert "site_url" not in defaults
    assert "proxy" not in defaults
    # 表单里不应再出现任何签到配置项（仅保留一句「站点已下线签到页」的说明）
    assert "启用每日自动签到" not in str(form)
    assert "签到执行周期" not in str(form)
    assert "signin" not in str(form).lower()


def test_audienceskeeper_only_cf_service():
    plugin = _new_plugin()
    assert plugin.get_service() == []

    # 只有 CF 盾任务，不再注册任何签到任务
    plugin.init_plugin({"enabled": True, "cf_cron": "0 */3 * * *"})
    services = plugin.get_service()
    assert len(services) == 1
    assert "RefreshCF" in services[0]["id"]
    assert not any("SignIn" in s["id"] for s in services)

    # 间隔小时写法
    plugin.init_plugin({"enabled": True, "cf_cron": "2.3/9-23"})
    assert plugin._cf_start_hour == 9
    assert plugin._cf_end_hour == 23
    services = plugin.get_service()
    assert len(services) == 1
    assert services[0]["trigger"] == "interval"
    assert services[0]["kwargs"]["hours"] == 2.3

    # 关闭过盾则没有任何任务
    plugin.init_plugin({"enabled": True, "cf_enabled": False})
    assert plugin.get_service() == []


def test_audienceskeeper_no_signin_api_or_command():
    plugin = _new_plugin()
    paths = [api["path"] for api in plugin.get_api()]
    assert "/refresh_cookie" in paths
    assert "/status" in paths
    assert "/signin" not in paths
    assert not any("signin" in p for p in paths)

    cmds = [c["cmd"] for c in plugin.get_command()]
    assert "/audiences_cookie" in cmds
    assert not any("signin" in c.lower() for c in cmds)


def test_audienceskeeper_action_buttons_only_cf():
    plugin = _new_plugin()
    btns_ok = plugin._action_buttons("cf", is_failed=False)
    assert len(btns_ok) == 1
    assert any("过盾" in b["text"] for b in btns_ok[0])
    assert not any("签到" in b["text"] for b in btns_ok[0])

    btns_fail = plugin._action_buttons("cf", is_failed=True)
    assert len(btns_fail) == 2
    assert any("今天不再通知" in b["text"] for b in btns_fail[1])
    assert not any("签到" in b["text"] for b in btns_fail[0])


def test_audienceskeeper_page_and_clear_event():
    plugin = _new_plugin()
    site = {"id": 12, "name": "人人人", "cookie": "a=1", "ua": "test"}
    with patch.object(plugin, "_get_site", return_value=site):
        page = plugin.get_page()
    assert isinstance(page, list)
    tables, clear_btns = [], []
    for row in page:
        for col in row.get("content", []):
            card = col.get("content", [{}])[0]
            for item in card.get("content", []):
                if item.get("component") == "VTable":
                    tables.append(item)
                if item.get("component") == "div":
                    for sub in item.get("content", []):
                        if isinstance(sub, dict) and sub.get("component") == "VBtn" \
                                and "清空" in sub.get("props", {}).get("text", ""):
                            clear_btns.append(sub)
    # 只剩一张过盾记录表
    assert len(tables) == 1
    for t in tables:
        assert t["props"].get("height") == "320px"
        assert t["props"].get("fixed-header") is True

    assert len(clear_btns) == 1
    for btn in clear_btns:
        assert "href" not in btn.get("props", {})
        assert "events" in btn
        assert "clear_history" in btn["events"]["click"]["api"]

    # 页面里不应再出现签到相关文案
    assert "签到" not in str(page)


def test_audienceskeeper_clear_history_purges_legacy_signin():
    plugin = _new_plugin()
    saved = []
    with patch.object(plugin, "save_data", side_effect=lambda k, v: saved.append((k, v))):
        plugin.api_clear_history()
    keys = [k for k, _ in saved]
    assert "cf_history" in keys
    # 历史遗留的签到数据一并清掉
    assert "signin_history" in keys


def test_audienceskeeper_parse_cookie_list():
    plugin = _new_plugin()
    cookies = plugin._parse_cookie_list("a=1; b=2; c_secure_uid=123", "https://audiences.me/")
    assert len(cookies) == 3
    assert cookies[0]["name"] == "a"
    assert cookies[0]["value"] == "1"
