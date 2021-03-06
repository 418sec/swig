#!/usr/bin/env python

import sys
import os
import subprocess

def failed():
    print("mkdist.py failed to complete")
    sys.exit(2)

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

import argparse
parser = argparse.ArgumentParser(description="Build a SWIG distribution tarball swig-x.y.z.tar.gz")
parser.add_argument("version", help="version string in format x.y.z")
parser.add_argument("-b", "--branch", required=False, default="master", help="git branch name to create tarball from [master]")
parser.add_argument("-f", "--force-tag", required=False, action="store_true", help="force tag (replace git tag if it already exists)")
parser.add_argument("-s", "--skip-checks", required=False, action="store_true", help="skip checks (that local and remote repos are in sync)")
args = parser.parse_args()

version = args.version
branch = args.branch
dirname = "swig-" + version
force_tag = args.force_tag
skip_checks = args.skip_checks

# Tools directory path $ENV/swig/Tools
toolsdir = os.path.dirname(os.path.abspath(__file__))
# Root directory path (swig) $ENV/swig
rootdir = os.path.abspath(os.path.join(toolsdir, os.pardir))
# version directory path $ENV/swig/<x.x.x>
dirpath = os.path.join(rootdir, dirname)

if sys.version_info[0:2] < (2, 7):
     print("Error: Python 2.7 or higher is required")
     sys.exit(3)

# Check name matches normal unix conventions
if dirname.lower() != dirname:
    print("directory name (" + dirname + ") should be in lowercase")
    sys.exit(3)

# If directory and tarball exist, remove it
print("Removing " + dirname)
if check_dir_exists(dirpath):
    run_command("rm", "-rf", dirpath)

print("Removing " + dirname + ".tar if exists")
filename = dirpath + ".tar"
if check_file_exists(filename):
    run_command("rm", "-rf", filename)

print("Removing " + dirname + ".tar.gz if exists")
filename += ".gz"
if check_file_exists(filename):
    run_command("rm", "-rf", filename)

# Grab the code from git

print("Checking there are no local changes in git repo")
run_command("git", "remote", "update", "origin") == 0 or failed()
command = ["git", "status", "--porcelain", "-uno"]
out = subprocess.check_output(command)
if out.strip():
    print("Local git repository has modifications")
    print(" ".join(command))
    print(out)
    sys.exit(3)

if not skip_checks:
    print("Checking git repository is in sync with remote repository")
    command = ["git", "log", "--oneline", branch + "..origin/" + branch]
    out = subprocess.check_output(command)
    if out.strip():
        print("Remote repository has additional modifications to local repository")
        print(" ".join(command))
        print(out)
        sys.exit(3)

    command = ["git", "log", "--oneline", "origin/" + branch + ".." + branch]
    out = subprocess.check_output(command)
    if out.strip():
        print("Local repository has modifications not pushed to the remote repository")
        print("These should be pushed and checked that they pass Continuous Integration testing before continuing")
        print(" ".join(command))
        print(out)
        sys.exit(3)

print("Tagging release")
tag = "v" + version
force = "-f " if force_tag else ""
command = ["git", "tag", "-a", "-m", "'Release version " + version + "'"]
force and command.extend(force, tag)
not force and command.append(tag)
run_command(*command) == 0 or failed()

outdir = dirname + "/"
print("Grabbing tagged release git repository using 'git archive' into " + outdir)

# using pipe operator without shell=True; split commands into individual ones.
# git archive command
command = ["git", "archive", "--prefix=" + outdir, tag, "."]
archive_ps = subprocess.Popen(command, cwd=rootdir, stdout=subprocess.PIPE)
# tar -xf -
tar_ps = subprocess.Popen(("tar", "-xf", "-"), stdin=archive_ps.stdout, stdout=subprocess.PIPE)
archive_ps.stdout.close()  # Allow archive_ps to receive a SIGPIPE if tar_ps exits.
output = tar_ps.communicate()

# Go build the system

print("Building system")
run_command("./autogen.sh", cwd=dirpath) == 0 or failed()

cmdpath = os.path.join(dirpath, "Source", "CParse")
run_command("bison", "-y", "-d", "parser.y", cwd=cmdpath) == 0 or failed()
run_command("mv", "y.tab.c", "parser.c", cwd=cmdpath) == 0 or failed()
run_command("mv", "y.tab.h", "parser.h", cwd=cmdpath) == 0 or failed()

run_command("make", "-f", "Makefile.in", "libfiles", "srcdir=./", cwd=dirpath) == 0 or failed()

# Remove autoconf files
run_command("find", dirname, "-name", "autom4te.cache", "-exec", "rm", "-rf", "{}", ";", cwd=rootdir)

# Build documentation
print("Building html documentation")
docpath = os.path.join(dirpath, "Doc", "Manual")
run_command("make", "all", "clean-baks", cwd=docpath) == 0 or failed()

# Build the tar-ball
run_command("tar", "-cf", dirname + ".tar", dirname, stdout=open(dirname + ".tar", "w")) == 0 or failed()
run_command("gzip", dirname + ".tar", stdout=open(dirname + ".tar.gz", "w")) == 0 or failed()

print("Finished building " + dirname + ".tar.gz")

