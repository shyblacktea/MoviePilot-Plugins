from unittest.mock import MagicMock, patch
from plugins.v3.audienceskeeper import AudiencesKeeper


def test_audienceskeeper_init_and_state():
    plugin = AudiencesKeeper()
    plugin.init_plugin({"enabled": True, "site_id": 12})
    assert plugin.get_state() is True
    assert plugin._site_id == 12

    plugin.stop_service()
    assert plugin.get_state() is False


def test_audienceskeeper_form():
    plugin = AudiencesKeeper()
    form, defaults = plugin.get_form()
    assert isinstance(form, list)
    assert isinstance(defaults, dict)
    assert defaults["enabled"] is False
    assert defaults["signin_enabled"] is True
    assert defaults["cf_enabled"] is True
    assert defaults["cf_cron"] == "0 */2 * * *"
    assert defaults["clear_history"] is False
    # 验证前端输入框已彻底去掉敏感字段
    assert "site_id" not in defaults
    assert "site_url" not in defaults
    assert "proxy" not in defaults


def test_audienceskeeper_services_cron_and_intervals():
    plugin = AudiencesKeeper()
    assert plugin.get_service() == []

    # 1. 5位 cron 签到 + 独立 CF 盾刷新
    plugin.init_plugin({"enabled": True, "signin_cron": "30 9 * * *", "cf_cron": "0 */3 * * *"})
    services = plugin.get_service()
    assert len(services) == 2
    assert any("SignIn" in s["id"] for s in services)
    assert any("RefreshCF" in s["id"] for s in services)

    # 2. 签到间隔范围 2.3/9-23
    plugin.init_plugin({"enabled": True, "signin_cron": "2.3/9-23", "cf_enabled": False})
    assert plugin._signin_start_hour == 9
    assert plugin._signin_end_hour == 23
    services = plugin.get_service()
    assert len(services) == 1
    assert services[0]["trigger"] == "interval"
    assert services[0]["kwargs"]["hours"] == 2.3

    # 3. 签到留空默认随机 2 次
    with patch.object(AudiencesKeeper, "_get_random_schedule") as mock_sched:
        from datetime import datetime
        mock_sched.return_value = [datetime(2026, 10, 19, 10, 15), datetime(2026, 10, 19, 16, 45)]
        plugin.init_plugin({"enabled": True, "signin_cron": "", "cf_enabled": False})
        services = plugin.get_service()
        assert len(services) == 2
        assert services[0]["trigger"] == "cron"
        assert services[0]["kwargs"]["hour"] == 10
        assert services[0]["kwargs"]["minute"] == 15


def test_audienceskeeper_action_buttons():
    plugin = AudiencesKeeper()
    btns_ok = plugin._action_buttons("signin", is_failed=False)
    assert len(btns_ok) == 1
    assert any("重新签到" in b["text"] for b in btns_ok[0])

    btns_fail = plugin._action_buttons("signin", is_failed=True)
    assert len(btns_fail) == 2
    assert any("今天不再通知" in b["text"] for b in btns_fail[1])


def test_audienceskeeper_page_and_clear_event():
    plugin = AudiencesKeeper()
    with patch.object(plugin, "_get_site", return_value={"id": 12, "name": "人人人", "cookie": "a=1", "ua": "test"}):
        page = plugin.get_page()
        assert isinstance(page, list)
        tables = []
        clear_btns = []
        for row in page:
            for col in row.get("content", []):
                card = col.get("content", [{}])[0]
                for item in card.get("content", []):
                    if item.get("component") == "VTable":
                        tables.append(item)
                    if item.get("component") == "div":
                        for sub in item.get("content", []):
                            if isinstance(sub, dict) and sub.get("component") == "VBtn" and "清空" in sub.get("props", {}).get("text", ""):
                                clear_btns.append(sub)
        assert len(tables) >= 2
        for t in tables:
            assert t["props"].get("height") == "320px"
            assert t["props"].get("fixed-header") is True

        assert len(clear_btns) >= 2
        for btn in clear_btns:
            assert "href" not in btn.get("props", {})
            assert "events" in btn
            assert "clear_history" in btn["events"]["click"]["api"]


def test_audienceskeeper_parse_cookie_list():
    plugin = AudiencesKeeper()
    cookies = plugin._parse_cookie_list("a=1; b=2; c_secure_uid=123", "https://audiences.me/")
    assert len(cookies) == 3
    assert cookies[0]["name"] == "a"
    assert cookies[0]["value"] == "1"
