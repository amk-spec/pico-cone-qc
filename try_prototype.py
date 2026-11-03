#!/usr/bin/env python3
"""Launch a local, synthetic-data-only prototype without installing PostgreSQL."""
import argparse
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import venv
import webbrowser

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description='Run the local Lander QC development prototype.')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--prepare-only', action='store_true', help='Install and prepare data without starting a server.')
    parser.add_argument('--no-install', action='store_true', help='Use existing installed dependencies (developer option).')
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        parser.error('Install Python 3.12 or newer, then run this launcher again.')
    if not 1024 <= args.port <= 65535:
        parser.error('Choose a port from 1024 to 65535.')
    os.chdir(ROOT)
    env_dir = ROOT / '.venv'
    python = env_dir / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.exists():
        print('Creating a private Python environment…', flush=True)
        venv.EnvBuilder(with_pip=True).create(env_dir)
    if not args.no_install:
        if subprocess.run([str(python), '-m', 'pip', '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
            subprocess.run([str(python), '-m', 'ensurepip', '--upgrade'], check=True)
        print('Installing the pinned application dependencies. Internet access is needed on the first run.', flush=True)
        subprocess.run([str(python), '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
    env = dict(os.environ, QC_USE_SQLITE='1')
    for command in [('migrate', '--noinput'), ('seed_demo',), ('check',)]:
        subprocess.run([str(python), 'manage.py', *command], env=env, check=True)
    accounts = ROOT / '.local/sqlite-review/demo-accounts.txt'
    print('\nLOCAL DEVELOPMENT PROTOTYPE — not production authorization.', flush=True)
    print('Your generated local login details:\n', flush=True)
    print(accounts.read_text(), flush=True)
    print(f'Credentials are also saved in: {accounts}', flush=True)
    if args.prepare_only:
        return
    url = f'http://127.0.0.1:{args.port}/login/'
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1', args.port)) == 0:
            parser.error(f'Port {args.port} is already in use. Try --port {args.port + 1}.')
    print(f'Opening {url}\nKeep this window open. Press Ctrl+C to stop the prototype.\n', flush=True)
    process = subprocess.Popen([str(python), 'manage.py', 'runserver', f'127.0.0.1:{args.port}', '--noreload', '--insecure'], env=env)
    def open_when_ready():
        for _ in range(100):
            if process.poll() is not None:
                return
            with socket.socket() as probe:
                if probe.connect_ex(('127.0.0.1', args.port)) == 0:
                    webbrowser.open(url)
                    return
            time.sleep(0.2)
    threading.Thread(target=open_when_ready, daemon=True).start()
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

if __name__ == '__main__':
    main()
