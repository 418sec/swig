import os, subprocess


def check_file_exists(path):
    """
    Checks if a file exists or not.
    """
    return os.path.isfile(path)


def check_dir_exists(path):
    """
    Checks if a folder exists or not.
    """
    return os.path.isdir(path)


def run_command(*args, **kwargs):
    """
    Runs an os command using subprocess module.
    """
    return subprocess.call(args, **kwargs)