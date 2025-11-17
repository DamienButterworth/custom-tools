from textual.containers import VerticalScroll
from textual.widgets import (
    Button,
    Input,
    TextArea,
    Label,
)

from config import YAMLConfig


class SettingsView(VerticalScroll):
    def __init__(self, config: YAMLConfig):
        super().__init__()
        self.config = config

    def compose(self):
        yield Label("GitHub Settings", classes="section")

        yield Label("Active Team Members:")
        yield TextArea("\n".join(self.config.config.github.active_team_members),
                       id="team_members")

        yield Label("Organisation:")
        yield Input(self.config.config.github.organisation, id="organisation")

        yield Label("Team:")
        yield Input(self.config.config.github.team, id="team")

        yield Label("Ignored Repositories:")
        yield TextArea("\n".join(self.config.config.github.ignored_repositories),
                       id="ignored_repos")

        yield Label("Local Settings", classes="section")

        yield Label("Active Working Directory:")
        yield Input(self.config.config.local.active_working_directory,
                    id="working_dir")

        yield Button("Save Settings", id="save_settings", variant="primary")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id != "save_settings":
            return

        updated_config = {
            "github": {
                "active-team-members":
                    self.query_one("#team_members", TextArea).text.splitlines(),
                "organisation":
                    self.query_one("#organisation", Input).value,
                "team":
                    self.query_one("#team", Input).value,
                "ignored-repositories":
                    self.query_one("#ignored_repos", TextArea).text.splitlines(),
            },
            "local": {
                "active-working-directory":
                    self.query_one("#working_dir", Input).value
            }
        }

        self.config.save(updated_config)
        if hasattr(self.app, "notify"):
            self.app.notify("Settings saved.", severity="information")
