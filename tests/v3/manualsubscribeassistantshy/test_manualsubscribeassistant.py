import pytest
from unittest.mock import MagicMock, patch

from plugins.v3.manualsubscribeassistantshy.core.models import (
    RankMediaItem,
    SubscribeOutcome,
    SubscribeStatus,
    media_identity,
)
from plugins.v3.manualsubscribeassistantshy.core.subscribes import SubscribeManager


def test_media_identity():
    # test tmdb identity
    id1 = media_identity(tmdb_id=123, is_tv=False, title="Test Movie")
    assert id1 == "tmdb_m_123"

    id2 = media_identity(tmdb_id=456, is_tv=True, season=2, title="Test TV")
    assert id2 == "tmdb_t_456_s2"

    # test douban identity
    id3 = media_identity(douban_id="99999", title="Test Douban")
    assert id3 == "douban_99999"


def test_subscribe_manager_state():
    mock_oper = MagicMock()
    mgr = SubscribeManager(mock_oper)

    res = mgr.set_state([1, 2], "R")
    assert res["ok"] == 2
    assert mock_oper.update.call_count == 2

    with pytest.raises(ValueError):
        mgr.set_state([1], "INVALID_STATE")
