#!/usr/bin/env python3
"""Filesystem safety tests using only disposable fixtures under /private/tmp."""

import contextlib
import io
import json
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import claude_local_reset as reset


class ResetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="claude-reset-fixture-", dir="/private/tmp")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "simulated-home"
        self.home.mkdir()
        self.environment = mock.patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.guard = mock.patch.object(reset, "require_stopped")
        self.guard.start()
        self.addCleanup(self.guard.stop)
        self.console = io.StringIO()
        self.output = contextlib.redirect_stdout(self.console)
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)
        self.error_output = contextlib.redirect_stderr(io.StringIO())
        self.error_output.__enter__()
        self.addCleanup(self.error_output.__exit__, None, None, None)

    def put(self, relative, content=b"fixture"):
        path = self.home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            content = content.encode()
        path.write_bytes(content)
        return path

    def desktop(self):
        self.put(reset.DESKTOP_PATHS[0] + "/ant-did", b"old-device-fixture")
        self.put(reset.DESKTOP_PATHS[0] + "/claude_desktop_config.json", b'{"mcpServers":{}}')
        self.put(reset.DESKTOP_PATHS[0] + "/claude-code-sessions/session.json", b"old-session")
        self.put(reset.DESKTOP_PATHS[1] + "/cache.bin", b"old-cache")
        self.put(reset.DESKTOP_PATHS[4] + "/mcp-server.log", b"old-log")
        self.put(reset.DESKTOP_PATHS[5], b"old-plist-bytes")

    def code(self):
        data = {
            "userID": "a" * 64,
            "machineID": "b" * 64,
            "anonymousId": "dummy-anonymous-id",
            "oauthAccount": {"emailAddress": "fixture@example.invalid"},
            "projects": {"/sample/project": {"trusted": True}},
            "mcpServers": {"sample": {"env": {"TOKEN": "fixture-secret-never-print"}}},
            "unknownFutureSetting": {"userID": "nested-field-preserved"},
        }
        self.put(".claude.json", json.dumps(data, indent=4))
        self.put(".claude.json.backup", json.dumps(data))
        self.put(".claude/backups/.claude.json.backup.123", json.dumps(data))
        self.put(".claude/backups/unrelated.txt", b"keep-rolling-misc")
        self.put(".claude/skills/sample/SKILL.md", b"keep-skill")
        self.put(".claude/settings.json", b'{"env":{"DISABLE_TELEMETRY":"1"}}')
        self.put(".claude/projects/sample/history.jsonl", b"keep-history")
        self.put(".claude/hooks/sample.sh", b"keep-hook")
        self.put(".claude/statsig/id", b"old-local-feature-id")
        self.put(".claude/telemetry/queue", b"old-local-events")
        self.put(".claude/.credentials.json", b"fixture-fallback-token")
        return data

    def tree(self):
        result = {}
        for path in self.home.rglob("*"):
            relative = path.relative_to(self.home).as_posix()
            if path.is_symlink():
                result[relative] = ("symlink", os.readlink(path))
            elif path.is_file():
                result[relative] = path.read_bytes()
            else:
                result[relative] = ("directory",)
        return result

    def test_preview_and_cli_default_are_read_only(self):
        self.desktop()
        self.code()
        before = self.tree()
        with mock.patch.object(Path, "home", return_value=self.home), mock.patch.object(reset.sys, "platform", "darwin"):
            self.assertEqual(reset.main([]), 0)
            self.assertEqual(reset.main(["--code-identity"]), 0)
        self.assertEqual(before, self.tree())
        self.assertFalse((self.home / reset.BACKUP_ROOT).exists())

    def test_default_preserves_all_code_bytes(self):
        self.desktop()
        self.code()
        before = {key: value for key, value in self.tree().items() if key.startswith(".claude")}
        batch = reset.apply_plan(self.home, reset.build_plan(self.home))
        after = {key: value for key, value in self.tree().items() if key.startswith(".claude")}
        self.assertEqual(before, after)
        self.assertEqual((batch / "original" / reset.DESKTOP_PATHS[0] / "claude-code-sessions/session.json").read_bytes(), b"old-session")
        self.assertFalse((self.home / reset.DESKTOP_PATHS[0]).exists())

    def test_move_preserves_nested_links_without_following_them(self):
        self.desktop()
        unrelated = self.put("unrelated/private", b"untouched")
        link = self.home / reset.DESKTOP_PATHS[0] / "external-link"
        link.symlink_to(unrelated)
        batch = reset.apply_plan(self.home, reset.build_plan(self.home))
        saved = batch / "original" / reset.DESKTOP_PATHS[0] / "external-link"
        self.assertTrue(saved.is_symlink())
        self.assertEqual(os.readlink(saved), str(unrelated))
        self.assertEqual(unrelated.read_bytes(), b"untouched")

    def test_optional_code_rotation_preserves_other_config_and_assets(self):
        self.desktop()
        original = self.code()
        original_bytes = (self.home / ".claude.json").read_bytes()
        protected = {key: value for key, value in self.tree().items() if key.startswith((".claude/skills", ".claude/projects", ".claude/hooks")) or key in {".claude/settings.json", ".claude/backups/unrelated.txt"}}
        batch = reset.apply_plan(self.home, reset.build_plan(self.home, True))
        current = reset.read_json(self.home / ".claude.json")
        for key in reset.IDENTITY_KEYS:
            self.assertNotEqual(current[key], original[key])
            self.assertRegex(current[key], r"^[0-9a-f]{64}$")
        self.assertNotIn("anonymousId", current)
        self.assertNotIn("oauthAccount", current)
        for key in original.keys() - set(reset.IDENTITY_KEYS) - {"anonymousId", "oauthAccount"}:
            self.assertEqual(current[key], original[key])
        self.assertEqual((batch / "original/.claude.json").read_bytes(), original_bytes)
        for relative, expected in protected.items():
            self.assertEqual(self.tree()[relative], expected)
        for relative in (*reset.CODE_PATHS, ".claude/backups/.claude.json.backup.123"):
            self.assertFalse((self.home / relative).exists())
            self.assertTrue((batch / "original" / relative).exists())
        self.assertEqual(stat.S_IMODE(batch.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((batch / "original/.claude.json").stat().st_mode), 0o600)

    def test_restore_preserves_new_profile_and_restores_exact_original(self):
        self.desktop()
        self.code()
        original = self.tree()
        batch = reset.apply_plan(self.home, reset.build_plan(self.home, True))
        self.put(reset.DESKTOP_PATHS[0] + "/new-conversation.json", b"new-conversation")
        new_identity = (self.home / ".claude.json").read_bytes()
        before_preview = self.tree()
        count = reset.restore_batch(self.home, batch)
        self.assertGreater(count, 0)
        self.assertEqual(before_preview, self.tree())
        self.assertEqual(reset.restore_batch(self.home, batch, True), count)
        restored = {key: value for key, value in self.tree().items() if not key.startswith(reset.BACKUP_ROOT)}
        self.assertEqual(original, restored)
        self.assertEqual((batch / "current-before-restore" / reset.DESKTOP_PATHS[0] / "new-conversation.json").read_bytes(), b"new-conversation")
        self.assertEqual((batch / "current-before-restore/.claude.json").read_bytes(), new_identity)
        before_repeat = self.tree()
        with self.assertRaises(ValueError):
            reset.restore_batch(self.home, batch, True)
        self.assertEqual(before_repeat, self.tree())

    def test_no_targets_does_not_create_backup(self):
        self.assertEqual(reset.build_plan(self.home), [])
        self.assertIsNone(reset.apply_plan(self.home, []))
        self.assertEqual(self.tree(), {})

    def test_symlinked_desktop_parent_is_rejected_before_writes(self):
        outside = self.home / "other"
        outside.mkdir()
        (self.home / "Library").symlink_to(outside, target_is_directory=True)
        before = self.tree()
        with self.assertRaises(ValueError):
            reset.build_plan(self.home)
        self.assertEqual(before, self.tree())

    def test_symlinked_backup_root_is_rejected(self):
        self.desktop()
        outside = self.home / "other"
        outside.mkdir()
        (self.home / reset.BACKUP_ROOT).symlink_to(outside, target_is_directory=True)
        before = self.tree()
        with self.assertRaises(ValueError):
            reset.build_plan(self.home)
        self.assertEqual(before, self.tree())

    def test_bad_code_json_stops_before_any_desktop_action(self):
        self.desktop()
        self.put(".claude.json", b"{invalid}")
        before = self.tree()
        with self.assertRaises(ValueError):
            reset.build_plan(self.home, True)
        self.assertEqual(before, self.tree())

    def test_duplicate_json_keys_are_not_silently_dropped(self):
        self.desktop()
        self.put(".claude.json", '{"userID":"' + "a" * 64 + '","projects":{},"projects":{"keep":1}}')
        before = self.tree()
        with self.assertRaises(ValueError):
            reset.build_plan(self.home, True)
        self.assertEqual(before, self.tree())

    def test_missing_or_unknown_id_format_is_rejected(self):
        self.desktop()
        for data in ({"userID": "unexpected-new-format"}, {"mcpServers": {}}):
            with self.subTest(data=data):
                self.put(".claude.json", json.dumps(data))
                before = self.tree()
                with self.assertRaises(ValueError):
                    reset.build_plan(self.home, True)
                self.assertEqual(before, self.tree())

    def test_custom_config_does_not_silently_touch_default_code(self):
        self.desktop()
        self.code()
        before = self.tree()
        with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": "/fixture/custom"}):
            with self.assertRaises(ValueError):
                reset.build_plan(self.home, True)
            self.assertTrue(reset.build_plan(self.home))
        self.assertEqual(before, self.tree())

    def test_changed_inputs_stop_before_backup_creation(self):
        self.desktop()
        self.code()
        plan = reset.build_plan(self.home, True)
        self.put(".claude.json", b"changed-after-preview")
        before = self.tree()
        with self.assertRaises(ValueError):
            reset.apply_plan(self.home, plan)
        self.assertEqual(before, self.tree())

    def test_partial_move_failure_keeps_originals_recoverable(self):
        self.desktop()
        original = self.tree()
        plan = reset.build_plan(self.home)
        real_rename = os.rename

        def fail_second(source, destination):
            if Path(source) == self.home / reset.DESKTOP_PATHS[1]:
                raise OSError("fixture move failure")
            return real_rename(source, destination)

        with mock.patch.object(reset.os, "rename", side_effect=fail_second):
            with self.assertRaises(OSError):
                reset.apply_plan(self.home, plan)
        batches = list((self.home / reset.BACKUP_ROOT).iterdir())
        self.assertEqual(len(batches), 1)
        self.assertEqual(reset.read_json(batches[0] / "manifest.json")["status"], "partial")
        self.assertEqual(reset.restore_batch(self.home, batches[0], True), 1)
        restored = {key: value for key, value in self.tree().items() if not key.startswith(reset.BACKUP_ROOT)}
        self.assertEqual(original, restored)

    def test_tampered_manifest_cannot_target_unrelated_files(self):
        self.desktop()
        batch = reset.apply_plan(self.home, reset.build_plan(self.home))
        self.put("unrelated", b"keep")
        manifest = reset.read_json(batch / "manifest.json")
        manifest["entries"][0]["path"] = "../../unrelated"
        reset.atomic_json(batch / "manifest.json", manifest)
        before = self.tree()
        with self.assertRaises(ValueError):
            reset.restore_batch(self.home, batch, True)
        self.assertEqual(before, self.tree())

    def test_corrupt_code_backup_blocks_restore_before_writes(self):
        self.desktop()
        self.code()
        batch = reset.apply_plan(self.home, reset.build_plan(self.home, True))
        (batch / "original/.claude.json").write_bytes(b"corrupted")
        before = self.tree()
        with self.assertRaises(ValueError):
            reset.restore_batch(self.home, batch, True)
        self.assertEqual(before, self.tree())

    def test_running_process_guard_stops_without_creating_backup(self):
        self.desktop()
        before = self.tree()
        with mock.patch.object(reset, "require_stopped", side_effect=ValueError("fixture running")):
            with self.assertRaises(ValueError):
                reset.apply_plan(self.home, reset.build_plan(self.home))
        self.assertEqual(before, self.tree())

    def test_process_scan_does_not_print_command_secrets(self):
        self.guard.stop()
        fake_processes = SimpleNamespace(stdout="123 /Applications/Claude.app/Contents/MacOS/Claude --token fixture-process-secret\n456 python3 claude_local_reset.py\n789 node /fixture/home/.claude-code-router/server.js --key fixture-router-secret\n")
        with mock.patch.object(reset.subprocess, "run", return_value=fake_processes):
            with self.assertRaises(ValueError) as caught:
                reset.require_stopped()
        self.assertIn("123", str(caught.exception))
        self.assertIn("789", str(caught.exception))
        self.assertNotIn("fixture-process-secret", str(caught.exception))
        self.assertNotIn("fixture-router-secret", str(caught.exception))
        self.assertNotIn("456", str(caught.exception))

    def test_cli_does_not_emit_credentials_or_identity_values(self):
        self.desktop()
        self.code()
        with mock.patch.object(Path, "home", return_value=self.home), mock.patch.object(reset.sys, "platform", "darwin"):
            self.assertEqual(reset.main(["--code-identity", "--apply"]), 0)
        for secret in ("fixture-secret-never-print", "fixture-fallback-token", "fixture@example.invalid", "a" * 64, "b" * 64, "old-device-fixture"):
            self.assertNotIn(secret, self.console.getvalue())

    def test_windows_archives_profile_data_and_leaves_installer_and_other_apps(self):
        self.put("AppData/Roaming/Claude/ant-did", b"old-device-fixture")
        self.put("AppData/Roaming/Claude/claude_desktop_config.json", b"{}")
        self.put("AppData/Local/Packages/Claude_fixturehash/LocalCache/Roaming/Claude/Local Storage/data", b"old-storage")
        self.put("AppData/Local/Packages/Claude_fixturehash/LocalCache/Local/installer-must-stay", b"keep-package")
        self.put("AppData/Local/AnthropicClaude/app/Claude.exe", b"keep-installer")
        self.put("AppData/Local/Packages/OtherApp_hash/LocalCache/Roaming/Claude/ant-did", b"not-this-app")
        self.put("AppData/Local/Claude-3p/ant-did", b"keep-3p")
        with mock.patch.object(reset.sys, "platform", "win32"):
            plan = reset.build_plan(self.home)
            batch = reset.apply_plan(self.home, plan)
        self.assertEqual(
            {entry["path"] for entry in plan},
            {
                "AppData/Roaming/Claude",
                "AppData/Local/Packages/Claude_fixturehash/LocalCache/Roaming/Claude",
            },
        )
        self.assertFalse((self.home / "AppData/Roaming/Claude").exists())
        self.assertEqual((batch / "original/AppData/Roaming/Claude/ant-did").read_bytes(), b"old-device-fixture")
        self.assertEqual((self.home / "AppData/Local/AnthropicClaude/app/Claude.exe").read_bytes(), b"keep-installer")
        self.assertEqual((self.home / "AppData/Local/Packages/Claude_fixturehash/LocalCache/Local/installer-must-stay").read_bytes(), b"keep-package")
        self.assertEqual((self.home / "AppData/Local/Claude-3p/ant-did").read_bytes(), b"keep-3p")
        self.assertEqual((self.home / "AppData/Local/Packages/OtherApp_hash/LocalCache/Roaming/Claude/ant-did").read_bytes(), b"not-this-app")

    def test_windows_preview_is_read_only_and_linux_is_refused(self):
        self.put("AppData/Roaming/Claude/ant-did", b"old-device-fixture")
        before = self.tree()
        with mock.patch.object(Path, "home", return_value=self.home), mock.patch.object(reset.sys, "platform", "win32"):
            self.assertEqual(reset.main([]), 0)
        self.assertEqual(before, self.tree())
        self.assertIn("安装目录", self.console.getvalue())
        self.assertNotIn("old-device-fixture", self.console.getvalue())
        with mock.patch.object(Path, "home", return_value=self.home), mock.patch.object(reset.sys, "platform", "linux"):
            with self.assertRaises(SystemExit) as caught:
                reset.main(["--apply"])
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual(before, self.tree())

    def test_windows_tasklist_uses_image_names_only(self):
        listing = "\n".join([
            '"Claude.exe","321","Console","1","100 K"',
            '"claude.exe","654","Console","1","20 K"',
            '"node.exe","999","Console","1","20 K"',
            '"claude-code-router.exe","777","Console","1","20 K"',
            "not,csv",
        ])
        self.assertEqual(reset.pids_from_tasklist(listing, "654"), ["321", "777"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
