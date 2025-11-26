from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button, Static


class Sidebar(Container):
    def compose(self) -> ComposeResult:
        yield Static(" Menu ", classes="title")
        yield Button("Home", id="home")
        yield Button("Settings", id="settings")
        yield Button("Github", id="github")
