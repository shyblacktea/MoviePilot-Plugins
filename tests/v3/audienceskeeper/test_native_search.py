"""Offline regression of the real search method; no live site requests."""
import unittest
from unittest.mock import Mock
from test_refresh_regression import load_plugin

class NativeSearchTests(unittest.TestCase):
    def setUp(self):
        cls,self.ns=load_plugin()
        self.plugin=cls()
        self.page=Mock()
        self.page.url='https://example.invalid/torrents.php?search=1080p'
        self.events=[]
        self.field=Mock()
        self.field.count.return_value=1
        self.page.locator.return_value.first=self.field
        self.field.click.side_effect=lambda **kw:self.events.append('click')
        self.field.fill.side_effect=lambda value,**kw:self.events.append(('fill',value))
        self.field.press.side_effect=lambda value,**kw:self.events.append(('press',value))
        self.plugin._goto_robust=Mock(return_value=(True,'ok'))
        self.plugin._wait_search_verification=Mock(side_effect=lambda page:self.events.append('verified') or True)
        self.plugin._has_cf_challenge=Mock(return_value=False)
        self.plugin._validate_page=Mock(return_value=(True,100,'ok'))

    def test_search_uses_interaction_and_native_submit_not_a_constructed_url(self):
        result=self.plugin._probe_search_page(self.page,{'url':'https://example.invalid/'})
        self.assertEqual(self.events,['click',('fill','1080p'),'verified',('press','Enter')])
        self.plugin._goto_robust.assert_not_called()
        self.assertEqual(result,(True,100,False))

    def test_incomplete_verification_never_submits(self):
        self.plugin._wait_search_verification.return_value=False
        self.plugin._wait_search_verification.side_effect=None
        self.assertEqual(self.plugin._probe_search_page(self.page,{'url':'https://example.invalid/'}),(False,0,True))
        self.field.press.assert_not_called()

    def test_unchanged_list_page_is_not_search_success(self):
        self.page.url='https://example.invalid/torrents.php'
        self.assertEqual(self.plugin._probe_search_page(self.page,{'url':'https://example.invalid/'}),(False,0,False))
        self.plugin._validate_page.assert_not_called()

    def test_submission_exception_fails_closed(self):
        self.field.press.side_effect=TimeoutError('private diagnostics')
        self.assertEqual(self.plugin._probe_search_page(self.page,{'url':'https://example.invalid/'}),(False,0,False))
        self.plugin._validate_page.assert_not_called()

    def test_verification_wait_is_bounded_and_checks_token(self):
        for facts, expected in (({'required':False,'ready':False,'challenge':False},True),({'required':True,'ready':True,'challenge':False},True),({'required':True,'ready':False,'challenge':False},False)):
            plugin,_=load_plugin()
            p=plugin()
            page=Mock()
            page.evaluate.return_value=facts
            self.assertEqual(p._wait_search_verification(page),expected)
            self.assertLessEqual(page.evaluate.call_count,20)

    def test_route_allows_cloudflare_resources_and_blocks_site_media(self):
        cls, _ = load_plugin()
        self.assertTrue(cls._should_allow_route('https://challenges.cloudflare.com/turnstile/v0/api.js', 'script'))
        self.assertTrue(cls._should_allow_route('https://challenges.cloudflare.com/cdn-cgi/challenge-platform/font.woff2', 'font'))
        self.assertTrue(cls._should_allow_route('https://audiences.me/torrents.php', 'document'))
        self.assertFalse(cls._should_allow_route('https://audiences.me/pic/poster.jpg', 'image'))
        self.assertFalse(cls._should_allow_route('https://audiences.me/static/font.woff2', 'font'))

    def test_solve_cf_challenge_polls_and_clicks_until_cleared(self):
        cls, _ = load_plugin()
        p = cls()
        page = Mock()
        states = iter([True, True, False, False])
        p._has_cf_challenge = Mock(side_effect=lambda pg: next(states, False))
        p._turnstile_state = Mock(return_value='')
        p._click_turnstile_if_present = Mock(return_value=True)
        self.assertTrue(p._solve_cf_challenge(page, timeout_s=5))
        p._click_turnstile_if_present.assert_called()

if __name__=='__main__': unittest.main()
