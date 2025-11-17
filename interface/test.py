from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import (
    Header,
    Footer,
    Button,
    Static,
    Input,
    TextArea,
    Label,
    Select,
)

import json
from config import YAMLConfig
from github.team_requests import GitHubTeamRequests


# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────
class Sidebar(Container):
    def compose(self) -> ComposeResult:
        yield Static(" Menu ", classes="title")
        yield Button("Home", id="home")
        yield Button("Settings", id="settings")
        yield Button("About", id="about")

        yield Static(" Data Views ", classes="section")

        yield Select(
            options=[
                ("Team Repos", "get_team_repos"),
            ],
            prompt="Select Data",
            id="data_select",
        )


# ─────────────────────────────────────────────────────────────
# Main Content Container
# ─────────────────────────────────────────────────────────────
class MainContent(Container):
    pass


# ─────────────────────────────────────────────────────────────
# Settings View
# ─────────────────────────────────────────────────────────────
class SettingsView(VerticalScroll):

    def __init__(self, config: YAMLConfig):
        super().__init__()
        self.config = config

    def compose(self) -> ComposeResult:
        yield Label("GitHub Settings", classes="section")

        yield Label("Active Team Members:")
        yield TextArea(
            "\n".join(self.config.config.github.active_team_members),
            id="team_members",
        )

        yield Label("Organisation:")
        yield Input(self.config.config.github.organisation, id="organisation")

        yield Label("Team:")
        yield Input(self.config.config.github.team, id="team")

        yield Label("Ignored Repositories:")
        yield TextArea(
            "\n".join(self.config.config.github.ignored_repositories),
            id="ignored_repos",
        )

        yield Label("Local Settings", classes="section")

        yield Label("Active Working Directory:")
        yield Input(
            self.config.config.local.active_working_directory,
            id="working_dir"
        )

        yield Button("Save Settings", id="save_settings", variant="primary")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id != "save_settings":
            return

        updated_config = {
            "github": {
                "active-team-members": (
                    self.query_one("#team_members", TextArea).text.splitlines()
                ),
                "organisation": self.query_one("#organisation", Input).value,
                "team": self.query_one("#team", Input).value,
                "ignored-repositories": (
                    self.query_one("#ignored_repos", TextArea).text.splitlines()
                ),
            },
            "local": {
                "active-working-directory":
                    self.query_one("#working_dir", Input).value
            }
        }

        self.config.save(updated_config)

        if hasattr(self.app, "notify"):
            self.app.notify("Settings saved.", severity="information")
        else:
            print("Settings saved.")


# ─────────────────────────────────────────────────────────────
# Main Application
# ─────────────────────────────────────────────────────────────
class MyApp(App):
    CSS_PATH = "styles.css"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Sidebar(id="sidebar")
        yield MainContent(id="content")
        yield Footer()

    # ─────────────────────────────────────────────────────────
    # Sidebar Button Logic
    # ─────────────────────────────────────────────────────────
    def on_button_pressed(self, event: Button.Pressed):
        content = self.query_one("#content", MainContent)
        content.remove_children()

        # home page
        if event.button.id == "home":
            view = Static("🏠 Home Page\n\nThis is the home screen.")
            view.styles.height = "100%"
            view.styles.width = "100%"
            content.mount(view)

        # settings page
        elif event.button.id == "settings":
            cfg = YAMLConfig()
            content.mount(SettingsView(cfg))

        # about page
        elif event.button.id == "about":
            about = Static("ℹ️ About\n\nA demo Textual TUI with a sidebar.")
            about.styles.height = "100%"
            about.styles.width = "100%"
            content.mount(about)

    # ─────────────────────────────────────────────────────────
    # Dropdown Handler
    # ─────────────────────────────────────────────────────────
    def on_select_changed(self, event: Select.Changed):
        if event.select.id != "data_select":
            return

        selected = event.value
        content = self.query_one("#content", MainContent)
        content.remove_children()

        # Mapping from dropdown values → functions
        data_function_map = {
            "get_team_repos": self.get_team_repos
        }

        if selected not in data_function_map:
            content.mount(Static(f"No function for: {selected}"))
            return

        # Execute data-producing function
        raw_data = data_function_map[selected]()

        # Prevent double-encoding JSON
        if isinstance(raw_data, str):
            pretty_json = raw_data
        else:
            pretty_json = json.dumps(raw_data, indent=2)

        # Display JSON
        ta = TextArea(pretty_json, read_only=True)
        ta.styles.height = "100%"
        ta.styles.width = "100%"
        content.mount(ta)

    # ─────────────────────────────────────────────────────────
    # JSON-producing functions
    # ─────────────────────────────────────────────────────────
    def get_team_repos(self):
        config = YAMLConfig()
        gtr = GitHubTeamRequests(
            config.config.github.organisation,
            config.config.github.team,
        )
        return gtr.get_team_repos().value()


# ─────────────────────────────────────────────────────────────
# Run the app
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    MyApp().run()
