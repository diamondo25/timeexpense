import sys
import csv
import arrow

"""
Usage: 

Download CSV from all transactions here: https://bankieren.rabobank.nl/online/nl/dashboard/betalen/transacties/
Put CSV in input folder


rabobank.py transactions.csv
"""


columns = ['Datum', 'Omschrijving', 'Bedrag', 'Tegenrekening naam', 'Via', 'Verwerkingsdatum']

records_per_month = {}


with open(sys.argv[1], newline='') as csvfile:
	r = csv.DictReader(csvfile, delimiter=';')

	for row in r:
		if 'P+R Zeeburg' in row['Omschrijving']: continue

		month = row['Datum'][:-3]
		if month not in records_per_month:
			records_per_month[month] = []

		tmp = {}
		for c in columns:
			tmp[c] = row[c]

		records_per_month[month].append(tmp)


for date, data in records_per_month.items():
	with open('input/rabobank-bymonth-' + date + '.csv', 'w', newline='') as f:
		w = csv.DictWriter(f, fieldnames=columns)

		w.writeheader()
		w.writerows(data)
