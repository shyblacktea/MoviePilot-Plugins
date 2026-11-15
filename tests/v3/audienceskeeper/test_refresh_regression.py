"""Offline regressions for the real plugin methods; only host/browser I/O is mocked.
Run with: python -m unittest discover -s tests/v3/audienceskeeper -p test_refresh_regression.py
AST loading avoids importing a running MoviePilot composition root.
"""
import ast
import copy
import json
import shutil
import subprocess
from datetime import datetime
import os
from pathlib import Path
import re
from typing import Any, Optional
import unittest
from unittest.mock import Mock
import urllib.parse


def load_plugin():
    path = Path(os.environ.get('KEEPER_SOURCE', Path(__file__).resolve().parents[3] / 'plugins.v3/audienceskeeper/__init__.py'))
    tree = ast.parse(path.read_text(encoding='utf-8'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'AudiencesKeeper')
    cls.bases = []
    for method in cls.body:
        if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            method.decorator_list = [d for d in method.decorator_list if isinstance(d, ast.Name) and d.id in ('staticmethod', 'classmethod')]
    module = ast.fix_missing_locations(ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), cls], type_ignores=[]))
    ns = {'re': re, 'urllib': urllib, 'datetime': datetime, 'Any': Any, 'Optional': Optional, 'logger': Mock()}
    exec(compile(module, str(path), 'exec'), ns)
    return ns['AudiencesKeeper'], ns


class BrowserContext:
    def __init__(self, page, cleanup_error=False):
        self.pages = [page]
        self.cleanup_error = cleanup_error
    def __enter__(self):
        return self
    def __exit__(self, *args):
        if self.cleanup_error:
            raise RuntimeError('browser cleanup timed out')
        return False
    def add_cookies(self, cookies):
        pass


