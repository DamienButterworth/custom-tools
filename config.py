import git_connector as gc
import check_coverages as cc

import os
import json

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "theme": "dark",
    "default_team": "",
    "default_org": "",
    "default_creator_filters": ""
}


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_SETTINGS.copy()


def save_settings(navigator):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(navigator.settings, f, indent=4)


def build_sections(settings):
    default_team = settings.get("default_team", "Team")
    if default_team == "":
        default_team = "Team"
    default_org = settings.get("default_org", "Organisation")
    if default_org == "":
        default_org = "Organisation"
    creator_filters = settings.get("default_creator_filters", "All team")
    if creator_filters == "":
        creator_filters = "All team"

    sections = {
        "Github": [
            (f"{default_team} repos", gc.get_team_repositories),
            (f"{default_team} members", gc.get_team_members),
            (f"{default_org} team slugs", gc.get_teams),
            (f"{default_org} repository branches", gc.get_repository_branches),
            (f"{default_team} branches", gc.get_team_branches),
            (f"{creator_filters} pull requests", gc.list_open_pull_requests_team),
        ],
        "Scala": [
            ("Recursive coverage percentages", cc.execute)
        ],
        "Settings": []  # Can be populated dynamically if needed
    }

    return sections


# Usage
settings = load_settings()
SECTIONS = build_sections(settings)
