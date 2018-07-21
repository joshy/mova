import subprocess
from subprocess import PIPE


def run(cmd):
    completed = subprocess.run(cmd, stderr=subprocess.STDOUT, shell=False, check=True)

    return completed.returncode, completed.stdout