class RefreshRegressionTests(unittest.TestCase):
    def setUp(self):
        cls, self.ns = load_plugin()
        self.plugin = cls()
        self.store = {'state': {'last_cf_success': True, 'last_cf_success_time': '2026-01-01 01:00:00'}}
        self.plugin.get_data = lambda key: copy.deepcopy(self.store.get(key))
        self.plugin.save_data = lambda key, value: self.store.update({key: copy.deepcopy(value)})
        self.plugin._get_site = Mock(return_value={'id': 12, 'url': 'https://example.invalid/', 'cookie': 'session=test'})
        self.plugin._harden_page = Mock()
        self.plugin._goto_robust = Mock(return_value=(True, 'ok'))
        self.plugin._has_cf_challenge = Mock(return_value=False)
        self.plugin._probe_search_page = Mock(return_value=(True, 100, False))
        self.plugin._validate_page = Mock(return_value=(True, 100, '页面验证通过'))
        self.plugin._save_cookies_from_context = Mock(return_value=('session=test', 'test-UA', False))
        self.page = Mock()
        self.page.title.return_value = 'Test site'
        self.context = BrowserContext(self.page)
        self.ns['launch_browser_context'] = lambda **kwargs: self.context

    def test_state_save_failure_preserves_cookie_result_history_and_notification(self):
        self.plugin._enabled = True
        self.plugin._send_notify = Mock()
        def save(key, value):
            if key == 'state':
                raise OSError('private disk diagnostic')
            self.store[key] = copy.deepcopy(value)
        self.plugin.save_data = save
        success, message = self.plugin.run_cf_job(is_manual=True)
        self.assertTrue(success)
        self.assertIn('状态持久化异常', message)
        self.assertNotIn('private disk diagnostic', message)
        self.plugin._save_cookies_from_context.assert_called_once()
        self.assertEqual(len(self.store['history']), 1)
        self.assertEqual(len(self.store['cf_history']), 1)
        self.assertIn('状态持久化异常', self.store['cf_history'][0]['detail'])
        self.plugin._send_notify.assert_called_once()
        self.assertIn('状态持久化异常', self.plugin._send_notify.call_args.kwargs['text'])

    def test_manual_api_preserves_current_result_when_state_read_fails(self):
        for business_success in (True, False):
            with self.subTest(business_success=business_success):
                self.setUp()
                self.plugin._enabled = True
                self.plugin._send_notify = Mock()
                self.plugin._goto_robust.return_value = (business_success, 'offline navigation')
                def get(key):
                    if key == 'state':
                        raise OSError('private storage diagnostic')
                    return copy.deepcopy(self.store.get(key))
                self.plugin.get_data = Mock(side_effect=get)
                response = self.plugin.api_refresh_cookie()
                self.assertEqual(response['success'], business_success)
                self.assertIn('状态持久化异常', response['message'])
                self.assertNotIn('private storage diagnostic', response['message'])
                # Only business-state persistence reads state; manual notification must not.
                state_reads = [call for call in self.plugin.get_data.call_args_list if call.args == ('state',)]
                self.assertEqual(len(state_reads), 1)
                self.assertEqual(self.plugin._save_cookies_from_context.call_count, int(business_success))
                self.plugin._send_notify.assert_called_once()
                self.assertIn(response['message'], self.plugin._send_notify.call_args.kwargs['text'])

    def test_automatic_failure_notification_survives_state_read_failure(self):
        self.plugin._enabled = True
        self.plugin._send_notify = Mock()
        self.plugin._goto_robust.return_value = (False, 'offline navigation')
        def get(key):
            if key == 'state':
                raise OSError('private storage diagnostic')
            return copy.deepcopy(self.store.get(key))
        self.plugin.get_data = get
        success, message = self.plugin.run_cf_job()
        self.assertFalse(success)
        self.assertIn('打开种子列表页失败', message)
        self.assertNotIn('private storage diagnostic', message)
        self.plugin._save_cookies_from_context.assert_not_called()
        self.plugin._send_notify.assert_called_once()
        self.assertIn(message, self.plugin._send_notify.call_args.kwargs['text'])
        warning = self.ns['logger'].warning.call_args.args[0]
        self.assertIn('通知状态读取异常', warning)
        self.assertIn('OSError', warning)

    def test_manual_api_uses_current_failure_when_state_save_fails(self):
        self.plugin._enabled = True
        self.plugin._notify_job_result = Mock()
        self.plugin._goto_robust.return_value = (False, 'offline navigation failure')
        def save(key, value):
            if key == 'state':
                raise OSError('state unavailable')
            self.store[key] = copy.deepcopy(value)
        self.plugin.save_data = save
        response = self.plugin.api_refresh_cookie()
        self.assertFalse(response['success'])
        self.assertIn('打开种子列表页失败', response['message'])
        self.assertIn('状态持久化异常', response['message'])
        self.assertTrue(self.store['state']['last_cf_success'])  # previous stored success is untouched
        self.plugin._save_cookies_from_context.assert_not_called()
        self.assertEqual(len(self.store['cf_history']), 1)
        self.plugin._notify_job_result.assert_called_once()

    def test_history_failure_still_attempts_other_history_without_business_retry(self):
        for failed_key in ('history', 'cf_history'):
            with self.subTest(failed_key=failed_key):
                self.setUp()
                self.plugin._enabled = True
                self.plugin._notify_job_result = Mock()
                attempts = []
                def save(key, value):
                    attempts.append(key)
                    if key == failed_key:
                        raise OSError('private persistence diagnostic')
                    self.store[key] = copy.deepcopy(value)
                self.plugin.save_data = save
                response = self.plugin.api_refresh_cookie()
                self.assertTrue(response['success'])
                self.assertIn('历史持久化异常', response['message'])
                self.assertNotIn('private persistence diagnostic', response['message'])
                self.assertTrue(self.store['state']['last_cf_success'])
                other_key = 'cf_history' if failed_key == 'history' else 'history'
                self.assertEqual(len(self.store.get(other_key, [])), 1)
                self.assertEqual(attempts.count('history'), 1)
                self.assertEqual(attempts.count('cf_history'), 1)
                self.plugin._save_cookies_from_context.assert_called_once()
                self.plugin._notify_job_result.assert_called_once()
                self.assertIn('历史持久化异常', self.plugin._notify_job_result.call_args.kwargs['body'])

    def test_all_record_saves_fail_without_changing_current_result_or_losing_notification(self):
        for business_success in (True, False):
            with self.subTest(business_success=business_success):
                self.setUp()
                self.plugin._enabled = True
                self.plugin._send_notify = Mock()
                self.plugin._goto_robust.return_value = (business_success, 'offline navigation')
                attempts = []
                def save(key, value):
                    attempts.append(key)
                    raise OSError('private storage failure')
                self.plugin.save_data = save
                response = self.plugin.api_refresh_cookie()
                self.assertEqual(response['success'], business_success)
                self.assertIn('状态持久化异常', response['message'])
                self.assertIn('历史持久化异常', response['message'])
                self.assertNotIn('private storage failure', response['message'])
                self.assertEqual(attempts, ['state', 'history', 'cf_history'])
                self.assertEqual(self.plugin._save_cookies_from_context.call_count, int(business_success))
                self.plugin._send_notify.assert_called_once()
                self.assertIn('历史持久化异常', self.plugin._send_notify.call_args.kwargs['text'])

    def test_partial_history_write_is_not_retried_or_duplicated(self):
        self.plugin._enabled = True
        self.plugin._notify_job_result = Mock()
        attempts = []
        def save(key, value):
            attempts.append(key)
            self.store[key] = copy.deepcopy(value)
            if key == 'cf_history':
                raise OSError('raised after write')
        self.plugin.save_data = save
        response = self.plugin.api_refresh_cookie()
        self.assertTrue(response['success'])
        self.assertIn('历史持久化异常', response['message'])
        self.assertEqual(attempts, ['state', 'history', 'cf_history'])
        self.assertEqual(len(self.store['history']), 1)
        self.assertEqual(len(self.store['cf_history']), 1)
        self.plugin._save_cookies_from_context.assert_called_once()

    def test_search_navigation_failure_is_not_success(self):
        self.plugin._probe_search_page.return_value = (False, 0, False)
        success, message = self.plugin.do_refresh_cf()
        self.assertFalse(success)
        self.plugin._save_cookies_from_context.assert_not_called()
        self.assertFalse(self.store['state']['last_cf_success'])

    def test_list_failure_updates_state_without_losing_last_success(self):
        self.plugin._goto_robust.return_value = (False, 'network unavailable')
        success, _ = self.plugin.do_refresh_cf()
        self.assertFalse(success)
        self.assertFalse(self.store['state']['last_cf_success'])
        self.assertEqual(self.store['state']['last_cf_success_time'], '2026-01-01 01:00:00')
        self.assertTrue(self.store['state']['last_cf_failure_time'])
        self.assertEqual(len(self.store['cf_history']), 1)

    def test_missing_site_updates_failure_state(self):
        self.plugin._get_site.return_value = None
        success, _ = self.plugin.do_refresh_cf()
        self.assertFalse(success)
        self.assertFalse(self.store['state']['last_cf_success'])

    def test_browser_exception_updates_failure_state(self):
        self.ns['launch_browser_context'] = Mock(side_effect=RuntimeError('launch failed'))
        success, _ = self.plugin.do_refresh_cf()
        self.assertFalse(success)
        self.assertFalse(self.store['state']['last_cf_success'])

    def test_cleanup_failure_does_not_reverse_verified_business_success(self):
        self.context.cleanup_error = True
        success, message = self.plugin.do_refresh_cf()
        self.assertTrue(success)
        self.assertTrue(self.store['state']['last_cf_success'])
        self.assertEqual(len(self.store['cf_history']), 1)
        self.assertIn('清理', message)

    def test_success_updates_independent_last_success_time(self):
        success, _ = self.plugin.do_refresh_cf()
        self.assertTrue(success)
        self.assertNotEqual(self.store['state']['last_cf_success_time'], '2026-01-01 01:00:00')
        self.assertEqual(len(self.store['cf_history']), 1)

    def test_page_displays_last_success_separately_from_last_run(self):
        page = str(self.plugin.get_page())
        self.assertIn('最近成功时间', page)
        self.assertIn('2026-01-01 01:00:00', page)

    def test_remaining_challenge_prevents_cookie_write(self):
        self.plugin._probe_search_page.return_value = (True, 0, True)
        success, _ = self.plugin.do_refresh_cf()
        self.assertFalse(success)
        self.plugin._save_cookies_from_context.assert_not_called()

    def test_invalid_list_content_prevents_cookie_write(self):
        self.plugin._validate_page.return_value = (False, 0, '登录已失效')
        success, _ = self.plugin.do_refresh_cf()
        self.assertFalse(success)
        self.plugin._save_cookies_from_context.assert_not_called()


