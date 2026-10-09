from pathlib import Path

SOURCE = Path(__file__).parents[3] / "plugins.v3/followupshy/__init__.py"


def test_v3_identity_fields_are_used():
    text = SOURCE.read_text()
    assert "class FollowUpShy" in text
    assert "plugin_config_prefix = \"followupshy_\"" in text
    assert "sub.media_id" in text
    assert "item.media_id" in text
    assert "SubscribeHistory.media_id" in text
    assert ".tmdbid" not in text
    assert "item.tmdb_id" not in text


def test_follow_up_skips_already_subscribed_sequels():
    text = SOURCE.read_text()
    assert "subscribed_items = self._get_subscribed_items()" in text
    assert "if self._is_subscribed(mediainfo, subscribed_items):" in text
    assert "if self._is_subscribed(latest_part, subscribed_items):" in text
    assert "已存在订阅，跳过续作通知" in text


def test_clean_media_info_and_prepare_payload_no_legacy_fields():
    text = SOURCE.read_text()
    assert 'plugin_version = "0.0.3"' in text
    assert "def _prepare_subscribe_payload" in text
    assert '"tmdbid": mediainfo.tmdb_id' not in text
    assert '"doubanid": mediainfo.douban_id' not in text
    assert '"bangumiid": mediainfo.bangumi_id' not in text
    assert '"media_source": MediaSource.TMDB.value' in text
    assert '"media_id": str(mediainfo.tmdb_id)' in text


def test_prepare_subscribe_payload_cleans_legacy_keys():
    import sys
    sys.path.insert(0, str(SOURCE.parents[1]))
    from followupshy import FollowUpShy
    from app.application.subscription.contract import _SUBSCRIPTION_FIELDS
    from app.schemas.types import MediaSource

    plugin = FollowUpShy.__new__(FollowUpShy)
    legacy_data = {
        "title": "沧元图",
        "year": "2023",
        "tmdbid": 229192,
        "doubanid": None,
        "bangumiid": None,
        "episode_group": None,
        "season": 1,
        "start_episode": 0,
    }
    prepared = plugin._prepare_subscribe_payload(legacy_data)
    assert prepared["media_source"] == MediaSource.TMDB
    assert prepared["media_id"] == "229192"
    assert "tmdbid" not in prepared
    assert "doubanid" not in prepared
    assert "bangumiid" not in prepared

    option_keys = set(prepared.keys()) - {
        "title",
        "year",
        "mtype",
        "episode_group",
        "season",
        "media_source",
        "media_id",
    }
    unknown = sorted(option_keys - _SUBSCRIPTION_FIELDS)
    assert not unknown
