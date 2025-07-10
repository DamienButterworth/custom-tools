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


from concurrent.futures import ThreadPoolExecutor, as_completed


def get_team_branches(org, team):
    team_repos = get_team_repositories(org, team)

    def fetch_branches(repo):
        branches = get_repository_branches(repo['full_name'], None)
        print(branches)
        return [
            {
                'name': branch['name'],
                'url': branch['url']
            }
            for branch in branches
        ]

    response = []
    with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust workers as needed
        future_to_repo = {executor.submit(fetch_branches, repo): repo for repo in team_repos}
        for future in as_completed(future_to_repo):
            try:
                response.extend(future.result())
            except Exception as e:
                print(f"Error fetching branches for repo {future_to_repo[future]['full_name']}: {e}")

    return response


def get_repository_branches(repo, org=None):
    full_repo = f"{org}/{repo}" if org else repo
    branches_url = f'{base_url}/repos/{full_repo}/branches'
    all_data = __handle_pagination(branches_url)
    branches = []
    for page in all_data:
        for branch in page:
            branch_name = branch['name']
            if org:
                url = f"https://github.com/{org}/{repo}/tree/{branch_name}"
            else:
                url = f"https://github.com/{repo}/tree/{branch_name}"
            branches.append({
                'name': branch_name,
                'url': url
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
