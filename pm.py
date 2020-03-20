import sys
import csv

"""
Usage: 

Download CSV from all transactions here: https://nl.parkmobile.com/Epms/ClientPages/permit/productactions.aspx?quickAction=ParkingHistory
Put CSV in input folder


pm.py xxxx-Parkeeracties.csv
"""


with open('input/parkmobile-clean.csv', 'w', newline='') as output:
	with open(sys.argv[1], newline='') as csvfile:
		r = csv.DictReader(csvfile)

		w = csv.DictWriter(output, fieldnames=r.fieldnames)
		w.writeheader()

		for row in r:
			locdesc = row['LocationDesc']
			if not ('Delft' in locdesc or 'Amsterdam' in locdesc): continue

			w.writerow(row)