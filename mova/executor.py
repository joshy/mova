import subprocess

def run(cmd):
    return subprocess.run(cmd, stderr=subprocess.PIPE, shell=False, check=True)

