"""Rendering with an installed browser (issue #12): VIZ_BROWSER_PATH or VIZ_BROWSER_CHANNEL names the browser to
launch, and then nothing is downloaded. No browser runs here: a fake Playwright records the launch arguments."""
from __future__ import annotations

import pytest

from viz import render


class FakeChromium:
    def __init__(self, errors=()):
        self.calls, self.errors = [], list(errors)

    def launch(self, **kwargs):
        self.calls.append(kwargs)
        if self.errors:
            raise self.errors.pop(0)
        return "browser"


class FakePlaywright:
    def __init__(self, errors=()):
        self.chromium, self.stopped = FakeChromium(errors), False

    def stop(self):
        self.stopped = True


@pytest.fixture(autouse=True)
def no_download(monkeypatch):
    """Each test starts with neither variable set, and a download attempt is recorded rather than run."""
    monkeypatch.delenv("VIZ_BROWSER_PATH", raising=False)
    monkeypatch.delenv("VIZ_BROWSER_CHANNEL", raising=False)
    runs = []
    monkeypatch.setattr(render.subprocess, "run", lambda *a, **k: runs.append(a))
    return runs


def test_channel_is_passed_to_the_launch(monkeypatch, no_download):
    monkeypatch.setenv("VIZ_BROWSER_CHANNEL", "chrome")
    pw = FakePlaywright()
    assert render._launch(pw) == "browser"
    assert pw.chromium.calls == [{"args": ["--no-sandbox"], "channel": "chrome"}]
    assert not no_download


def test_path_wins_over_channel(monkeypatch):
    monkeypatch.setenv("VIZ_BROWSER_CHANNEL", "chrome")
    monkeypatch.setenv("VIZ_BROWSER_PATH", "/opt/chrome/chrome")
    pw = FakePlaywright()
    render._launch(pw)
    assert pw.chromium.calls == [{"args": ["--no-sandbox"], "executable_path": "/opt/chrome/chrome"}]


def test_a_named_browser_that_fails_is_not_replaced_by_the_download(monkeypatch, no_download):
    monkeypatch.setenv("VIZ_BROWSER_CHANNEL", "msedge")
    pw = FakePlaywright([RuntimeError("Executable doesn't exist at /Applications/Microsoft Edge.app")])
    with pytest.raises(RuntimeError, match="Executable doesn't exist"):
        render._launch(pw)
    assert len(pw.chromium.calls) == 1 and not no_download


def test_without_a_setting_the_first_use_downloads_and_retries(no_download, capsys):
    pw = FakePlaywright([RuntimeError("Executable doesn't exist at ~/.cache/ms-playwright")])
    assert render._launch(pw) == "browser"
    assert pw.chromium.calls == [{"args": ["--no-sandbox"]}] * 2
    assert len(no_download) == 1 and "chromium-headless-shell" in no_download[0][0]
    assert "installing headless Chromium" in capsys.readouterr().err


def test_without_a_setting_another_launch_error_is_raised_as_before(no_download):
    pw = FakePlaywright([RuntimeError("Target page, context or browser has been closed")])
    with pytest.raises(RuntimeError, match="has been closed"):
        render._launch(pw)
    assert pw.chromium.calls == [{"args": ["--no-sandbox"]}] and not no_download


@pytest.mark.parametrize("name, value", [("VIZ_BROWSER_CHANNEL", "chrome"), ("VIZ_BROWSER_PATH", "/opt/chrome/chrome")])
def test_setup_downloads_nothing_when_a_browser_is_named(monkeypatch, no_download, capsys, name, value):
    monkeypatch.setenv(name, value)
    render.install_browser()
    assert not no_download
    assert value in capsys.readouterr().err


def test_setup_downloads_when_no_browser_is_named(no_download):
    render.install_browser()
    assert len(no_download) == 1


def test_renderer_stops_playwright_when_the_launch_fails(monkeypatch):
    import playwright.sync_api as api
    pw = FakePlaywright([RuntimeError("Target page, context or browser has been closed")])

    class Starter:
        def start(self):
            return pw

    monkeypatch.setattr(api, "sync_playwright", lambda: Starter())
    with pytest.raises(RuntimeError, match="has been closed"):
        render.Renderer()
    assert pw.stopped
