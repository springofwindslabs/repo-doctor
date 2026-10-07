"""Smoke tests for repo-doctor (stdlib unittest, no deps)."""
import json
import tempfile
import unittest
from pathlib import Path

from repo_doctor.checks import diagnose, grade_of
from repo_doctor.report import render_json, render_markdown


def make_repo(tmp: Path, *, good: bool) -> Path:
    root = tmp / ("good" if good else "bad")
    root.mkdir()
    if good:
        (root / "README.md").write_text("# demo\n\n## Install\npip install demo\n\n"
                                        "## Usage\ndemo --help\n" + "x" * 300, encoding="utf-8")
        (root / "LICENSE").write_text("MIT", encoding="utf-8")
        (root / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
        (root / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")
        t = root / "tests"; t.mkdir()
        (t / "test_demo.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
        w = root / ".github" / "workflows"; w.mkdir(parents=True)
        (w / "ci.yml").write_text("on: push\n", encoding="utf-8")
    else:
        (root / "app.py").write_text(
            'AWS = "AKIA' + "Q" * 16 + '"\n'
            'db_password = "hunter2hunter2"\n', encoding="utf-8")
        (root / ".env").write_text("TOKEN=abc12345678\n", encoding="utf-8")
    return root


class TestDiagnose(unittest.TestCase):
    def test_good_repo_scores_high(self):
        with tempfile.TemporaryDirectory() as td:
            d = diagnose(make_repo(Path(td), good=True))
            self.assertGreaterEqual(d.score, 75, d)

    def test_bad_repo_scores_low_and_finds_secrets(self):
        with tempfile.TemporaryDirectory() as td:
            d = diagnose(make_repo(Path(td), good=False))
            self.assertLess(d.score, 60)
            crit = [f for f in d.findings if f.severity == "critical"]
            self.assertTrue(any("AWS" in f.message for f in crit), crit)
            self.assertTrue(any(".env" in f.message for f in crit), crit)

    def test_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            d = diagnose(make_repo(Path(td), good=True))
            obj = json.loads(render_json(d))
            self.assertEqual(obj["tool"], "repo-doctor")
            self.assertIn("| Check |", render_markdown(d))

    def test_grades(self):
        self.assertEqual(grade_of(95), "A")
        self.assertEqual(grade_of(10), "F")


if __name__ == "__main__":
    unittest.main()
