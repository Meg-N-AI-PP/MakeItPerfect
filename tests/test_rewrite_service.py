from app.models.app_state import AppState
from app.models.dto import ClipboardSnapshot, RewriteResult
from app.models.enums import PromptMode
from app.services.rewrite_service import RewriteService


class FakeClipboard:
    def __init__(self, selection):
        self._selection = selection
        self.pasted = None
        self.restored = False

    def snapshot(self):
        return ClipboardSnapshot(text="old", had_text=True)

    def capture_selection(self):
        return self._selection

    def paste_text(self, text):
        self.pasted = text

    def restore(self, snapshot):
        self.restored = True


class FakeOpenAI:
    def __init__(self, response="REWRITTEN", error=None):
        self._response = response
        self._error = error

    def rewrite(self, text, model, mode, result_language=None):
        if self._error:
            raise self._error
        return self._response


def _state():
    return AppState(model="gpt-5", mode=PromptMode.MAKE_IT_BETTER, is_running=True)


def test_successful_rewrite_pastes_and_restores():
    clipboard = FakeClipboard(selection="hello")
    service = RewriteService(_state(), clipboard, FakeOpenAI("HELLO"), restore_clipboard=True)
    result = service.run()
    assert isinstance(result, RewriteResult)
    assert result.success
    assert clipboard.pasted == "HELLO"
    assert clipboard.restored


def test_no_selection_reports_error():
    clipboard = FakeClipboard(selection="   ")
    service = RewriteService(_state(), clipboard, FakeOpenAI(), restore_clipboard=True)
    result = service.run()
    assert not result.success
    assert result.message == "No text selected."
    assert clipboard.pasted is None
    assert clipboard.restored
