"""Vault auto-push — the write side of vault-carried persistence (D34).

A run's documents + DB snapshot are committed to the vault git on every governed write, but in the
ephemeral web runtime the local clone is discarded between sessions, so a commit only PERSISTS if it
reaches the vault's remote. `RFP_VAULT_AUTOPUSH` turns pushing on; it stays off for local/tests.
These tests prove a commit reaches a real (bare) remote when enabled, and does not when disabled.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.pilot.vault import git_commit_run


def _git(cwd: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True)
    return out.stdout.strip()


def _vault_with_remote(tmp_path: Path) -> tuple[Path, Path]:
    """A vault clone with an established upstream tracking branch + its bare remote."""

    remote = tmp_path / "remote.git"
    subprocess.run(
        ["git", "init", "--bare", "-b", "main", str(remote)], check=True, capture_output=True
    )
    vault = tmp_path / "vault"
    subprocess.run(["git", "clone", str(remote), str(vault)], check=True, capture_output=True)
    _git(vault, "config", "user.email", "t@kr-rfp.local")
    _git(vault, "config", "user.name", "T")
    (vault / "seed.txt").write_text("seed", encoding="utf-8")
    _git(vault, "add", "-A")
    _git(vault, "commit", "-m", "seed")
    # establish an upstream tracking branch so a bare `git push` has a target
    _git(vault, "push", "-u", "origin", "main")
    return vault, remote


def test_commit_pushes_to_remote_when_autopush_enabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault, remote = _vault_with_remote(tmp_path)
    before = _git(remote, "rev-parse", "HEAD")

    monkeypatch.setenv("RFP_VAULT_AUTOPUSH", "1")
    (vault / "runs").mkdir()
    (vault / "runs" / "note.txt").write_text("a governed change", encoding="utf-8")
    git_commit_run(vault, "demo-run", "governed write")

    after = _git(remote, "rev-parse", "HEAD")
    assert after != before  # the remote advanced — the commit was pushed (it survives the wipe)


def test_commit_pushes_to_empty_vault_with_no_upstream(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A freshly-created vault repo: an EMPTY bare remote with no commits and no branch yet, so the
    # clone has no upstream. The first governed write must still reach it (push -u origin HEAD).
    remote = tmp_path / "remote.git"
    subprocess.run(
        ["git", "init", "--bare", "-b", "main", str(remote)], check=True, capture_output=True
    )
    vault = tmp_path / "vault"
    subprocess.run(["git", "clone", str(remote), str(vault)], check=True, capture_output=True)
    _git(vault, "config", "user.email", "t@kr-rfp.local")
    _git(vault, "config", "user.name", "T")

    monkeypatch.setenv("RFP_VAULT_AUTOPUSH", "1")
    (vault / "runs").mkdir()
    (vault / "runs" / "note.txt").write_text("first governed change", encoding="utf-8")
    git_commit_run(vault, "demo-run", "first write")

    # The remote received the branch + commit despite having had no upstream to begin with.
    assert _git(remote, "rev-parse", "HEAD") == _git(vault, "rev-parse", "HEAD")


def test_commit_does_not_push_when_autopush_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault, remote = _vault_with_remote(tmp_path)
    before = _git(remote, "rev-parse", "HEAD")

    monkeypatch.delenv("RFP_VAULT_AUTOPUSH", raising=False)
    (vault / "runs").mkdir()
    (vault / "runs" / "note.txt").write_text("a local-only change", encoding="utf-8")
    git_commit_run(vault, "demo-run", "governed write")

    # The commit exists locally but the remote did NOT advance (no push without the opt-in).
    assert _git(remote, "rev-parse", "HEAD") == before
    assert _git(vault, "rev-parse", "HEAD") != before
