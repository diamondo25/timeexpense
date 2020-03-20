#!/usr/bin/env python3
from bs4 import BeautifulSoup
import requests
from datetime import date, timedelta
from urllib.parse import urlsplit, urlunsplit, parse_qsl
from dotenv import load_dotenv
import os
load_dotenv()


USERNAME = os.getenv('FD_USERNAME')
PASSWORD = os.getenv('FD_PASSWORD')
MEDIUMID = os.getenv('FD_MEDIUMID')
TRACELEVEL = os.getenv('FD_TRACELEVEL')
if TRACELEVEL is None:
	TRACELEVEL = 0
else:
	TRACELEVEL = int(TRACELEVEL)

"""
Open https://www.ov-chipkaart.nl/mijn-ov-chip.htm
End up at login.ovchipkaart.nl
Copy sessionDataKey element

POST https://login.ov-chipkaart.nl/commonauth
username=
password=
chkRemember=off
sessionDataKey=-


// Medium ID = hashed card ID?

Fetch data
GET https://www.ov-chipkaart.nl/mijn-ov-chip/mijn-ov-reishistorie.htm

mediumid=$MEDIUMID
begindate=01-01-2020
enddate=29-01-2020
type=




GET https://www.ov-chipkaart.nl/mijn-ov-chip/mijn-ov-reishistorie/ov-reishistorie-declaratie.htm
begindate=01-01-2020
enddate=29-01-2020
type=
mediumid: $MEDIUMID


Submit .export-transactions-form 
"""

s = requests.Session()
def fetch_page(method, url, query, data = None, just_return = False):
	def fix_url(u):
		# First slash
		if u[0] == '/':
			u = url[:url.find('/', 8)] + u
		elif u[0] == '.':
			# Full path, not last last
			tmp = url[:url.rfind('/')+1]
			while '../' in u:
				u = u[3:]
				if tmp.find('/') > 8:
					tmp = tmp[:tmp.rfind('/')+1]

			u = tmp + u
		return u

	if method == 'POST':
		m = s.post
	elif method == 'GET':
		m = s.get
	else:
		raise ValueError('Unspupported method: ' + method)

	up = urlsplit(url)

	if up.query != '':
		qsl = parse_qsl(up.query)
		if query is None:
			query = {}
		for k, v in qsl:
			query[k] = v

		url = urlunsplit([
			up[0], up[1], up[2], '', up[4]
		])


	if TRACELEVEL > 1:
		print('DBG: Loading %s %s' % (method, url))
		print('DBG: ', query)
		print('DBG: ', data)

	x = m(url, data=data, params=query)
	if TRACELEVEL > 0:
		print('DBG: ', x.url)

	if just_return:
		return x

	x = x.text

	soup = BeautifulSoup(x, 'html.parser')
	#print(soup)

	# Process meta tag redirect...

	meta_tags = soup.find_all('meta')
	for mt in meta_tags:
		if not mt.has_attr('http-equiv') or not mt.has_attr('content'):
			continue

		if mt['http-equiv'] != 'refresh':
			continue

		content = mt['content']
		if content.find('url=') > 0:
			new_url = fix_url(content[content.find('url=')+4:])

			return fetch_page('GET', new_url, None, None)

	# Process SAML login screen

	if 'document.forms[0].submit()' in x:
		f = soup.find('form')
		new_url = f['action']
		method = 'POST'
		inputs = f.find_all('input')
		post_data = {}
		for i in inputs:
			if i.has_attr('name') and i.has_attr('value'):
				post_data[i['name']] = i['value']

		return fetch_page(method, fix_url(new_url), None, post_data)

	if 'Log in met je gebruikersnaam' in x:
		f = soup.find('form')
		new_url = f['action']
		method = 'POST'
		inputs = f.find_all('input')
		post_data = {}
		for i in inputs:
			if i.has_attr('name'):
				n = i['name']
				v = ''
				if n == 'username': 
					v = USERNAME
				elif n == 'password': 
					v = PASSWORD
				elif i.has_attr('value'):
					v = i['value']
				post_data[n] = v

		return fetch_page(method, fix_url(new_url), None, post_data)


	return soup


def fetch_transactions(year, month, formats = ['PDF', 'CSV']):
	## TODO figure out the stuff with datetime for last day of month and cur day
	# export-transactions-form

	fromd = date(year, month, 1)
	if month == 12:
		month = 0
		year += 1
	tod = date(year, month+1, 1) - (timedelta(days=1))

	page = fetch_page('GET', 'https://www.ov-chipkaart.nl/mijn-ov-chip/mijn-ov-reishistorie/ov-reishistorie-declaratie.htm', {
		'begindate': fromd.strftime('%d-%m-%Y'),
		'enddate': tod.strftime('%d-%m-%Y'),
		'type': '',
		'mediumid': MEDIUMID,
	})

	dlform = page.find(class_='export-transactions-form')

	if dlform is None:
		# No transactions?
		return {}

	inputs = dlform.find_all('input')
	post_data = {}
	for i in inputs:
		if i.has_attr('name'):
			n = i['name']
			v = ''
			if i.has_attr('value'):
				v = i['value']
			post_data[n] = v


	rets = {}
	for fmt in formats:

		post_data['documentFormat'] = fmt

		c = fetch_page('POST', 'https://www.ov-chipkaart.nl/web/document', None, post_data, just_return=True)

		fname = c.headers['Content-Disposition']
		fname = fname[fname.index('=')+1:]


		rets[fmt] = {
			'filename': fname,
			'reader': c,
		}

	return rets

def download_transactions(year, month):
	txs = fetch_transactions(year, month)
	for fmt, data in txs.items():

		original_filename = data['filename']
		# Make more sane filenames
		filename = '%d-%d' % (year, month)
		if '.pdf' in original_filename:
			filename = 'declaratieoverzicht_' + filename + '.pdf'
		else:
			filename = 'transacties_' + filename + '.csv'


		print('Saving %s ' % filename)
		with open('input/' + filename, 'wb') as fd:
		    for chunk in data['reader'].iter_content(chunk_size=128):
		        fd.write(chunk)


for i in range(0, 12):
	m = i+1
	download_transactions(2018, m)
	download_transactions(2019, m)


#download_transactions(2019, 10)
#download_transactions(2019, 11)
#download_transactions(2019, 12)
download_transactions(2020, 1)
download_transactions(2020, 2)