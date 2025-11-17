import json

from textual.app import App
from textual.containers import Container
from textual.widgets import (
    Header,
    Footer,
    Button,
    Static,
    Select,
)

from JsonTreeViewer import JsonTreeViewer
from config import YAMLConfig
from github.team_requests import GitHubTeamRequests
from Sidebar import Sidebar
from SettingsView import SettingsView


class MainContent(Container):
    pass

class MyApp(App):
    CSS_PATH = "styles.css"

    def compose(self):
        yield Header()
        yield Sidebar(id="sidebar")
        yield MainContent(id="content")
        yield Footer()

    # ---------------- Home / Settings / About ----------------
    def on_button_pressed(self, event: Button.Pressed):
        content = self.query_one("#content", MainContent)
        content.remove_children()

        if event.button.id == "home":
            view = Static("🏠 Home Page\n\nThis is the home screen.")
            view.styles.width = "100%"
            view.styles.height = "100%"
            content.mount(view)

        elif event.button.id == "settings":
            cfg = YAMLConfig()
            content.mount(SettingsView(cfg))

        elif event.button.id == "about":
            view = Static("ℹ️ About\n\nA demo Textual TUI with sidebar & JSON viewer.")
            view.styles.width = "100%"
            view.styles.height = "100%"
            content.mount(view)

    # ---------------------- Dropdown ----------------------
    def on_select_changed(self, event: Select.Changed):
        if event.select.id != "data_select":
            return

        handler = {
            "get_team_repos": self.get_team_repos,
        }.get(event.value)

        content = self.query_one("#content", MainContent)
        content.remove_children()

        if not handler:
            content.mount(Static("No handler found."))
            return

        raw = handler()

        # Normalize JSON
        if isinstance(raw, str):
            try:
                data = json.loads(raw)
            except:
                content.mount(Static(raw))
                return
        else:
            data = raw

        viewer = JsonTreeViewer(data, title="Team Repos", label_key="name")
        content.mount(viewer)

    # ---------------------- Data Function ----------------------
    def get_team_repos(self):
        cfg = YAMLConfig()
        gtr = GitHubTeamRequests(cfg.config.github.organisation,
                                 cfg.config.github.team)
        return gtr.get_team_repos().value()


# ─────────────────────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    MyApp().run()
