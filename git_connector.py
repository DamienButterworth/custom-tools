import requests
import os

base_url = "https://api.github.com"

token = os.getenv('GITHUB_TOKEN')

session = requests.session()

if not token:
    print("Error: GitHub token not found. Please set the GITHUB_TOKEN environment variable.")
    exit(1)

headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json'
}


def handle_pagination(url):
    all_data = []
    page = 1
    while True:
        response = session.get(url, headers=headers, params={'page': page, 'per_page': 100})
        if response.status_code == 200:
            data = response.json()
            if not data:
                break
            all_data.append(data)
            page += 1
        else:
            print(f'Failed to perform paginated request')
            break
    return all_data


def get_pull_requests(repo, creator_filters=None):
    url = f"{base_url}/repos/{repo}/pulls"
    print(f'Fetching pull requests from: {repo}')
    all_data = handle_pagination(url)
    all_data_flat = [repo for page in all_data for repo in page]
    all_pull_requests = []
    for pr in all_data_flat:
        if creator_filters and pr['user']['login'] not in creator_filters:
            continue
        pr_data = {
            'repository': repo,
            'pr_title': pr['title'],
            'created_by': pr['user']['login'],
            'created_at': pr['created_at'],
            'url': pr['html_url']
        }
        all_pull_requests.append(pr_data)
    return all_pull_requests


def get_team_members(org, team_slug):
    url = f'{base_url}/orgs/{org}/teams/{team_slug}/members'
    print(f'Fetching team members from {team_slug} in {org}')
    all_members = []
    all_data = handle_pagination(url)
    all_data_flat = [repo for page in all_data for repo in page]
    for member in all_data_flat:
        all_members.append(member['login'])
    return all_members


def get_team_repositories(org, team_slug):
    url = f'{base_url}/orgs/{org}/teams/{team_slug}/repos'
    print(f'Fetching repositories for team: {team_slug} in {org}')
    all_repositories = []
    all_data = handle_pagination(url)
    all_data_flat = [repo for page in all_data for repo in page]
    for repo in all_data_flat:
        all_repositories.append(repo['full_name'])
    print(f'Found {len(all_repositories)} repositories')
    return all_repositories
