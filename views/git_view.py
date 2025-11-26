# views/git_view.py

import asyncio
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Vertical
from textual.widgets import Button
from interface.JsonTreeViewer import JsonTreeViewer  # <-- you must have this installed

from models.github_config import GithubConfig
from github import GitHubTeamRequests


class GithubView(VerticalScroll):
    def __init__(self, config: GithubConfig):
        super().__init__()
        self.content = None
        self.teams_button = None
        self.members_button = None
        self.team_repositories_button = None
        self.git_config = config
        self.gtr = GitHubTeamRequests(config.organisation, config.team)

    def compose(self) -> ComposeResult:
        self.teams_button = Button("Organisation Teams", id="org_teams", variant="primary")
        self.members_button = Button("Team Members", id="team_members", variant="primary")
        self.team_repositories_button = Button("Team Repositories", id="team_repos", variant="primary")
        self.content = Vertical()
        yield self.teams_button
        yield self.members_button
        yield self.team_repositories_button
        yield self.content


    async def run_with_prep_async(self, func, message):
        self.teams_button.display = False
        self.members_button.display = False
        self.team_repositories_button.display = False
        self.content.remove_children()
        from textual.widgets import Label
        loading = Label(message)
        self.content.mount(loading)
        result = await asyncio.to_thread(func)
        await loading.remove()
        return result


    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button is self.teams_button:
            result = await self.run_with_prep_async(
                self.gtr.list_teams,
                f"Fetching teams for organisation {self.git_config.organisation}..."
            )
            viewer = JsonTreeViewer(result.data, title="Organisation Teams", label_key="name")
            self.content.mount(viewer)
            return

        if event.button is self.members_button:
            result = await self.run_with_prep_async(
                self.gtr.get_team_members,
                f"Fetching team members for team {self.git_config.team}..."
            )
            viewer = JsonTreeViewer(result.data, title="Team Members", label_key="login")
            self.content.mount(viewer)
            return

        if event.button is self.team_repositories_button:
            result = await self.run_with_prep_async(
                self.gtr.get_team_repos,
                f"Fetching repositories for team {self.git_config.team}..."
            )
            viewer = JsonTreeViewer(result.data, title="Team Repos", label_key="name")
            self.content.mount(viewer)
            return
