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


def get_pull_requests(repo, creator_filters=None):
    url = f"{base_url}/repos/{repo}/pulls"
    all_data = __handle_pagination(url)
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
    all_data = __handle_pagination(url)
    usernames = [member['login'] for page in all_data for member in page]
    return usernames


def get_team_repositories(org, team_slug):
    url = f'{base_url}/orgs/{org}/teams/{team_slug}/repos'
    print(f'Fetching repositories for team: {team_slug} in {org}')
    all_data = __handle_pagination(url)

    repo_info = []
    for page in all_data:
        for repo in page:
            name = repo['full_name']
            archived = "📦 Archived" if repo.get('archived') else "✅ Active"
            privacy = "🔒 Private" if repo.get('private') else "🌍 Public"
            fork = "🍴 Fork" if repo.get('fork') else "📘 Original"
            info = f"{name} — {archived} | {privacy} | {fork}"
            repo_info.append(info)

    return repo_info


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


def get_team_slugs(org):
    url = f'{base_url}/orgs/{org}/teams'
    print(f'Fetching team slugs for organization: {org}')
    all_data = __handle_pagination(url)
    slugs = [team['slug'] for page in all_data for team in page]
    return slugs


def get_repository_branches(repo, org=None):
    full_repo = f"{org}/{repo}" if org else repo
    branches_url = f'{base_url}/repos/{full_repo}/branches'
    print(f'Fetching branches for repository: {full_repo}')
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
