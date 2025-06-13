import os
import re


def extract_scoverage_settings(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        value_match = re.search(r"ScoverageKeys\.coverageMinimumStmtTotal\s*:=\s*([\d.]+)", content)
        fail_match = re.search(r"ScoverageKeys\.coverageFailOnMinimum\s*:=\s*true", content)

        value = float(value_match.group(1)) if value_match else None
        fail = bool(fail_match)

        return value, fail
    except (UnicodeDecodeError, FileNotFoundError):
        return None, False


def scan_project_dir(project_dir):
    for dirpath, _, filenames in os.walk(project_dir):
        for filename in filenames:
            if filename.endswith(".scala") or filename.endswith(".sbt"):
                file_path = os.path.join(dirpath, filename)
                value, fail = extract_scoverage_settings(file_path)
                if value is not None and fail:
                    return value  # Found what we need
    return None  # Not found or missing condition


def scan_root_dir(root_dir):
    passing = {}
    failing = []

    for item in os.listdir(root_dir):
        subdir_path = os.path.join(root_dir, item)
        if os.path.isdir(subdir_path):
            value = scan_project_dir(subdir_path)
            if value is not None:
                passing[subdir_path] = value
            else:
                failing.append(subdir_path)

    return passing, failing


def execute(root_directory):
    passing, failing = scan_root_dir(root_directory)

    print("\n✅ Projects with coverage enforcement:")
    for dir_path, value in sorted(passing.items()):
        print(f"{dir_path}: {value}")

    print("\n❌ Projects missing coverage enforcement:")
    for dir_path in sorted(failing):
        print(dir_path)
