try:
    import pytest
except ImportError:
    pytest = None
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
    assert defaults["site_id"] == 0
    assert defaults["enabled"] is False
    assert defaults["signin_enabled"] is True
    assert defaults["clear_history"] is False
    assert defaults["cron"] == ""


def test_audienceskeeper_services_cron_and_intervals():
    plugin = AudiencesKeeper()
    assert plugin.get_service() == []

    # 1. 5位 cron
    plugin.init_plugin({"enabled": True, "cron": "30 9 * * *"})
    services = plugin.get_service()
    assert len(services) == 1
    assert "MainJob" in services[0]["id"]

    # 2. 间隔范围 2.3/9-23
    plugin.init_plugin({"enabled": True, "cron": "2.3/9-23"})
    assert plugin._start_time == 9
    assert plugin._end_time == 23
    services = plugin.get_service()
    assert len(services) == 1
    assert services[0]["trigger"] == "interval"
    assert services[0]["kwargs"]["hours"] == 2.3

    # 3. 留空默认随机 2 次
    with patch.object(AudiencesKeeper, "_get_random_schedule") as mock_sched:
        from datetime import datetime
        mock_sched.return_value = [datetime(2026, 10, 19, 10, 15), datetime(2026, 10, 19, 16, 45)]
        plugin.init_plugin({"enabled": True, "cron": ""})
        services = plugin.get_service()
        assert len(services) == 2
        assert services[0]["trigger"] == "cron"
        assert services[0]["kwargs"]["hour"] == 10
        assert services[0]["kwargs"]["minute"] == 15


def test_audienceskeeper_action_buttons():
    plugin = AudiencesKeeper()
    # 成功按钮
    btns_ok = plugin._action_buttons("signin", is_failed=False)
    assert len(btns_ok) == 1
    assert any("重新签到" in b["text"] for b in btns_ok[0])

    # 失败按钮带「今天不再通知」
    btns_fail = plugin._action_buttons("signin", is_failed=True)
    assert len(btns_fail) == 2
    assert any("今天不再通知" in b["text"] for b in btns_fail[1])


def test_audienceskeeper_scrollable_page():
    plugin = AudiencesKeeper()
    with patch.object(plugin, "_get_site", return_value={"id": 12, "name": "观众", "cookie": "a=1", "ua": "test"}):
        page = plugin.get_page()
        assert isinstance(page, list)
        # 验证表格存在固定高度和滚动条属性
        tables = []
        for row in page:
            for col in row.get("content", []):
                card = col.get("content", [{}])[0]
                for item in card.get("content", []):
                    if item.get("component") == "VTable":
                        tables.append(item)
        assert len(tables) >= 2
        for t in tables:
            assert t["props"].get("height") == "320px"
            assert t["props"].get("fixed-header") is True


def test_audienceskeeper_parse_cookie_list():
    plugin = AudiencesKeeper()
    cookies = plugin._parse_cookie_list("a=1; b=2; c_secure_uid=123", "https://audiences.me/")
    assert len(cookies) == 3
    assert cookies[0]["name"] == "a"
    assert cookies[0]["value"] == "1"
    assert cookies[0]["domain"] == "audiences.me"
