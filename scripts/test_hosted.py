import os,secrets,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
os.chdir(root)
database=os.environ.get('DATABASE_URL') or (root/'.local/database-url').read_text().strip()
subprocess.run([str(root/'.venv/bin/python'),'manage.py','collectstatic','--noinput'],env=dict(os.environ,LANDER_BUILD='1',LANDER_HOSTED_PREVIEW='0',QC_USE_SQLITE='1'),check=True)
env=dict(os.environ,LANDER_HOSTED_PREVIEW='1',LANDER_DATA_DIR=str(root/'.local/hosted-check'),DJANGO_SECRET_KEY=secrets.token_urlsafe(64),DJANGO_ALLOWED_HOSTS='preview.test',DATABASE_URL=database)
env.pop('QC_USE_SQLITE',None)
for cmd in [('check','--deploy'),('test','qc.hosted_tests','--noinput','--verbosity','1')]:
 subprocess.run([str(root/'.venv/bin/python'),'manage.py',*cmd],env=env,check=True)