class PageValidationTests(unittest.TestCase):
    def setUp(self):
        cls, self.ns = load_plugin()
        self.plugin = cls()
        self.page = Mock()
        self.page.url = 'https://example.invalid/torrents.php?search=1080p'
        self.page.title.return_value = 'Test site'
        self.snapshot = {'url': self.page.url, 'logged_in': True, 'login_form': False,
                         'blocked': False, 'challenge': False, 'table': True,
                         'search_form': True, 'empty': False, 'ids': ['12', '12', '34']}
        self.page.evaluate.side_effect = lambda *a: dict(self.snapshot)

    def validate(self):
        return self.plugin._validate_page(self.page, {'url': 'https://example.invalid/'})

    def test_missing_validator_is_not_a_success(self):
        self.assertTrue(callable(getattr(self.plugin, '_validate_page', None)), '缺少业务页校验')

    def test_unique_results_only(self):
        if not hasattr(self.plugin, '_validate_page'):
            self.skipTest('validator implemented in this slice')
        ok, count, _ = self.validate()
        self.assertTrue(ok)
        self.assertEqual(count, 2)

    def test_block_login_challenge_and_unknown_pages_are_rejected(self):
        if not hasattr(self.plugin, '_validate_page'):
            self.skipTest('validator implemented in this slice')
        for overrides in ({'blocked': True}, {'login_form': True}, {'logged_in': False},
                          {'challenge': True}, {'table': False},
                          {'url': 'https://foreign.invalid/torrents.php'}):
            with self.subTest(overrides=overrides):
                original = dict(self.snapshot)
                self.snapshot.update(overrides)
                self.assertFalse(self.validate()[0])
                self.snapshot = original

    def test_zero_results_need_explicit_empty_state(self):
        if not hasattr(self.plugin, '_validate_page'):
            self.skipTest('validator implemented in this slice')
        self.snapshot.update(ids=[], empty=True)
        self.assertTrue(self.validate()[0])
        self.snapshot.update(empty=False)
        self.assertFalse(self.validate()[0])

    def test_static_turnstile_component_is_not_necessarily_a_block(self):
        self.page.frames = []
        self.page.locator.return_value.count.return_value = 1
        self.assertFalse(self.plugin._has_cf_challenge(self.page))

    def test_http_404_same_domain_is_navigation_failure(self):
        self.page.goto.return_value = Mock(status=404)
        ok, _ = self.plugin._goto_robust(self.page, self.page.url, rounds=1)
        self.assertFalse(ok)

    def test_navigation_timeout_same_domain_is_not_soft_success(self):
        self.page.goto.side_effect = TimeoutError('test navigation timeout')
        ok, _ = self.plugin._goto_robust(self.page, self.page.url, rounds=1)
        self.assertFalse(ok)


