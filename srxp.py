#!/usr/bin/env python3
from bs4 import BeautifulSoup
import requests
from datetime import date, timedelta
from urllib.parse import urlsplit, urlunsplit, parse_qsl
from dotenv import load_dotenv
import os
import sys, json
load_dotenv()


ACCOUNT = os.getenv('SRXP_ACCOUNT')
CUSTOMER = os.getenv('SRXP_CUSTOMER')
TOKEN = os.getenv('SRXP_TOKEN')

# /api/1/accounts/136831/expenses?exchange_rates=1
# {"distance":{"unit":"km","amount":600},"waypoints":[{"location":""},{"location":""}],"currency_id":1,"expense_date":"2019-10-28T00:00:00+00:00","description":"Delft <> Huizen, 6 trips between 2019-10-28 and 2019-10-30","amounts":[{"category_id":94859}],"type":"mileage","tags":[]}



s = requests.Session()
s.headers.update({'Authorization': TOKEN})

baseurl = 'https://portal.srxp.com/api/1'
baseurl_account = baseurl + '/accounts/' + ACCOUNT
baseurl_customer = baseurl + '/customers/' + CUSTOMER

datastore = {}

def get(url):
	print(url)
	return s.get(url)

def post(url, json):
	print(url)
	print(json)
	return s.post(url, json=json)


def load_data(name, baseurl):
	d = get(baseurl+'/' + name).json()
	print(d)
	datastore[name] = d[name]

for x in ['vats']:
	load_data(x, baseurl_customer)

for x in ['payment_methods', 'categories']:
	load_data(x, baseurl_account)

load_data('currencies', baseurl)

def find(data_type, name):
	for variant in datastore[data_type]:
		if variant['name'] == name:
			return variant['id']

	print('Unable to find ' + data_type + ' ' + name)
	exit()
	return -1


def find_category(name):
	return find('categories', name)

def find_currency(name):
	return find('currencies', name)

def find_payment_method(name):
	return find('payment_methods', name)

def submit_milage_expense(data):

	dest_addr = {}
	if 'Delft' in data['comment']:
		dest_addr = {'location': "Vlinderweg 2, 2623 AX Delft, Netherlands", 'latitude': 51.988805, 'longitude': 4.363294}
	else:
		dest_addr = {'location': "Zuiderzeeweg 8, 1095 KJ Amsterdam, Netherlands", 'latitude': 52.370623, 'longitude': 4.963934}


	post(baseurl_account+'/expenses?exchange_rates=1', json={
		"distance": {
			"unit": "km",
			"amount": data['mileage']
		},
		"waypoints": [
			{'location': "Huizen, Netherlands", 'latitude': 52.299465, 'longitude': 5.243393},
			dest_addr
		],
		"currency_id": find_currency('Euro'),
		"expense_date": data['date'] + "T00:00:00+00:00",
		"description": data['comment'],
		"amounts": [{"category_id": find_category(category_name_map[data['route_type']])}],
		"type": "mileage",
		"tags": []
	})

category_name_map = {
	'Public Transit': 'Public Transport',
	'Parking': 'Parking',
	'Car': 'Mileage Costs',
}


def submit_receipt_expense(data):
	amount = data['refund_amount']
	vat_amount = (data['tax'] / 100.0) * amount
	vat_id = 0
	for variant in datastore['vats']:
		if variant['percentage'] == data['tax']:
			vat_id = variant['id']
			break

	if vat_id == 0:
		print('Unable to add expense, no vat found with this tax amount')
		return

	post(baseurl_account+'/expenses?exchange_rates=1', json={
		"payment_method_id": find_payment_method('Private Paid'),
		"currency_id": find_currency('Euro'),
		"country": "NL",
		"expense_date": data['date'] + "T00:00:00+00:00",
		"description": data['comment'],
		"amounts": [
			{
				"amount": amount - vat_amount,
				"vat_amount": vat_amount,
				"vat_id": vat_id,
				"category_id": find_category(category_name_map[data['route_type']]),
				"display_inclusive": True
			}
		],
		"type": "receipt",
		"tags": []
	})

if len(sys.argv) > 1:
	with open(sys.argv[1]) as file:
		arr = json.load(file)
		for item in arr:
			if item['route_type'] in ['Car']:
				submit_milage_expense(item)
			else:
				submit_receipt_expense(item)
else:
	expenses = get(baseurl_account+'/expenses').json()['expenses']
	for x in expenses:
		print(x)