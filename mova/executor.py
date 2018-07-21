import subprocess

def run(cmd):
    print('foo')
    return subprocess.run(cmd, stderr=subprocess.PIPE, shell=False, check=True)

