import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

base_url = "https://api.github.com"

token = os.getenv('GITHUB_TOKEN')

if not token:
    print("Error: GitHub token not found. Please set the GITHUB_TOKEN environment variable.")
    exit(1)

headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json'
}

session = requests.Session()


def list_open_pull_requests_team(org, team, creator_filters=None):
    team_repos = get_team_repositories(org, team)
    repos = []
    for team in team_repos:
        repos.append(team['full_name'])

    all_pull_requests = []

    for repo in repos:
        open_prs = get_pull_requests(repo, creator_filters)
        all_pull_requests.extend(open_prs)

    return all_pull_requests


def get_pull_requests(repo, creator_filters=None):
    url = f"{base_url}/repos/{repo}/pulls"
    all_data = __handle_pagination(url)

    # Prepare a filtered response
    response = [
        {
            'url': pr['url'],
            'user': pr['user']['login']
        }
        for page in all_data
        for pr in page
        if creator_filters is None or pr['user']['login'] in creator_filters
    ]

    return response



def get_team_members(org, team):
    url = f'{base_url}/orgs/{org}/teams/{team}/members'
    all_data = __handle_pagination(url)
    response = [
        {
            'user': user['login']
        }
        for page in all_data
        for user in page
    ]
    return response


def get_team_repositories(org, team):
    url = f'{base_url}/orgs/{org}/teams/{team}/repos'
    all_data = __handle_pagination(url)
    response = [
        {
            "full_name": repo['full_name']
        }
        for page in all_data
        for repo in page
    ]
    return response


def get_teams(org):
    url = f'{base_url}/orgs/{org}/teams'
    all_data = __handle_pagination(url)
    response = [
        {
            "slug": team['slug']
        }
        for page in all_data
        for team in page
    ]
    return response


def get_team_branches(org, team):
    team_repos = get_team_repositories(org, team)
    paginated_branches = []
    for repo in team_repos:
        branches = get_repository_branches(repo, None)
        paginated_branches.append(branches)

    response = [
        {
            'name': branch['name'],
            'latest_commit': branch['latest_commit']
        }
        for branches in paginated_branches
        for branch in branches
    ]
    return response


def get_repository_branches(repo, org=None):
    full_repo = f"{org}/{repo}" if org else repo
    branches_url = f'{base_url}/repos/{full_repo}/branches'
    all_data = __handle_pagination(branches_url)

    branches = []
    for page in all_data:
        for branch in page:
            branch_name = branch['name']
            commit_url = branch['commit']['url']
            try:
                commit_response = session.get(commit_url, headers=headers)
                commit_response.raise_for_status()
                commit_data = commit_response.json()
                latest_commit = commit_data['commit']['committer'].get('date')
            except requests.exceptions.RequestException as e:
                print(f"Error fetching commit data for branch {branch_name}: {e}")
                latest_commit = None

            branches.append({
                'name': branch_name,
                'latest_commit': latest_commit
            })
    return branches


def __handle_pagination(url):
    all_data = []
    page = 1
    while True:
        try:
            response = session.get(url, headers=headers, params={'page': page, 'per_page': 100})
            response.raise_for_status()
            data = response.json()
            if not data:
                break
            all_data.append(data)
            page += 1
        except requests.exceptions.RequestException as e:
            print(f'Error occurred: {e}')
            break
    return all_data
