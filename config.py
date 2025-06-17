import git_connector as gc
import check_coverages as cc

import os
import json

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "default_team": "",
    "default_org": ""
}

SECTIONS = {
    "GitHub": [
        ("Team repos", gc.get_team_repositories),
        ("Team members", gc.get_team_members),
        ("Team slugs", gc.get_teams),
        ("Repository branches", gc.get_repository_branches),
        ("Team branches", gc.get_team_branches),
        ("Pull requests", gc.list_open_pull_requests_team),
    ],
    "Scala": [
        ("Recursive coverage percentages", cc.execute)
    ],
    "Settings": []
}


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_SETTINGS.copy()


def save_settings(navigator):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(navigator.settings, f, indent=4)
