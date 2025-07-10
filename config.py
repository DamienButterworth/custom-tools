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
    default_team_name = settings.get("default_team", "")
    if default_team_name:
        default_team_name = f"({default_team_name})"
    default_org_name = settings.get("default_org", "")
    if default_org_name:
        default_org_name = f"({default_org_name})"
    creator_filters_name = settings.get("default_creator_filters", "")
    if creator_filters_name:
        creator_filters_name = f"({creator_filters_name})"

    sections = {
        "Github": [
            (f"Team repos {default_team_name}", gc.get_team_repositories),
            (f"Team members {default_team_name}", gc.get_team_members),
            (f"Organisation team slugs {default_org_name}", gc.get_teams),
            (f"Organisation repository branches {default_org_name}", gc.get_repository_branches),
            (f"Team branches {default_team_name}", gc.get_team_branches),
            (f"Team pull requests {creator_filters_name}", gc.list_open_pull_requests_team),
        ],
        "Scala": [
            ("Recursive coverage percentage=s", cc.execute)
        ],
        "Settings": []  # Can be populated dynamically if needed
    }

    return sections


# Usage
settings = load_settings()
SECTIONS = build_sections(settings)
