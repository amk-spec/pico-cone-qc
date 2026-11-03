from pathlib import Path
from playwright.sync_api import sync_playwright
import json
root=Path(__file__).resolve().parents[1]
credentials={line.split('\t')[0]:line.split('\t')[1] for line in (root/'.local/demo-accounts.txt').read_text().splitlines() if '\t' in line}
artifacts=root/'.local/screenshots';artifacts.mkdir(exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
 page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
 errors=[]
 page.on('pageerror',lambda error:errors.append(str(error)))
 response=page.goto('http://127.0.0.1:8000/login/')
 assert response.status==200
 page.fill('[name=username]','owner');page.fill('[name=password]',credentials['owner'])
 page.get_by_role('button',name='Sign in').click();page.wait_for_url('http://127.0.0.1:8000/')
 page.get_by_text('Quality, connected.').wait_for()
 assert page.locator('.metric').count()==4
 assert page.locator('nav a').count()==13
 page.screenshot(path=str(artifacts/'overview.png'),full_page=True)
 for route in ['jobs','coupons','records','issues','qualifications','resources','decisions','impacts','authority','sources']:
  response=page.goto(f'http://127.0.0.1:8000/{route}/')
  assert response.status==200,(route,response.status)
  assert page.locator('h1').count()==1
 # Exercise a real create POST with CSRF and an actual controller/database round trip.
 page.goto('http://127.0.0.1:8000/jobs/new/')
 if not (root/'.local/browser-job-created').exists():
  page.fill('[name=number]','DEMO-BROWSER-01');page.fill('[name=title]','Browser-created demonstration work order')
  page.get_by_role('button',name='Save prototype record').click()
  page.wait_for_url('**/jobs/*/')
  assert 'Browser-created' in page.locator('h1').inner_text()
  (root/'.local/browser-job-created').write_text('Synthetic browser test record only.')
 # Verify unresolved criteria are visibly denied even to the owner.
 page.goto('http://127.0.0.1:8000/records/')
 page.locator('a.strong-link',has_text='DEMO-WPS-001').click()
 form=page.locator('form').filter(has=page.get_by_role('button',name='Approve prototype evidence'))
 form.locator('[name=capacity]').select_option('owner')
 form.locator('[name=reason]').fill('Browser check: unresolved criteria must remain blocked.')
 form.get_by_role('button',name='Approve prototype evidence').click()
 page.get_by_text('Unresolved / TBD requirements cannot be approved',exact=False).wait_for()
 page.screenshot(path=str(artifacts/'controlled-record.png'),full_page=True)
 # Mobile navigation and content must remain usable without page-level overflow.
 mobile=browser.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
 mobile.goto('http://127.0.0.1:8000/login/')
 mobile.fill('[name=username]','cone');mobile.fill('[name=password]',credentials['cone'])
 mobile.get_by_role('button',name='Sign in').click();mobile.wait_for_url('http://127.0.0.1:8000/')
 mobile.screenshot(path=str(artifacts/'overview-mobile.png'),full_page=True)
 assert mobile.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'), 'Page overflow on mobile'
 assert not errors,errors
 print(json.dumps({'desktop_routes':10,'create_form':'passed','TBD_approval_denied':'passed','mobile_overflow':'passed','browser_errors':errors,'screenshots':str(artifacts)}))
 browser.close()