class PageSnapshotScriptTests(unittest.TestCase):
    """Execute the production snapshot JS in an offline DOM (optional node/jsdom).

    Set NODE_PATH to an external jsdom installation; no site is contacted.
    The host browser fixtures separately verify rendered DOM behavior.
    """
    @classmethod
    def setUpClass(cls):
        if not shutil.which('node'):
            raise unittest.SkipTest('node is unavailable; run host browser fixtures')
        check = subprocess.run(['node', '-e', "require('jsdom')"], capture_output=True)
        if check.returncode:
            raise unittest.SkipTest('jsdom is unavailable; set NODE_PATH or run host browser fixtures')

    def snapshot(self, html):
        cls, _ = load_plugin()
        page = Mock()
        def evaluate(script):
            runner = r"""
                const {JSDOM} = require('jsdom');
                const fs = require('node:fs');
                const input = JSON.parse(fs.readFileSync(0, 'utf8'));
                const dom = new JSDOM(input.html, {
                    url: 'https://example.invalid/torrents.php?search=1080p',
                    runScripts: 'outside-only'
                });
                Object.defineProperty(dom.window.HTMLElement.prototype, 'innerText', {
                    get() { return this.textContent; }
                });
                console.log(JSON.stringify(dom.window.eval('(' + input.script + ')()')));
            """
            result = subprocess.run(['node', '-e', runner], input=json.dumps({'html': html, 'script': script}),
                                    text=True, capture_output=True, check=True)
            return json.loads(result.stdout)
        page.evaluate.side_effect = evaluate
        return cls._page_snapshot(page)

    def test_torrent_and_recommendation_titles_are_not_block_notices(self):
        facts = self.snapshot('''<div class="site-userbar"><a href="userdetails.php?id=1">user</a></div>
            <table id="torrenttable"><tr><td><a href="details.php?id=12">Access Denied 1996 1080p</a>
            </td></tr></table><a href="details.php?id=34">You Have Been Blocked</a>''')
        self.assertFalse(facts['blocked'])
        self.assertTrue(facts['logged_in'])
        self.assertEqual(facts['ids'], ['12'])

    def test_plain_http_200_block_notice_is_not_hidden_by_results(self):
        for notice in ('搜索人机验证未通过，请返回种子列表页重新进行验证',
                       'Access denied', 'You have been blocked'):
            with self.subTest(notice=notice):
                facts = self.snapshot('''<div class="site-userbar"><a href="userdetails.php?id=1">user</a></div>
                    <table id="torrenttable"><tr><td><a href="details.php?id=12">normal title</a>
                    </td></tr></table><p>''' + notice + '</p>')
                self.assertTrue(facts['blocked'])
                self.assertTrue(facts['table'])


