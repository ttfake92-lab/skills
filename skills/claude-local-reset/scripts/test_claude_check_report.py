#!/usr/bin/env python3
"""Recorded results only; no browser, network, account or real-home access."""

from copy import deepcopy
import contextlib
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock

import claude_check_report as report


NOW = datetime(2026, 10, 11, 2, 0, tzinfo=timezone.utc)


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.tags = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.add(attributes["id"])
        if tag == "a":
            self.links.append(attributes)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="claude-report-fixture-", dir="/private/tmp")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.network, self.browser, self.operation = report.demo_inputs(NOW)
        # Convert the sample into a complete successful recording with public
        # test values. It never contacts these addresses.
        self.network["exit_ip"]["attempts"][0]["observation"]["ip"] = "1.1.1.1"
        self.browser["sites"]["ipleak"]["public_ips"] = ["1.1.1.1"]
        self.browser["sites"]["browserleaks_dns"]["resolver_ips"] = ["8.8.8.8"]
        self.network["claude_settings"]["entries"] = []
        self.browser["sites"]["netcoffee"] = {"checked_at_utc": NOW.isoformat(), "dns": {"completed": True, "state": "clear"}, "webrtc": {"completed": True, "state": "clear"}}
        self.browser["sites"]["browserleaks_webrtc"]["public_ips"] = ["1.1.1.1"]
        guard = mock.patch.object(report.subprocess, "run", side_effect=AssertionError("real commands forbidden in report tests"))
        guard.start()
        self.addCleanup(guard.stop)

    def evaluate(self, **kwargs):
        return report.evaluate(self.network, self.browser, self.operation, expected_country="JP", now=NOW, **kwargs)

    @staticmethod
    def by_id(result):
        return {item["id"]: item for item in result["checks"]}

    def test_confirmed_complete_results_pass_only_their_measured_scope(self):
        result = self.evaluate()
        checks = self.by_id(result)
        for key in ("ipleak", "browserleaks_dns", "netcoffee_dns", "netcoffee_webrtc", "system_proxy", "terminal_routes"):
            self.assertEqual(checks[key]["state"], "pass")
        self.assertEqual(checks["ipv6"]["state"], "not_tested")
        self.assertEqual(checks["stability"]["state"], "not_tested")
        self.assertEqual(result["heading"], "本次关键质检已通过")
        self.assertEqual(sum(result["counts"].values()), len(result["checks"]))
        self.assertEqual(result["next_steps"][0]["title"], "自行登录并验证")

    def test_cn_and_hk_are_failures_even_with_caller_passed_flags(self):
        for site in ("ipleak", "browserleaks_dns"):
            for code in ("CN", "HK"):
                with self.subTest(site=site, code=code):
                    browser = deepcopy(self.browser)
                    browser["sites"][site].update(country_codes=["JP", code], passed=True, status="pass")
                    result = report.evaluate(self.network, browser, self.operation, expected_country="JP", now=NOW)
                    self.assertEqual(self.by_id(result)[site]["state"], "fail")
                    self.assertEqual(result["tone"], "fail")

    def test_country_must_match_known_expected_route_and_cannot_be_guessed(self):
        self.browser["sites"]["ipleak"]["country_codes"] = ["US"]
        self.assertEqual(self.by_id(self.evaluate())["ipleak"]["state"], "fail")
        for value in ([], ["ZZ"], ["China"], ["JP", "unrecognized"]):
            self.browser["sites"]["ipleak"]["country_codes"] = value
            self.assertEqual(self.by_id(self.evaluate())["ipleak"]["state"], "not_tested")

    def test_netcoffee_dns_and_udp_are_independent_and_missing_is_not_pass(self):
        site = self.browser["sites"]["netcoffee"]
        site["dns"] = {"completed": True, "state": "leak"}
        site["webrtc"] = {"completed": True, "state": "clear"}
        result = self.by_id(self.evaluate())
        self.assertEqual(result["netcoffee_dns"]["state"], "fail")
        self.assertEqual(result["netcoffee_webrtc"]["state"], "pass")
        for state in ("unknown", "disabled", None):
            site["webrtc"] = {"completed": True, "state": state}
            self.assertEqual(self.by_id(self.evaluate())["netcoffee_webrtc"]["state"], "not_tested")
        site["webrtc"] = {"completed": "true", "state": "clear"}
        self.assertEqual(self.by_id(self.evaluate())["netcoffee_webrtc"]["state"], "not_tested")

    def test_loading_empty_and_private_ip_results_cannot_pass(self):
        site = self.browser["sites"]["ipleak"]
        for values in ((False, ["1.1.1.1"]), (True, []), (True, ["192.168.1.10"]), (True, ["203.0.113.10"]), (True, ["not-an-ip"])):
            with self.subTest(values=values):
                site["completed"], site["public_ips"] = values
                self.assertEqual(self.by_id(self.evaluate())["ipleak"]["state"], "not_tested")

    def test_remote_or_unconfirmed_browser_is_not_user_evidence(self):
        for context in ({"type": "remote-browser", "profile_confirmed": True}, {"type": "local-browser", "profile_confirmed": False}, {"type": "local-browser", "profile_confirmed": "true"}):
            self.browser["context"] = context
            checks = self.by_id(self.evaluate())
            self.assertTrue(all(checks[key]["state"] == "not_tested" for key in ("ipleak", "browserleaks_dns", "netcoffee_dns", "netcoffee_webrtc")))

    def test_expired_missing_and_future_timestamps_are_not_fresh_checks(self):
        site = self.browser["sites"]["ipleak"]
        for value in ((NOW - timedelta(hours=2)).isoformat(), (NOW + timedelta(hours=2)).isoformat(), "2026-10-11T02:00:00", None, "invalid"):
            site["checked_at_utc"] = value
            self.assertEqual(self.by_id(self.evaluate())["ipleak"]["state"], "not_tested")
        self.network["checked_at_utc"] = (NOW - timedelta(hours=2)).isoformat()
        self.assertEqual(self.by_id(self.evaluate())["system_proxy"]["state"], "not_tested")

    def test_missing_inputs_still_produce_actionable_receipt(self):
        result = report.evaluate(now=NOW)
        self.assertEqual(result["counts"]["pass"], 0)
        self.assertEqual(result["tone"], "review")
        html = report.render_html(result)
        self.assertIn("接下来做什么", html)
        for site in ("ipleak", "browserleaks_dns", "netcoffee"):
            self.assertIn(report.SITES[site][1], html)

    def test_proxy_mode_and_incomplete_configuration_do_not_create_false_pass(self):
        self.network["system_proxy"]["flags"]["HTTPEnable"] = [1]
        self.assertEqual(self.by_id(self.evaluate())["system_proxy"]["state"], "review")
        self.network["expected_mode"] = "system-proxy"
        self.assertEqual(self.by_id(self.evaluate())["system_proxy"]["state"], "pass")
        self.network["claude_settings"]["custom_config_dir_present"] = True
        self.assertEqual(self.by_id(self.evaluate())["terminal_routes"]["state"], "review")
        self.network["npm_proxy"]["status"] = "未检测"
        self.assertEqual(self.by_id(self.evaluate())["package_proxies"]["state"], "not_tested")

    def test_conflicting_public_candidates_require_review_even_if_clear(self):
        self.browser["sites"]["browserleaks_webrtc"]["public_ips"] = ["8.8.8.8"]
        self.assertEqual(self.by_id(self.evaluate())["browserleaks_webrtc"]["state"], "review")

    def test_partial_reset_cannot_report_reset_completed(self):
        self.operation.update(action="reset", status="partial", backup_path="/Users/example/ClaudeLocalResetBackups/fixture")
        result = self.evaluate()
        self.assertEqual(self.by_id(result)["operation"]["state"], "fail")
        self.assertEqual(result["operation_status"], "partial")
        self.assertIn("~/ClaudeLocalResetBackups/fixture", report.render_html(result))
        self.operation["status"] = "not_run"
        self.assertEqual(self.by_id(self.evaluate())["operation"]["state"], "not_tested")

    def test_partial_check_overrides_green_individual_results(self):
        self.operation["status"] = "failed"
        result = self.evaluate()
        self.assertEqual(self.by_id(result)["operation"]["state"], "fail")
        self.assertEqual(result["tone"], "fail")

    def test_timezone_is_only_compared_when_user_has_named_a_target(self):
        self.assertNotIn("timezone", self.by_id(self.evaluate()))
        self.assertEqual(self.by_id(self.evaluate(expected_timezone="Asia/Taipei"))["timezone"]["state"], "pass")
        self.assertEqual(self.by_id(self.evaluate(expected_timezone="America/Los_Angeles"))["timezone"]["state"], "fail")

    def test_report_redacts_raw_secrets_full_ip_and_untrusted_page_links(self):
        secret = "fixture-token-MUST-NOT-APPEAR"
        self.network["raw_settings"] = {"ANTHROPIC_API_KEY": secret}
        self.network["environment"]["entries"].append({"name": "ANTHROPIC_API_KEY", "kind": "credential_or_sensitive", "value": secret})
        self.browser["context"]["profile"] = secret
        self.browser["sites"]["ipleak"].update(url="javascript:alert('bad')", html=secret, token=secret)
        result = self.evaluate()
        html = report.render_html(result)
        for value in (secret, "1.1.1.1", "8.8.8.8", "javascript:"):
            self.assertNotIn(value, html)
            self.assertNotIn(value, json.dumps(result))
        self.assertIn("1.1.1.*", html)

    def test_dynamic_text_is_escaped_and_links_are_fixed_safe_new_tabs(self):
        self.operation.update(action="reset", status="completed", backup_path='/Users/example/ClaudeLocalResetBackups/<script>alert(1)</script>')
        html = report.render_html(self.evaluate())
        self.assertIn("&lt;script&gt;", html)
        parser = LinkCollector()
        parser.feed(html)
        self.assertNotIn("script", parser.tags)
        self.assertNotIn("iframe", parser.tags)
        self.assertNotIn("img", parser.tags)
        external = [link for link in parser.links if link["href"].startswith("https://")]
        local = [link for link in parser.links if not link["href"].startswith("https://")]
        self.assertTrue(external)
        self.assertTrue(all(link.get("target") == "_blank" and "noopener" in link.get("rel", "") for link in external))
        self.assertEqual([link["href"] for link in local], ["guide.html"])
        self.assertTrue(all("target" not in link for link in local))
        self.assertIn("Content-Security-Policy", html)

    def test_bundle_is_private_and_existing_report_cannot_be_overwritten(self):
        output = self.root / "delivery"
        path = report.write_report(output, self.evaluate())
        self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(path.with_suffix(".json").stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE((output / "guide.html").stat().st_mode), 0o600)
        originals = {file.name: file.read_bytes() for file in output.iterdir()}
        self.assertEqual(set(originals), {"report.html", "guide.html", "report.json"})
        with self.assertRaises(FileExistsError):
            report.write_report(output, report.evaluate(now=NOW))
        self.assertEqual({file.name: file.read_bytes() for file in output.iterdir()}, originals)
        alias = self.root / "alias"
        alias.symlink_to(output, target_is_directory=True)
        with self.assertRaises(ValueError):
            report.write_report(alias / "outside", self.evaluate())

    def test_opener_uses_only_local_file_and_preserves_bundle_on_failure(self):
        path = report.write_report(self.root / "delivery", self.evaluate())
        runner = mock.Mock(return_value=type("Result", (), {"returncode": 0})())
        self.assertEqual(report.open_report(path, runner=runner, platform="darwin"), "opened")
        self.assertEqual(runner.call_args.args[0], ["/usr/bin/open", str(path)])
        runner.side_effect = OSError("fixture-secret")
        self.assertEqual(report.open_report(path, runner=runner, platform="darwin"), "failed")
        self.assertTrue(path.is_file())
        self.assertTrue(path.with_name("guide.html").is_file())
        self.assertEqual(report.open_report(path, runner=runner, platform="linux"), "unsupported_platform")
        runner = mock.Mock(return_value=type("Result", (), {"returncode": 0})())
        self.assertEqual(report.open_report(path, runner=runner, platform="win32"), "opened")
        self.assertEqual(runner.call_args.args[0][:4], ["cmd", "/c", "start", ""])
        self.operation["backup_path"] = "C:\\Users\\example\\ClaudeLocalResetBackups\\fixture"
        rendered = report.render_html(self.evaluate())
        self.assertIn("~/ClaudeLocalResetBackups/fixture", rendered)
        self.assertNotIn("Users", rendered)

    def test_guide_entry_precedes_summary_and_two_pages_link_back_offline(self):
        path = report.write_report(self.root / "delivery", self.evaluate())
        html = path.read_text()
        self.assertLess(html.index('class="guide-entry"'), html.index('<section class="hero"'))
        parser = LinkCollector()
        parser.feed(path.with_name("guide.html").read_text())
        self.assertTrue({"first-time", "previously-banned", "manual", "quality-check", "daily"}.issubset(parser.ids))
        local = [link["href"] for link in parser.links if not link["href"].startswith("https://")]
        self.assertIn("report.html", local)
        for href in local:
            if href.startswith("#"):
                self.assertIn(href[1:], parser.ids)
            else:
                self.assertEqual(href, "report.html")
                self.assertTrue((path.parent / href).is_file())

    def test_guide_has_literal_invocation_and_never_loads_or_echoes_sensitive_inputs(self):
        result = self.evaluate()
        result.update(browser_context="fixture-secret", backup_display="fixture-secret", generated_at_utc="<script>alert(1)</script>")
        html = report.render_guide(result)
        self.assertIn("$claude-local-reset", html)
        self.assertNotIn("$$claude-local-reset", html)
        self.assertNotIn("$demo_banner", html)
        self.assertNotIn("$generated_at", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("fixture-secret", html)
        parser = LinkCollector()
        parser.feed(html)
        self.assertTrue(set(parser.tags).isdisjoint({"script", "iframe", "img", "input", "form", "button", "link"}))
        external = [link for link in parser.links if link["href"].startswith("https://")]
        self.assertTrue(all(link.get("target") == "_blank" and "noopener" in link.get("rel", "") for link in external))
        self.assertIn("Content-Security-Policy", html)

    def test_demo_label_is_carried_into_guide_without_altering_real_receipt(self):
        simulated = report.evaluate(*report.demo_inputs(NOW), now=NOW, demo=True)
        html = report.render_guide(simulated)
        self.assertIn("演示 · 模拟数据", html)
        self.assertIn("没有检查或改动这台电脑", html)
        self.assertNotIn("演示 · 模拟数据", report.render_guide(self.evaluate()))

    def test_guide_only_delivery_never_invokes_audit_or_opener_and_leaves_checks_missing(self):
        output = io.StringIO()
        with mock.patch.object(report, "open_report", side_effect=AssertionError("opener not requested")), contextlib.redirect_stdout(output):
            self.assertEqual(report.main(["--output-dir", str(self.root / "guide-only")]), 0)
        files = json.loads(output.getvalue())
        self.assertEqual(files["open_status"], "not_requested")
        self.assertEqual(Path(files["guide"]).parent, Path(files["html"]).parent)
        self.assertTrue(Path(files["guide"]).is_file())
        recorded = json.loads(Path(files["json"]).read_text())
        self.assertEqual(recorded["counts"]["pass"], 0)
        self.assertEqual(recorded["operation_status"], "not_run")

    def test_demo_cli_never_reads_real_inputs_and_uses_mocked_opener(self):
        output = io.StringIO()
        with mock.patch.object(report, "read_input", side_effect=AssertionError("no inputs in demo")), mock.patch.object(report, "open_report", return_value="opened") as opener, contextlib.redirect_stdout(output):
            self.assertEqual(report.main(["--demo", "--output-dir", str(self.root / "demo"), "--open"]), 0)
        data = json.loads(output.getvalue())
        self.assertTrue(data["demo"])
        self.assertEqual(data["open_status"], "opened")
        opener.assert_called_once()
        self.assertIn("演示 · 模拟数据", Path(data["html"]).read_text())
        self.assertIn("演示 · 模拟数据", Path(data["guide"]).read_text())

    def test_invalid_input_fails_without_secret_output_or_partial_delivery(self):
        source = self.root / "invalid.json"
        source.write_text('{"token":"fixture-secret",')
        output, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            self.assertEqual(report.main(["--network-json", str(source), "--output-dir", str(self.root / "delivery")]), 2)
        self.assertNotIn("fixture-secret", output.getvalue() + error.getvalue())
        self.assertFalse((self.root / "delivery").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
