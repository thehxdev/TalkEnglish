from typing import Optional
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Label, TextArea
from talkenglish.middleware import PromptMiddleware

TUI_CSS = """
Screen {
    background: $surface-darken-2;
}

#layout {
    height: 100%;
    padding: 1 2;
}

.panel {
    border: round $primary;
    background: $surface;
    padding: 0 1;
    margin-bottom: 1;
    height: 1fr;
}

.panel-title {
    text-style: bold;
    color: $accent;
    padding: 0 0;
}

TextArea {
    height: 1fr;
    border: solid $surface-lighten-1;
}

#output-text {
    background: $surface-darken-1;
}

.actions {
    height: auto;
    margin-top: 1;
    margin-bottom: 0;
}

Button {
    margin-right: 1;
}
"""

class TalkEnglishApp(App):
    CSS = TUI_CSS
    TITLE = "TalkEnglish"
    SUB_TITLE = "Engineering Prompt Refiner"

    BINDINGS = [
        Binding("ctrl+j", "refine", "Refine (Ctrl+J)", priority=True),
        Binding("ctrl+enter", "refine", "Refine (Ctrl+Enter)", priority=True),
        Binding("f5", "refine", "Refine (F5)", priority=True),
        Binding("ctrl+k", "clear", "Clear (Ctrl+K)"),
        Binding("ctrl+c", "quit", "Quit", priority=True),
    ]

    def __init__(self, middleware: Optional[PromptMiddleware] = None):
        super().__init__()
        self.middleware = middleware or PromptMiddleware()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="layout"):
            with Vertical(classes="panel"):
                yield Label("Raw Input Prompt (Any Language):", classes="panel-title")
                yield TextArea(
                    id="input-text",
                    show_line_numbers=True,
                )
                with Horizontal(classes="actions"):
                    yield Button("Refine Prompt", id="btn-refine", variant="primary")
                    yield Button("Clear", id="btn-clear", variant="error")

            with Vertical(classes="panel"):
                yield Label("Refined Engineering Prompt (English):", classes="panel-title")
                yield TextArea(
                    id="output-text",
                    read_only=True,
                    show_line_numbers=True,
                )
                with Horizontal(classes="actions"):
                    yield Button("Copy to Clipboard", id="btn-copy", variant="success")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn-refine":
            self.action_refine()
        elif button_id == "btn-clear":
            self.action_clear()
        elif button_id == "btn-copy":
            self.action_copy()

    def action_clear(self) -> None:
        input_area = self.query_one("#input-text", TextArea)
        input_area.text = ""
        input_area.focus()
        self.notify("Input cleared.")

    def action_copy(self) -> None:
        output_area = self.query_one("#output-text", TextArea)
        text = output_area.text.strip()
        if text:
            self.copy_to_clipboard(text)
            self.notify("Copied refined prompt to clipboard!", severity="information")
        else:
            self.notify("Nothing to copy.", severity="warning")

    def action_refine(self) -> None:
        input_area = self.query_one("#input-text", TextArea)
        text = input_area.text.strip()
        if not text:
            self.notify("Input prompt is empty.", severity="warning")
            return

        btn_refine = self.query_one("#btn-refine", Button)
        btn_refine.disabled = True
        self.notify("Refining prompt for coding agent...", severity="information")
        self._run_refine(text)

    @work(thread=True)
    def _run_refine(self, text: str) -> None:
        try:
            result = self.middleware.process(text)
            self.app.call_from_thread(self._on_refine_success, result)
        except Exception as e:
            self.app.call_from_thread(self._on_refine_error, str(e))

    def _on_refine_success(self, result: str) -> None:
        output_area = self.query_one("#output-text", TextArea)
        output_area.text = result
        btn_refine = self.query_one("#btn-refine", Button)
        btn_refine.disabled = False
        self.notify("Refinement complete!", severity="information")

    def _on_refine_error(self, err_msg: str) -> None:
        btn_refine = self.query_one("#btn-refine", Button)
        btn_refine.disabled = False
        self.notify(f"Refinement error: {err_msg}", severity="error")

def run_tui() -> None:
    app = TalkEnglishApp()
    app.run()
