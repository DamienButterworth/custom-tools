from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Button

from Sidebar import Sidebar
from config import YAMLConfig
from github import GitHubTeamRequests
from views.git_view import GithubView
from views.home_view import HomeView
from views.settings_view import SettingsView


class MyApp(App):

    CSS_PATH = "styles.css"

    def __init__(self, config: YAMLConfig):
        super().__init__()
        self.config = config
        self.gtr = GitHubTeamRequests(
            config.config.github.organisation,
            config.config.github.team,
        )

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Sidebar(id="sidebar"),
            Container(id="content"),
            id="main-row",
        )

        yield Footer()

    async def on_mount(self) -> None:
        content = self.query_one("#content", Container)
        await content.mount(HomeView())

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id not in ("home", "github", "settings"):
            return

        content = self.query_one("#content", Container)
        await content.remove_children()

        if event.button.id == "home":
            await content.mount(HomeView())

        elif event.button.id == "github":
            await content.mount(GithubView(config.config.github))

        elif event.button.id == "settings":
            await content.mount(SettingsView(self.config))


if __name__ == "__main__":
    config = YAMLConfig("config.yaml")
    MyApp(config).run()
