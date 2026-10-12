#!/usr/bin/env python3
"""Simulated files and commands only: never inspect the user's live network."""

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import claude_network_check as check


class FakeCommands:
    def __init__(self):
        self.calls = []
        self.responses = {
            "scutil": check.CommandResult(0, "<dictionary> {\n HTTPEnable : 0\n HTTPSEnable : 0\n SOCKSEnable : 0\n ProxyAutoConfigEnable : 0\n}"),
            "npm:proxy": check.CommandResult(0, "null\n"),
            "npm:https-proxy": check.CommandResult(0, "null\n"),
            "git": check.CommandResult(1),
            "readlink": check.CommandResult(0, "/var/db/timezone/zoneinfo/Asia/Taipei\n"),
            "node": check.CommandResult(0, "Asia/Taipei\n"),
            "curl:4": check.CommandResult(0, json.dumps({"ip": "8.8.8.8", "country": "US", "city": "Fixture City", "org": "AS15169 Example"})),
            "curl:6": check.CommandResult(0, json.dumps({"ip": "2606:4700:4700::1111", "geo": {"country_code": "US"}, "as": {"asn": "AS13335", "name": "Fixture Provider"}})),
        }

    @staticmethod
    def find(name):
        if name not in {"scutil", "npm", "git", "curl", "readlink", "node"}:
            raise AssertionError("unexpected executable")
        return "/simulated-bin/" + name

    def run(self, argv, *, cwd, environment, timeout):
        self.calls.append((list(argv), Path(cwd), dict(environment), timeout))
        name = Path(argv[0]).name
        if name == "npm":
            key = "npm:" + argv[3]
            assert argv[1:3] == ["config", "get"]
            assert "--offline" in argv and "--logs-max=0" in argv
        elif name == "curl":
            key = "curl:" + ("4" if "-4" in argv else "6")
            assert argv[1] == "-q"
            assert argv[-1] == "https://ipinfo.io/json"
            assert "-k" not in argv and "--insecure" not in argv
        else:
            key = name
        return self.responses[key]


class NetworkCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="claude-network-fixture-", dir="/private/tmp")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "simulated-home"
        self.home.mkdir()
        self.system_dir = Path(self.temp.name) / "simulated-etc"
        self.system_dir.mkdir()
        self.system_files = []
        for name in ("zshrc", "zprofile", "profile", "bashrc"):
            path = self.system_dir / ("fixture-" + name)
            path.write_text("# fixture system shell file\n", encoding="utf-8")
            self.system_files.append(str(path))
        self.system_hosts = self.system_dir / "hosts"
        self.system_hosts.write_text("127.0.0.1 localhost\n::1 localhost\n", encoding="utf-8")
        self.fake = FakeCommands()
        self.environment = {}
        env_patch = mock.patch.dict(os.environ, {}, clear=True)
        env_patch.start()
        self.addCleanup(env_patch.stop)
        # A regression cannot fall back to an actual scutil/npm/git/curl process.
        process_guard = mock.patch.object(check.subprocess, "run", side_effect=AssertionError("real commands forbidden in tests"))
        process_guard.start()
        self.addCleanup(process_guard.stop)

    def put(self, relative, content):
        path = self.home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def collect(self, **kwargs):
        return check.collect_report(self.home, self.environment, runner=self.fake.run, finder=self.fake.find, system_files=self.system_files, hosts_path=str(self.system_hosts), **kwargs)

    def tree(self):
        return {
            str(path.relative_to(self.home)): os.readlink(path) if path.is_symlink() else path.read_bytes() if path.is_file() else None
            for path in self.home.rglob("*")
        }

    def test_default_read_only_and_no_online_queries(self):
        self.put(".zshrc", "export HTTPS_PROXY=http://127.0.0.1:7890\n")
        self.put(".claude/settings.json", '{"env":{"ANTHROPIC_BASE_URL":"https://gateway.example.invalid/v1"},"hooks":{"preserve":"yes"}}')
        before = self.tree()
        report = self.collect()
        self.assertEqual(before, self.tree())
        self.assertEqual(report["mode"], "read-only")
        self.assertEqual(report["exit_ip"]["status"], "未检测")
        self.assertEqual({Path(call[0][0]).name for call in self.fake.calls}, {"scutil", "npm", "git", "readlink", "node"})
        self.assertTrue(all(call[1] == self.home for call in self.fake.calls))
        self.assertTrue(all(item["status"] == "未检测" for item in report["browser_tests"].values()))

    def test_credentials_hidden_across_every_configuration_source(self):
        secret = "fixture-password-MUST-NOT-APPEAR"
        token = "fixture-token-MUST-NOT-APPEAR"
        relay = f"https://user:{secret}@relay.example.invalid:8443/private/{token}?token={token}#secret"
        self.environment.update(ANTHROPIC_API_KEY=token, ANTHROPIC_BASE_URL=relay, HTTPS_PROXY=relay, CLAUDE_CODE_OAUTH_TOKEN=token, NO_PROXY=secret)
        self.put(".zshrc", f'export ANTHROPIC_AUTH_TOKEN="{token}"\nexport HTTPS_PROXY="{relay}"\n')
        self.put(".claude/settings.json", json.dumps({"env": {"ANTHROPIC_BASE_URL": relay, "ANTHROPIC_API_KEY": token}, "mcpServers": {"hidden": {"env": {"TOKEN": token}}}}))
        self.fake.responses["npm:proxy"] = check.CommandResult(0, relay)
        self.fake.responses["git"] = check.CommandResult(0, f"http.{relay}.proxy\n{relay}\0https.proxy\n{relay}\0")
        text = json.dumps(self.collect(), ensure_ascii=False)
        # The relay URL path must stay hidden; fixture file paths may legitimately
        # live under /private/tmp, so the marker is tied to the relay host instead.
        for value in (secret, token, "relay.example.invalid:8443/private", "token=", "user:"):
            self.assertNotIn(value, text)
        self.assertIn("https://relay.example.invalid:8443", text)
        self.assertIn("custom_host", text)
        self.assertNotIn("mcpServers", text)

    def test_shell_commands_are_candidates_and_never_executed(self):
        marker = self.home / "must-not-exist"
        self.put(".zshenv", f'export ANTHROPIC_BASE_URL="$(touch {marker})"\n# ANTHROPIC_API_KEY=comment-secret\nexport HTTPS_PROXY="unterminated\n')
        report = self.collect()
        self.assertFalse(marker.exists())
        entries = next(item for item in report["shell_files"] if item["file"] == "~/.zshenv")["entries"]
        self.assertEqual([item["name"] for item in entries], ["ANTHROPIC_BASE_URL", "HTTPS_PROXY"])
        self.assertTrue(all(item["status"] == "待核实" for item in entries))
        text = json.dumps(entries)
        self.assertNotIn("touch", text)
        self.assertNotIn("comment-secret", text)

    def test_invalid_or_duplicate_settings_are_not_reported_as_clean(self):
        for value in ('{"secret":"fixture-secret",', '{"env":{},"env":{"ANTHROPIC_API_KEY":"fixture-secret"}}', '{"env":[]}'):
            with self.subTest(value=value):
                self.put(".claude/settings.json", value)
                item = self.collect()["claude_settings"]
                self.assertEqual(item["status"], "未检测")
                self.assertNotIn("fixture-secret", json.dumps(item))

    def test_symlinked_settings_directory_and_shell_file_are_skipped(self):
        outside = Path(self.temp.name) / "outside-fixture"
        outside.mkdir()
        (outside / "settings.json").write_text('{"env":{"ANTHROPIC_BASE_URL":"https://outside.example.invalid"}}')
        (self.home / ".claude").symlink_to(outside, target_is_directory=True)
        (self.home / ".zshrc").symlink_to(outside / "settings.json")
        report = self.collect()
        self.assertEqual(report["claude_settings"]["read_state"], "symlink_skipped")
        self.assertEqual(report["shell_files"][0]["read_state"], "symlink_skipped")
        self.assertNotIn("outside.example.invalid", json.dumps(report))

    def test_oversized_and_nonregular_files_are_not_read(self):
        self.put(".zshrc", "a" * (check.MAX_BYTES + 1))
        (self.home / ".profile").mkdir()
        report = self.collect()
        self.assertEqual(report["shell_files"][0]["read_state"], "too_large")
        profile = next(item for item in report["shell_files"] if item["file"] == "~/.profile")
        self.assertEqual(profile["read_state"], "not_regular")

    def test_system_shell_files_and_hosts_are_wired_without_extra_commands(self):
        report = self.collect()
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(len(report["shell_files"]), 8)
        self.assertEqual([item["file"] for item in report["shell_files"]], ["~/" + name for name in check.SHELL_FILES])
        self.assertEqual(len(report["system_shell_files"]), 4)
        self.assertTrue(all(item["status"] == "已观察" for item in report["system_shell_files"]))
        self.assertEqual(report["hosts_file"]["status"], "已观察")
        self.assertEqual(report["hosts_file"]["matches"], [])
        self.assertEqual({Path(call[0][0]).name for call in self.fake.calls}, {"scutil", "npm", "git", "readlink", "node"})

    def test_system_shell_candidates_carry_system_origin(self):
        Path(self.system_files[0]).write_text("export HTTPS_PROXY=http://127.0.0.1:7890\n", encoding="utf-8")
        report = self.collect()
        entry = report["system_shell_files"][0]["entries"][0]
        self.assertEqual(entry["name"], "HTTPS_PROXY")
        self.assertEqual(entry["origin"], "系统启动文件候选；不代表当前已生效")

    def test_hosts_mappings_are_flagged_without_exposing_addresses(self):
        self.system_hosts.write_text("127.0.0.1 localhost\n203.0.113.5 api.anthropic.com\nclaude.ai mirror.example.invalid\n", encoding="utf-8")
        item = check.scan_hosts_file(str(self.system_hosts))
        self.assertEqual(item["status"], "待核实")
        self.assertEqual([match["domain"] for match in item["matches"]], ["api.anthropic.com", "claude.ai"])
        self.assertNotIn("203.0.113.5", json.dumps(item))

    def test_curl_wget_proxy_candidates_are_redacted(self):
        self.put(".curlrc", 'proxy = "https://user:fixture-pass@relay.example.invalid:8443"\n')
        report = self.collect()
        curl = next(item for item in report["curl_wget"] if item["file"] == "~/.curlrc")
        wget = next(item for item in report["curl_wget"] if item["file"] == "~/.wgetrc")
        self.assertEqual(curl["status"], "待核实")
        self.assertEqual(curl["entries"][0]["kind"], "proxy")
        self.assertEqual(curl["entries"][0]["target"], "https://relay.example.invalid:8443")
        self.assertEqual(wget["status"], "已观察")
        self.assertNotIn("fixture-pass", json.dumps(report))

    def test_settings_local_is_scanned_separately_and_failures_do_not_look_clean(self):
        self.put(".claude/settings.local.json", '{"env":{"ANTHROPIC_BASE_URL":"https://relay.example.invalid/v1"}}')
        report = self.collect()
        self.assertEqual(report["claude_settings_local"]["status"], "已观察")
        self.assertEqual(report["claude_settings_local"]["entries"][0]["route"], "custom_host")
        self.assertEqual(report["claude_settings"]["status"], "已观察")
        self.put(".claude/settings.local.json", '{"env":')
        self.assertEqual(self.collect()["claude_settings_local"]["status"], "未检测")

    def test_system_proxy_interpretation_depends_on_requested_mode(self):
        self.fake.responses["scutil"] = check.CommandResult(0, "HTTPEnable : 1\nProxyAutoConfigEnable : 1\nProxyAutoDiscoveryEnable : 1\n<scoped> { HTTPEnable : 0 }")
        tun = self.collect(expected_mode="tun")["system_proxy"]
        system = self.collect(expected_mode="system-proxy")["system_proxy"]
        self.assertEqual(tun["status"], "待核实")
        self.assertEqual(system["status"], "已观察")
        self.assertEqual(tun["flags"]["HTTPEnable"], [0, 1])
        self.assertIsNone(tun["flags"]["HTTPSEnable"])
        self.assertIn("ProxyAutoConfigEnable", tun["enabled"])

    def test_missing_flags_and_disabled_expected_system_proxy_remain_unverified(self):
        self.assertEqual(self.collect(expected_mode="system-proxy")["system_proxy"]["status"], "待核实")
        self.fake.responses["scutil"] = check.CommandResult(0, "<dictionary> {}")
        self.assertEqual(self.collect()["system_proxy"]["status"], "未检测")

    def test_command_failures_and_missing_tools_do_not_look_clean(self):
        self.fake.responses["scutil"] = check.CommandResult(3, "error containing fixture-secret")
        self.fake.responses["npm:proxy"] = check.CommandResult(None, error="timeout")
        self.fake.responses["git"] = check.CommandResult(2, "fixture-secret")
        report = self.collect()
        for key in ("system_proxy", "npm_proxy", "git_proxy"):
            self.assertEqual(report[key]["status"], "未检测")
        self.assertNotIn("fixture-secret", json.dumps(report))
        missing = check.collect_report(self.home, {}, runner=self.fake.run, finder=lambda name: None, online=True, system_files=self.system_files, hosts_path=str(self.system_hosts))
        self.assertEqual(missing["exit_ip"]["status"], "未检测")
        self.assertEqual(missing["system_proxy"]["reason"], "command_missing")

    def test_npm_null_and_empty_git_mean_no_matching_values(self):
        report = self.collect()
        self.assertTrue(all(item["configured"] is False for item in report["npm_proxy"]["entries"]))
        self.assertEqual(report["git_proxy"], {"status": "已观察", "entries": []})
        self.fake.responses["git"] = check.CommandResult(0, "malformed-response-secret")
        self.assertEqual(self.collect()["git_proxy"]["status"], "未检测")

    def test_custom_config_dir_and_official_provider_settings_require_context(self):
        self.environment.update(CLAUDE_CONFIG_DIR="/fixture/custom", CLAUDE_CODE_USE_BEDROCK="1", ANTHROPIC_BASE_URL="https://api.anthropic.com")
        report = self.collect()
        self.assertTrue(report["claude_settings"]["custom_config_dir_present"])
        self.assertNotIn("/fixture/custom", json.dumps(report))
        entries = {item["name"]: item for item in report["environment"]["entries"]}
        self.assertEqual(entries["ANTHROPIC_BASE_URL"]["route"], "official_api_host")
        self.assertEqual(entries["CLAUDE_CODE_USE_BEDROCK"]["status"], "已观察")

    def test_timezone_records_real_values_without_loading_node_options(self):
        self.environment.update(TZ="America/Los_Angeles", NODE_OPTIONS="--require /fixture/must-not-run")
        self.fake.responses["node"] = check.CommandResult(0, "America/Los_Angeles\n")
        report = self.collect()
        self.assertEqual(report["timezone"]["system"]["value"], "Asia/Taipei")
        self.assertEqual(report["timezone"]["tz_override"], "America/Los_Angeles")
        node_call = next(call for call in self.fake.calls if Path(call[0][0]).name == "node")
        self.assertNotIn("NODE_OPTIONS", node_call[2])
        self.assertEqual(node_call[2]["TZ"], "America/Los_Angeles")
        self.assertTrue(all("NODE_OPTIONS" not in call[2] for call in self.fake.calls if Path(call[0][0]).name == "npm"))
        self.assertEqual(self.environment["NODE_OPTIONS"], "--require /fixture/must-not-run")

    def test_privacy_preferences_are_observations_not_automatic_repairs(self):
        self.environment.update(DISABLE_TELEMETRY="1", DISABLE_ERROR_REPORTING="0", CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="unparsed-fixture-secret")
        entries = {item["name"]: item for item in self.collect()["environment"]["entries"]}
        self.assertEqual(entries["DISABLE_TELEMETRY"]["value"], "1")
        self.assertEqual(entries["DISABLE_ERROR_REPORTING"]["value"], "0")
        self.assertEqual(entries["DISABLE_ERROR_REPORTING"]["status"], "已观察")
        self.assertNotIn("unparsed-fixture-secret", json.dumps(entries))

    def test_online_queries_handle_legacy_and_current_ipinfo_formats(self):
        self.environment["HTTPS_PROXY"] = "http://127.0.0.1:7890"
        report = self.collect(online=True)
        ipv4, ipv6 = report["exit_ip"]["attempts"]
        self.assertEqual(ipv4["observation"]["reported_ip_family"], 4)
        self.assertEqual(ipv4["observation"]["country"], "US")
        self.assertEqual(ipv6["observation"]["reported_ip_family"], 6)
        self.assertIsNone(ipv6["observation"]["city"])
        self.assertEqual(ipv6["observation"]["asn"], "AS13335")
        curl_calls = [call for call in self.fake.calls if Path(call[0][0]).name == "curl"]
        self.assertEqual(len(curl_calls), 2)
        self.assertTrue(all(call[2]["HTTPS_PROXY"] == self.environment["HTTPS_PROXY"] for call in curl_calls))
        self.assertTrue(all(item["status"] == "未检测" for item in report["browser_tests"].values()))

    def test_ipv6_query_failure_is_not_evidence_of_ipv6_being_disabled(self):
        self.fake.responses["curl:6"] = check.CommandResult(7, "fixture-proxy-password")
        report = self.collect(online=True)
        item = report["exit_ip"]["attempts"][1]
        self.assertEqual(item["status"], "未检测")
        self.assertNotIn("observation", item)
        self.assertNotIn("fixture-proxy-password", json.dumps(report))
        self.assertIn("不证明", report["exit_ip"]["limitations"])

    def test_requested_connection_family_does_not_override_reported_ip(self):
        self.fake.responses["curl:6"] = self.fake.responses["curl:4"]
        item = self.collect(online=True)["exit_ip"]["attempts"][1]
        self.assertEqual(item["requested_connection_family"], 6)
        self.assertEqual(item["observation"]["reported_ip_family"], 4)

    def test_invalid_ip_responses_do_not_leak_raw_bodies(self):
        for value in ('not-json-fixture-secret', '{"ip":"invalid","token":"fixture-secret"}', '{"ip":"192.168.1.1"}', '{"ip":"127.0.0.1"}', '["fixture-secret"]'):
            with self.subTest(value=value):
                self.fake.responses["curl:4"] = check.CommandResult(0, value)
                self.fake.responses["curl:6"] = check.CommandResult(7)
                report = self.collect(online=True)
                self.assertEqual(report["exit_ip"]["status"], "未检测")
                self.assertNotIn("fixture-secret", json.dumps(report))

    def test_subprocess_runner_suppresses_stderr_and_exception_details(self):
        with mock.patch.object(check.subprocess, "run", return_value=subprocess.CompletedProcess(["fixture"], 1, stdout="", stderr="fixture-secret")) as process:
            result = check.run_command(["fixture"], cwd=self.home, environment={}, timeout=1)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(process.call_args.kwargs["stderr"], subprocess.DEVNULL)
            self.assertNotIn("shell", process.call_args.kwargs)
        for error in (OSError("fixture-secret"), subprocess.TimeoutExpired("fixture-secret", 1, output="fixture-secret")):
            with mock.patch.object(check.subprocess, "run", side_effect=error):
                self.assertNotIn("fixture-secret", repr(check.run_command(["fixture"], cwd=self.home, environment={}, timeout=1)))

    def test_cli_is_exercised_with_fake_home_and_fake_commands_only(self):
        actual_collect = check.collect_report
        def simulated(home, environment, **kwargs):
            return actual_collect(home, environment, runner=self.fake.run, finder=self.fake.find, **kwargs)
        output = io.StringIO()
        with mock.patch.object(check.Path, "home", return_value=self.home), mock.patch.object(check.sys, "platform", "darwin"), mock.patch.object(check, "collect_report", side_effect=simulated), contextlib.redirect_stdout(output):
            self.assertEqual(check.main([]), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["exit_ip"]["reason"], "online_not_requested")
        self.assertTrue(all(Path(call[0][0]).name != "curl" for call in self.fake.calls))

    def test_windows_reads_wininet_powershell_and_hosts_without_scutil_or_secrets(self):
        self.put(
            "Documents/PowerShell/Microsoft.PowerShell_profile.ps1",
            '$env:HTTPS_PROXY = "http://user:fixture-secret@relay.example:8443"\n',
        )
        hosts = self.system_dir / "windows-hosts"
        hosts.write_text("203.0.113.8 api.anthropic.com\n", encoding="utf-8")
        calls = []

        def finder(name):
            if name not in {"tzutil", "npm", "git", "node"}:
                raise AssertionError(name)
            return "/simulated-bin/" + name

        def runner(argv, **kwargs):
            name = Path(argv[0]).name
            calls.append(name)
            if name == "tzutil":
                return check.CommandResult(0, "Taipei Standard Time\n")
            if name == "npm":
                return check.CommandResult(0, "null\n")
            if name == "git":
                return check.CommandResult(1)
            if name == "node":
                return check.CommandResult(0, "Asia/Taipei\n")
            raise AssertionError(name)

        report = check.collect_report(
            self.home, {}, runner=runner, finder=finder, platform="win32",
            windows_proxy={
                "ProxyEnable": 0, "AutoConfigURL": False, "AutoDetect": 0,
                "ProxyServer": "http://user:fixture-secret@127.0.0.1:1",
            },
            hosts_path=str(hosts), system_files=(), expected_mode="tun",
        )
        self.assertNotIn("scutil", calls)
        self.assertNotIn("fixture-secret", json.dumps(report))
        self.assertNotIn("203.0.113.8", json.dumps(report))
        self.assertEqual(report["system_proxy"]["flags"]["HTTPEnable"], [0])
        self.assertEqual(report["system_proxy"]["flags"]["ProxyAutoDiscoveryEnable"], [0])
        self.assertEqual(report["timezone"]["system"]["windows_id"], "Taipei Standard Time")
        self.assertNotIn("value", report["timezone"]["system"])
        self.assertEqual(report["hosts_file"]["matches"][0]["domain"], "api.anthropic.com")
        self.assertEqual(report["profile_scan"], {"platform": "win32", "user_files": len(check.WIN_SHELL_FILES), "system_files": 0})
        proxies = [entry for item in report["shell_files"] for entry in item["entries"]]
        self.assertEqual(proxies[0]["target"], "http://relay.example:8443")
        enabled = check.windows_proxy_flags({"ProxyEnable": 1, "AutoConfigURL": True, "ProxyServer": "fixture-secret"})
        self.assertEqual(enabled["SOCKSEnable"], [1])
        self.assertNotIn("ProxyAutoDiscoveryEnable", enabled)
        self.assertNotIn("fixture-secret", json.dumps(enabled))


if __name__ == "__main__":
    unittest.main(verbosity=2)
