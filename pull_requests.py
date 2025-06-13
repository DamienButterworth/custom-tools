from git_connector import get_pull_requests, get_team_repositories


def list_open_pull_requests_terminal(repos, creator_filters=None):
    all_pull_requests = []

    for repo in repos:
        open_prs = get_pull_requests(repo, creator_filters)
        all_pull_requests.extend(open_prs)

    return all_pull_requests


def list_open_pull_requests_team(org, team_slug, creator_filters=None):
    repos = get_team_repositories(org, team_slug)
    all_pull_requests = []

    for repo in repos:
        open_prs = get_pull_requests(repo, creator_filters)
        all_pull_requests.extend(open_prs)

    return all_pull_requests
