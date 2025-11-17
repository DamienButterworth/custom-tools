from textual.containers import Container
from textual.widgets import (
    Button,
    Static,
    Select,
)


class Sidebar(Container):
    def compose(self):
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