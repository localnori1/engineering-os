import importlib.util
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/eos.py"
SPEC = importlib.util.spec_from_file_location("eos", SCRIPT)
eos = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["eos"] = eos
SPEC.loader.exec_module(eos)

EVAL_SCRIPT = Path(__file__).resolve().parents[1] / "scripts/eval_os.py"
EVAL_SPEC = importlib.util.spec_from_file_location("eval_os", EVAL_SCRIPT)
eval_os = importlib.util.module_from_spec(EVAL_SPEC)
assert EVAL_SPEC.loader is not None
sys.modules["eval_os"] = eval_os
EVAL_SPEC.loader.exec_module(eval_os)


class EngineeringOsTests(unittest.TestCase):
    def test_cli_new_end_to_end(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "project"
            result = eos.main(["new", str(target), "--name", "CLI Example", "--no-git"])
            self.assertEqual(0, result)
            self.assertTrue((target / "docs/project/PROJECT.md").exists())

    def test_new_creates_valid_initialized_project(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "project"
            eos.copy_template(target)
            actions = eos.initialize(target, "Example", no_git=True)
            self.assertTrue((target / "docs/project/PROJECT.md").exists())
            self.assertTrue((target / ".claude/skills").exists())
            self.assertTrue((target / "docs/project/SERVICES.md").exists())
            self.assertTrue((target / ".claude/agents/reviewer.md").exists())
            self.assertIn("Example", (target / "docs/project/PROJECT.md").read_text())
            self.assertTrue(any("created docs/project" in action for action in actions))
            errors = [f for f in eos.check_repository(target, strict=True) if f.level == "error"]
            self.assertEqual([], errors)

    def test_initialize_is_idempotent_and_preserves_project_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "project"
            eos.copy_template(target)
            eos.initialize(target, "First", no_git=True)
            project = target / "docs/project/PROJECT.md"
            project.write_text("custom project state\n", encoding="utf-8")
            eos.initialize(target, "Second", no_git=True)
            self.assertEqual("custom project state\n", project.read_text(encoding="utf-8"))

    def test_git_initialization_and_hook_installation(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "project"
            eos.copy_template(target)
            actions = eos.initialize(target, "Example", no_git=False)
            self.assertTrue((target / ".git").is_dir())
            self.assertTrue(any("initialized Git" in action for action in actions))
            self.assertIn("core.hooksPath", eos.install_hooks(target).replace("configured local ", ""))
            configured = eos.run(["git", "config", "--get", "core.hooksPath"], target)
            self.assertEqual(".githooks", configured.stdout.strip())

    def test_check_rejects_unfinished_skill_scaffold(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "project"
            eos.copy_template(target)
            eos.initialize(target, "Example", no_git=True)
            skill = target / "skills/context-management/SKILL.md"
            skill.write_text(skill.read_text(encoding="utf-8") + "\nTODO\n", encoding="utf-8")
            messages = [f.message for f in eos.check_repository(target, strict=True)]
            self.assertTrue(any("unfinished scaffold" in message for message in messages))

    def test_ui_engineering_is_first_class_and_legacy_ui_routes_are_removed(self):
        skill = eos.ROOT / "skills/ui-engineering/SKILL.md"
        self.assertTrue(skill.exists())
        self.assertTrue((eos.ROOT / "templates/ui-foundation.md").exists())
        self.assertFalse((eos.ROOT / "skills/engineering-change/references/ui-change.md").exists())
        self.assertFalse((eos.ROOT / "skills/engineering-review/references/ui.md").exists())

    def test_safe_environment_example_is_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "project"
            eos.copy_template(target)
            eos.initialize(target, "Example", no_git=True)
            (target / ".env.example").write_text("API_URL=https://example.test\n", encoding="utf-8")
            errors = [f.message for f in eos.check_repository(target, strict=True) if f.level == "error"]
            self.assertFalse(any("secret-like filename" in message for message in errors))

    def test_secret_named_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "project"
            eos.copy_template(target)
            eos.initialize(target, "Example", no_git=True)
            (target / ".env").symlink_to("missing-local-secret")
            errors = [f.message for f in eos.check_repository(target, strict=True) if f.level == "error"]
            self.assertTrue(any("secret-like filename" in message for message in errors))

    def test_adapter_conflict_fails_before_project_state_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "project"
            eos.copy_template(target)
            (target / ".agents/skills").mkdir(parents=True)
            with self.assertRaisesRegex(RuntimeError, "Refusing to replace"):
                eos.initialize(target, "Example", no_git=True)
            self.assertFalse((target / "docs/project/PROJECT.md").exists())

    def test_existing_claude_agents_are_kept_not_blocking(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "project"
            eos.copy_template(target)
            (target / ".claude/agents").mkdir(parents=True)
            (target / ".claude/agents/mine.md").write_text("custom", encoding="utf-8")
            actions = eos.initialize(target, "Example", no_git=True)
            self.assertTrue(any("skipped .claude/agents" in action for action in actions))
            self.assertEqual("custom", (target / ".claude/agents/mine.md").read_text())

    def test_common_live_secrets_are_detected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            # Built at runtime so this test file never contains a key-shaped string.
            samples = {
                "Stripe secret key": "sk_" + "live_" + "a1B2" * 6,
                "database URL with password": "postgres" + "://app:hunter2pass@db.example.com/prod",
            }
            for label, value in samples.items():
                (root / "config.js").write_text(f"const k = '{value}';\n", encoding="utf-8")
                messages = [f.message for f in eos.check_secrets(root)]
                self.assertTrue(any(label in m for m in messages), label)
            (root / "config.js").write_text("postgres" + "://app:pw123@localhost/dev", encoding="utf-8")
            self.assertEqual([], eos.check_secrets(root))

    def test_package_excludes_build_and_git_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "project"
            eos.copy_template(target)
            (target / "dist").mkdir()
            (target / "dist/ignored.txt").write_text("ignore", encoding="utf-8")
            (target / ".git").mkdir()
            (target / ".git/ignored").write_text("ignore", encoding="utf-8")
            (target / "docs/project").mkdir(parents=True)
            (target / "docs/project/private.md").write_text("project", encoding="utf-8")
            (target / "source/private.pdf").write_text("artifact", encoding="utf-8")
            archive = Path(temporary) / "engineering-os.zip"
            eos.package(target, archive)
            with zipfile.ZipFile(archive) as opened:
                names = opened.namelist()
            self.assertIn("AGENTS.md", names)
            self.assertNotIn("dist/ignored.txt", names)
            self.assertNotIn(".git/ignored", names)
            self.assertNotIn("docs/project/private.md", names)
            self.assertNotIn("source/private.pdf", names)

    def test_packaged_archive_can_initialize_and_validate(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "engineering-os.zip"
            eos.package(eos.ROOT, archive)
            extracted = Path(temporary) / "extracted"
            with zipfile.ZipFile(archive) as opened:
                opened.extractall(extracted)
            initialized = subprocess.run(
                [
                    sys.executable,
                    str(extracted / "scripts/eos.py"),
                    "init",
                    "--name",
                    "Packaged Example",
                    "--no-git",
                ],
                cwd=extracted,
                text=True,
                capture_output=True,
            )
            self.assertEqual(0, initialized.returncode, initialized.stderr)
            checked = subprocess.run(
                [sys.executable, str(extracted / "scripts/eos.py"), "check", "--strict"],
                cwd=extracted,
                text=True,
                capture_output=True,
            )
            self.assertEqual(0, checked.returncode, checked.stdout + checked.stderr)

    def test_new_refuses_target_inside_template(self):
        with self.assertRaisesRegex(RuntimeError, "outside the template root"):
            eos.copy_template(eos.ROOT / "nested-project")

    def test_version_is_rendered_and_update_check_never_compares_project_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            current = Path(temporary) / "current"
            candidate = Path(temporary) / "candidate"
            eos.copy_template(current)
            eos.copy_template(candidate)
            eos.initialize(current, "Versioned", no_git=True)
            project = current / "docs/project/PROJECT.md"
            self.assertIn(eos.os_version(current), project.read_text(encoding="utf-8"))
            project.write_text("local project state\n", encoding="utf-8")
            lines = eos.compare_os(current, candidate)
            self.assertEqual("No OS-owned file differences.", lines[-1])

    def test_update_check_reports_os_change_without_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            current = Path(temporary) / "current"
            candidate = Path(temporary) / "candidate"
            eos.copy_template(current)
            eos.copy_template(candidate)
            before = (current / "AGENTS.md").read_text(encoding="utf-8")
            (candidate / "AGENTS.md").write_text("candidate contract\n", encoding="utf-8")
            lines = eos.compare_os(current, candidate)
            self.assertIn("CHANGE AGENTS.md", lines)
            self.assertEqual(before, (current / "AGENTS.md").read_text(encoding="utf-8"))

    def test_behavior_eval_reference_passes_and_empty_results_fail(self):
        cases = eval_os.load_json(eos.ROOT / "evals/cases.json")
        self.assertEqual([], eval_os.validate_cases(cases))
        reference = eval_os.load_json(eos.ROOT / "evals/fixtures/reference-results.json")
        self.assertEqual([], eval_os.score(cases, reference))
        self.assertTrue(eval_os.score(cases, []))

    def test_handoff_requires_complete_structure_and_valid_timestamp(self):
        with tempfile.TemporaryDirectory() as temporary:
            handoff = Path(temporary) / "CURRENT.md"
            handoff.write_text("---\nstatus: ready\nupdated: not-a-date\n---\n\n# Current\n", encoding="utf-8")
            messages = [finding.message for finding in eos.check_handoff(handoff, strict=True)]
            self.assertTrue(any("updated timestamp" in message for message in messages))
            self.assertTrue(any("Exact next step" in message for message in messages))

    def test_knowledge_check_detects_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / "docs/requirements"
            directory.mkdir(parents=True)
            record = "---\nid: REQ-001\nstatus: proposed\nclassification: provided\n---\n\n## Provenance\n\nSource.\n"
            (directory / "one.md").write_text(record, encoding="utf-8")
            (directory / "two.md").write_text(record, encoding="utf-8")
            messages = [finding.message for finding in eos.check_knowledge(root, strict=True)]
            self.assertTrue(any("duplicate knowledge id REQ-001" in message for message in messages))


if __name__ == "__main__":
    unittest.main()
