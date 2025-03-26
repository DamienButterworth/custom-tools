import argparse
import csv

from tabulate import tabulate

from git_connector import get_pull_requests, get_team_repositories, get_team_members

parser = argparse.ArgumentParser(description='Fetch open pull requests from GitHub repositories.')
parser.add_argument('-fn', '--file-name', required=False, help='Output result to csv file with name')
parser.add_argument('-o', '--org', required=True, help='GitHub organization name')
parser.add_argument('-t', '--team', required=True, help='GitHub team slug')
parser.add_argument('-r', '--repo-overrides', nargs='*'),
parser.add_argument('-c', '--creator-filters', nargs='*',
                    help='List of GitHub usernames to filter by. Overrides dynamic team member fetch.')

args = parser.parse_args()


def list_open_pull_requests_terminal(repos, creator_filters=None):
    all_pull_requests = []

    for repo in repos:
        open_prs = get_pull_requests(repo, creator_filters)
        all_pull_requests.extend(open_prs)

    if all_pull_requests:
        #TODO: Figure out how to add headers correctly
        headers = ["Repository", "PR Title", "Created By", "Created At", "URL"]
        print("\nOpen Pull Requests:")
        print(tabulate(all_pull_requests, tablefmt="fancy_grid"))
    else:
        print("No open pull requests found for the provided repositories.")


def list_open_pull_requests_csv(repos, output_file, creator_filters=None):
    all_pull_requests = []

    for repo in repos:
        open_prs = get_pull_requests(repo, creator_filters)
        all_pull_requests.extend(open_prs)

    if not output_file.endswith('.csv'):
        output_file = output_file + '.csv'

    if all_pull_requests:
        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['repository', 'pr_title', 'created_by', 'created_at',
                                                      'url'])
            writer.writeheader()
            writer.writerows(all_pull_requests)

        print(f"Pull requests have been written to {output_file}")
    else:
        print("No open pull requests found for the provided repositories.")


org_name = args.org
team_slug = args.team

if args.repo_overrides:
    repositories = args.repo_overrides
else:
    repositories = get_team_repositories(org_name, team_slug)

if args.creator_filters:
    creator_filters = args.creator_filters
else:
    creator_filters = get_team_members(org_name, team_slug)

if args.file_name:
    list_open_pull_requests_csv(repositories, args.file_name, creator_filters)
else:
    list_open_pull_requests_terminal(repositories, creator_filters)
