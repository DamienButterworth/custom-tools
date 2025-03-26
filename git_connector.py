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

def handle_pagination(url):
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


def get_pull_requests(repo, creator_filters=None):
    print(f'Fetching pull requests for: {repo}')
    url = f"{base_url}/repos/{repo}/pulls"
    all_data = handle_pagination(url)
    return [
        {
            'repository': repo,
            'pr_title': pr['title'],
            'created_by': pr['user']['login'],
            'created_at': pr['created_at'],
            'url': pr['html_url']
        }
        for page in all_data
        for pr in page
        if not creator_filters or pr['user']['login'] in creator_filters
    ]


def get_team_members(org, team_slug):
    url = f'{base_url}/orgs/{org}/teams/{team_slug}/members'
    print(f'Fetching team members from {team_slug} in {org}')
    all_data = handle_pagination(url)
    return [member['login'] for page in all_data for member in page]


def get_team_repositories(org, team_slug):
    url = f'{base_url}/orgs/{org}/teams/{team_slug}/repos'
    print(f'Fetching repositories for team: {team_slug} in {org}')
    all_data = handle_pagination(url)
    return [repo['full_name'] for page in all_data for repo in page]


def fetch_pull_requests_for_repos(repos, creator_filters=None):
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(get_pull_requests, repo, creator_filters) for repo in repos]
        results = []
        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as e:
                print(f'Error occurred while fetching PRs: {e}')
        return results


def fetch_repositories_for_teams(org, team_slugs):
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(get_team_repositories, org, team_slug) for team_slug in team_slugs]
        all_repositories = []
        for future in as_completed(futures):
            try:
                all_repositories.extend(future.result())
            except Exception as e:
                print(f'Error occurred while fetching repositories: {e}')
        return all_repositories