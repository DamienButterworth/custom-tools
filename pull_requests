import requests
import csv
import os
import subprocess
import argparse


def get_open_pull_requests(repo, token, creator_filters=None):
    url = f'https://api.github.com/repos/{repo}/pulls'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Handle pagination for pull requests
    all_pull_requests = []
    page = 1
    while True:
        response = requests.get(url, headers=headers, params={'page': page, 'per_page': 100})
        if response.status_code == 200:
            pull_requests = response.json()
            if not pull_requests:
                break  # No more pull requests, exit the loop
            for pr in pull_requests:
                if creator_filters and pr['user']['login'] not in creator_filters:
                    continue
                pr_data = {
                    'repository': repo,
                    'pr_number': pr['number'],
                    'pr_title': pr['title'],
                    'created_by': pr['user']['login'],
                    'created_at': pr['created_at'],
                    'url': pr['html_url']
                }
                all_pull_requests.append(pr_data)
            page += 1
        else:
            print(f"Failed to fetch pull requests for {repo}: {response.status_code}, {response.content}")
            break
    return all_pull_requests


def get_team_repositories(org, team_slug, token):
    url = f'https://api.github.com/orgs/{org}/teams/{team_slug}/repos'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    all_repositories = []
    page = 1
    while True:
        response = requests.get(url, headers=headers, params={'page': page, 'per_page': 100})
        if response.status_code == 200:
            repositories = response.json()
            if not repositories:
                break  # No more repositories, exit the loop
            for repo in repositories:
                all_repositories.append(repo['full_name'])  # Getting full repository names (e.g., 'org/repo')
            page += 1
        else:
            print(f"Failed to fetch repositories for team {team_slug}: {response.status_code}, {response.content}")
            break
    return all_repositories


def get_team_members(org, team_slug, token):
    url = f'https://api.github.com/orgs/{org}/teams/{team_slug}/members'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    all_members = []
    page = 1
    while True:
        response = requests.get(url, headers=headers, params={'page': page, 'per_page': 100})
        if response.status_code == 200:
            members = response.json()
            if not members:
                break  # No more members, exit the loop
            for member in members:
                all_members.append(member['login'])  # Adding the username to the list
            page += 1
        else:
            print(f"Failed to fetch members for team {team_slug}: {response.status_code}, {response.content}")
            break
    return all_members


def list_open_pull_requests(repos, token, output_file, creator_filters=None):
    all_pull_requests = []

    for repo in repos:
        open_prs = get_open_pull_requests(repo, token, creator_filters)
        all_pull_requests.extend(open_prs)

    if all_pull_requests:
        # Write the list of pull requests to a CSV file
        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['repository', 'pr_number', 'pr_title', 'created_by', 'created_at',
                                                      'url'])
            writer.writeheader()
            writer.writerows(all_pull_requests)

        print(f"Pull requests have been written to {output_file}")

        # Open the CSV file with the default application
        subprocess.run(['open', output_file])
        print(f"Opened {output_file} with the default application.")

    else:
        print("No open pull requests found for the provided repositories.")


github_token = os.getenv('GITHUB_TOKEN')

if not github_token:
    print("Error: GitHub token not found. Please set the GITHUB_TOKEN environment variable.")
    exit(1)

parser = argparse.ArgumentParser(description='Fetch open pull requests from GitHub repositories.')
parser.add_argument('-o', '--org', required=True, help='GitHub organization name')
parser.add_argument('-t', '--team', required=True, help='GitHub team slug')
parser.add_argument('-fn', '--file-name', default='open_pull_requests.csv', help='Output CSV file name')
parser.add_argument('-cf', '--creator-filters', nargs='*',
                    help='List of GitHub usernames to filter by. Overrides dynamic team member fetch.')

args = parser.parse_args()

org_name = args.org
team_slug = args.team

repositories = get_team_repositories(org_name, team_slug, github_token)

if args.creator_filters:
    creator_filters = args.creator_filters
else:
    creator_filters = get_team_members(org_name, team_slug, github_token)

output_csv_file = args.file_name
list_open_pull_requests(repositories, github_token, output_csv_file, creator_filters)
