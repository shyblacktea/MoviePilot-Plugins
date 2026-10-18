import pytest
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


def test_audienceskeeper_services():
    plugin = AudiencesKeeper()
    # disabled -> no services
    assert plugin.get_service() == []

    # enabled -> 2 services
    plugin.init_plugin({"enabled": True, "signin_enabled": True, "cf_enabled": True})
    services = plugin.get_service()
    assert len(services) == 2
    assert any("SignIn" in s["id"] for s in services)
    assert any("RefreshCF" in s["id"] for s in services)


def test_audienceskeeper_parse_cookie_list():
    plugin = AudiencesKeeper()
    cookies = plugin._parse_cookie_list("a=1; b=2; c_secure_uid=123", "https://audiences.me/")
    assert len(cookies) == 3
    assert cookies[0]["name"] == "a"
    assert cookies[0]["value"] == "1"
    assert cookies[0]["domain"] == "audiences.me"