class CookieWriteTests(unittest.TestCase):
    def setUp(self):
        cls, _ = load_plugin()
        self.plugin = cls()
        self.plugin._update_site = Mock(return_value=True)
        self.page = Mock()
        self.page.evaluate.return_value = 'test-UA'
        self.ctx = Mock(pages=[self.page])
        self.site = {'id': 12, 'url': 'https://example.invalid/', 'cookie': 'session=old'}
        self.ctx.cookies.return_value = [{'name': 'session', 'value': 'fresh', 'domain': 'example.invalid'}]

    def test_database_rejection_is_not_reported_as_cookie_updated(self):
        self.plugin._update_site.return_value = False
        with self.assertRaises(RuntimeError):
            self.plugin._save_cookies_from_context(self.ctx, self.site)

    def test_foreign_cookie_is_not_merged_or_counted_as_clearance(self):
        self.ctx.cookies.return_value.append({'name': 'cf_clearance', 'value': 'foreign', 'domain': 'notexample.invalid'})
        cookie, ua, has_cf = self.plugin._save_cookies_from_context(self.ctx, self.site)
        self.assertFalse(has_cf)
        self.assertNotIn('foreign', cookie)
        self.assertEqual(ua, 'test-UA')
        self.assertIn('session=fresh', cookie)

    def test_disabled_manual_endpoint_does_not_return_previous_success(self):
        self.plugin._enabled = False
        self.plugin.get_data = lambda key: {'last_cf_success': True, 'last_cf_message': 'previous success'}
        self.assertFalse(self.plugin.api_refresh_cookie()['success'])


if __name__ == '__main__':
    unittest.main()
