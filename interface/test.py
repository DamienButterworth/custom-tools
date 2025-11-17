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
)

from config import YAMLConfig

class Sidebar(Container):
    def compose(self) -> ComposeResult:
        yield Static(" Menu ", classes="title")
        yield Button("Home", id="home")
        yield Button("Settings", id="settings")
        yield Button("About", id="about")


class MainContent(Container):
    pass


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

        # Local section
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

        # Safe notify across Textual versions
        if hasattr(self.app, "notify"):
            self.app.notify("Settings saved.", severity="information")
        else:
            print("Settings saved.")


class MyApp(App):
    CSS_PATH = "styles.css"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Sidebar(id="sidebar")
        yield MainContent(id="content")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        content = self.query_one("#content", MainContent)
        content.remove_children()

        if event.button.id == "home":
            content.mount(
                Static("🏠 Home Page\n\nThis is the home screen.", expand=True)
            )

        elif event.button.id == "settings":
            cfg = YAMLConfig()
            content.mount(SettingsView(cfg))

        elif event.button.id == "about":
            content.mount(
                Static("ℹ️ About\n\nA demo Textual TUI with a sidebar.", expand=True)
            )


if __name__ == "__main__":
    MyApp().run()
