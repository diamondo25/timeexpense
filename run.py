import arrow
from datetime import date, timedelta
import argparse
import csv
import os
import json

avg_liter_per_km = 1.0 / 8
avg_liter_price = 1.63
refunded_per_km = 0.19

avg_price_per_km = avg_liter_per_km * avg_liter_price

def read_float_with_comma(num):
	return round(float(num.replace(',', '.')), 2)

class Trip:
	def __init__(self, date, price):
		self.date = date
		self.price = price

class Route:
	def __init__(self, name, route_type, km_per_trip, refund_per_km, price_per_km, tax):
		self.km_per_trip = km_per_trip
		self.refund_per_km = refund_per_km
		self.name = name
		self.trips = []
		self.price_per_km = price_per_km
		self.route_type = route_type
		self.tax = tax

	def add_trip(self, date, price):
		if price is None:
			price = self.km_per_trip * self.price_per_km
			price = round(price, 2)
		self.trips.append(Trip(date, price))
		print('Adding trip for {} date {} ({} price)'.format(self.name, date.format('YYYY-MM-DD'), price))

	def has_trips(self):
		return len(self.trips) > 0

	def total_km(self):
		return len(self.trips) * self.km_per_trip

	def total_price(self):
		sum = 0
		for trip in self.trips:
			sum += trip.price
		return sum

	def total_refund_per_km(self):
		if self.refund_per_km:
			return self.total_km() * refunded_per_km
		else:
			return 0

	def get_first_date(self):
		date = None
		for trip in self.trips:
			if date is None or trip.date < date:
				date = trip.date
		return date

	def get_last_date(self):
		date = None
		for trip in self.trips:
			if date is None or trip.date > date:
				date = trip.date
		return date

	def remove_trips_not_in_days(self, days, days_not_tripped):
		new_trips = []
		for day in days:
			found = False
			for trip in self.trips:
				if day == trip.date:
					new_trips.append(trip)
					found = True
			if found == False and days_not_tripped is not None:
				days_not_tripped.append(day)

		self.trips = new_trips

	def get_comment(self):
		first_date = self.get_first_date()
		last_date = self.get_last_date()
		trip_date_text = ''
		if first_date == last_date:
			trip_date_text = 'on ' + first_date.format('YYYY-MM-DD')
		else:
			trip_date_text = 'between %s and %s' % (
				first_date.format('YYYY-MM-DD'),
				last_date.format('YYYY-MM-DD')
			)

		return '{}, {} trips {}'.format(
			self.name,
			len(self.trips),
			trip_date_text
		)


	def report(self):
		if len(self.trips) == 0:
			print('No trips for {} ({})'.format(self.name, self.route_type))
			return

		print('Trip: {} ({})'.format(self.name, self.route_type))
		print(' - Trips: {}'.format(len(self.trips)))
		print(' - Total KM: {}'.format(self.total_km()))
		print(' - Total price: {:.2f} euro'.format(self.total_price()))
		if self.refund_per_km:
			print(' - Total refund per km: {:.2f} euro'.format(self.total_refund_per_km()))
			
		print(' - Comment: {}'.format(self.get_comment()))

	def get_json_dict(self):
		ret = {}
		ret['comment'] = self.get_comment()
		ret['route_type'] = self.route_type
		ret['date'] = self.get_first_date().format('YYYY-MM-DD')
		if self.refund_per_km:
			ret['mileage'] = self.total_km()
		else:
			ret['refund_amount'] = self.total_price()
			ret['tax'] = self.tax

		return ret

delftTrips = Route('Delft <> Huizen', 'Car', 100, True, avg_price_per_km, 0)
amsterdamCarTrips = Route('Amsterdam Zeeburg <> Huizen', 'Car', 40, True, avg_price_per_km, 0)
amsterdamOVTrips = Route('Amsterdam OV', 'Public Transit', 4.5, False, 0, 9)
# https://btw-berekenen-online.nl/btw-op-parkeren/
# Parking on the road is 0%, parking on Zeeburg is 21%
amsterdamParkingZeeburg = Route('Amsterdam Zeeburg parking', 'Parking', 0, False, 0, 21)

parser = argparse.ArgumentParser(description='Calculate expenses')
parser.add_argument('--ov-csv', nargs='*', type=argparse.FileType('r'))
parser.add_argument('--rabo-csv', nargs='*', type=argparse.FileType('r'))
parser.add_argument('--pm-csv', type=argparse.FileType('r'))
parser.add_argument('--fromday', default=arrow.now().shift(months=-1).format('YYYY-MM-DD'))
parser.add_argument('--today', default=arrow.now().format('YYYY-MM-DD'))
parser.add_argument('--year', type=int)
parser.add_argument('--month', type=int)
parser.add_argument('--euro95-price', default=avg_liter_price, type=int)
parser.add_argument('--skipday', nargs='*')
parser.add_argument('--sub-a-day', action='store_true')

args = parser.parse_args()

# print(repr(args))
avg_liter_price = args.euro95_price

if args.month is not None:
	year = args.year
	month = args.month

	fromd = date(year, month, 1)
	if month == 12:
		month = 0
		year += 1
	tod = date(year, month+1, 1) - (timedelta(days=1))
	fromday = arrow.get(fromd)
	today = arrow.get(tod)
else:
	fromday = arrow.get(args.fromday, 'YYYY-MM-DD')
	today =  arrow.get(args.today, 'YYYY-MM-DD')

if args.sub_a_day:
	today = today.shift(days=-1)

print('From day: %s' % fromday.format('YYYY-MM-DD'))
print('To day:   %s' % today.format('YYYY-MM-DD'))

skipdays = []

if args.skipday:
	for day in args.skipday:
		skip = arrow.get(day, 'YYYY-MM-DD')
		skipdays.append(skip)

def get_weekdays_from_range(fromday, today):
	arr = []
	for r in arrow.Arrow.range('day', fromday, today):

		wd = r.isoweekday()
		if wd >= 1 and wd <= 5:
			arr.append(r)

	return arr



if os.path.isfile('holiday.txt'):
	with open('holiday.txt') as f:
		while True:
			line = f.readline()
			if not line: break

			elems = line.split("\t")
			x = arrow.get(elems[0], 'YYYY-MM-DD')
			y = arrow.get(elems[1], 'YYYY-MM-DD')
			for r in get_weekdays_from_range(x, y):
				skipdays.append(r)

#for x in skipdays:
#	print('Skipping %s' % (x.format('YYYY-MM-DD (dddd)')))

weekdays = []

days = 0
for r in get_weekdays_from_range(fromday, today):
	if r in skipdays: continue

	print('Adding weekday %s' % (r.format('YYYY-MM-DD (dddd)')))
	weekdays.append(r)
	days = days + 1

print('Total weekdays: %d' % days)


daysInAmsterdam = []
earlyDaysInAmsterdam = []
newestDateInCSV = arrow.get('1999-12-31', 'YYYY-MM-DD')

# Parsing OV CSVs
if args.ov_csv is not None:
	print('Processing OV-chipkaart data')
	for f in args.ov_csv:
		reader = csv.reader(f, delimiter=';')
		for row in reader:
			if row[0] == 'Datum': continue

			date = arrow.get(row[0], 'DD-MM-YYYY')

			if newestDateInCSV < date:
				newestDateInCSV = date
			
			if (date < fromday) or (date > today): continue

			# print(', '.join(row))
			start_date = row[0]
			from_station = row[2]
			checkin_time = row[3]
			to_station = row[4]
			
			checkin_fulldate = arrow.get(start_date + ' ' + checkin_time, 'DD-MM-YYYY HH:mm')
			amsterdamOVTrips.add_trip(date, read_float_with_comma(row[5]))

			tripStartSecondsFromStartOfDay = (checkin_fulldate.datetime - date.datetime).total_seconds()

			# Handling the 'been in amsterdam' stuff
			if (
				from_station == 'Centraal Station' and to_station == 'Zuiderzeeweg' and
				tripStartSecondsFromStartOfDay <= (60 * 12 * 60)
			):
				if tripStartSecondsFromStartOfDay <= (60 * 6 * 60):
					print('Went home in the middle of the night... %s' % (checkin_fulldate.format('DD-MM-YYYY HH:mm')))
				else:
					print('Went home early? %s' % (checkin_fulldate.format('DD-MM-YYYY HH:mm')))
					continue

			if (
				(from_station == 'Centraal Station' and to_station == 'Zuiderzeeweg') or
				(to_station == 'Centraal Station' and from_station == 'Zuiderzeeweg')
			):
				if tripStartSecondsFromStartOfDay <= (60 * 10.25 * 60):
					print('Early date? %s' % (checkin_fulldate.format('DD-MM-YYYY HH:mm')))
					earlyDaysInAmsterdam.append(date)
				daysInAmsterdam.append(date)



if args.rabo_csv is not None:
	print('Processing Rabobank data')
	btlatm = 'Betaalautomaat '
	for f in args.rabo_csv:
		reader = csv.DictReader(f)
		for row in reader:
			date = arrow.get(row['Datum'], 'YYYY-MM-DD')
			description = row['Omschrijving']
			pay_time = description[len(btlatm):]
			pay_time = pay_time[:5]
			hour = pay_time[0:2]
			if hour[0] == '0': 
				hour = hour[1:]

			hour = int(hour)
			stayed_in_amsterdam = hour <= 3 or hour >= 13

			if hour >= 0 and hour <= 3:
				# holy shit erwin wtf...
				# gotta correct for that
				date = date.shift(days=-1)
				print('Stop leaving work so late: ' + description)


			if (date < fromday) or (date > today): continue

			amsterdamParkingZeeburg.add_trip(date, float(row['Bedrag']) * -1.0)
			
			if stayed_in_amsterdam:
				daysInAmsterdam.append(date)




if args.pm_csv is not None:
	print('Processing parkmobile data')
	reader = csv.DictReader(args.pm_csv)

	for row in reader:
		# Mark all days in amsterdam when we parked there
		date = arrow.get(row['StartTime'], 'D-M-YYYY H:mm:ss')
		if (date < fromday) or (date > today): continue

		if 'Amsterdam' not in row['LocationDesc']: continue
		print('Parked in amsterdam @ %s ' % (date.format('DD-MM-YYYY')))
		daysInAmsterdam.append(date)


print('Adding car trips....')

for day in set(daysInAmsterdam):
	# From and to
	amsterdamCarTrips.add_trip(day, None)
	amsterdamCarTrips.add_trip(day, None)

leftoverDays = []

print('Removing days that were not weekdays...')

amsterdamCarTrips.remove_trips_not_in_days(weekdays, leftoverDays)
amsterdamOVTrips.remove_trips_not_in_days(weekdays, leftoverDays)
amsterdamParkingZeeburg.remove_trips_not_in_days(weekdays, leftoverDays)

print('Adding trips to delft...')

for day in set(leftoverDays):
	# From and to
	delftTrips.add_trip(day, None)
	delftTrips.add_trip(day, None)

print('Also cleaning up delft trips...')
delftTrips.remove_trips_not_in_days(weekdays, None)

sumkm = 0
sumprice = 0
refundprice = 0

print('')
print('')
print('')
print('--- Trips:')
print('')

json_output = []

for trip in [amsterdamOVTrips, amsterdamParkingZeeburg, amsterdamCarTrips, delftTrips]:
	trip.report()
	sumkm += trip.total_km()
	sumprice += trip.total_price()
	refundprice += trip.total_refund_per_km()

	if trip.has_trips():
		json_output.append(trip.get_json_dict())

print('Total KM: {}'.format(sumkm))
print('Total Price: {}'.format(sumprice))
print('Total refundable price: {}'.format(refundprice))

print('Newest date in CSV: {}'.format(newestDateInCSV))


json_filename = 'output/%s_%s.json' % (
	fromday.format('YYYY-MM-DD'),
	today.format('YYYY-MM-DD')
)

with open(json_filename, 'wb') as fd:
	fd.write(json.dumps(json_output, indent=4).encode('utf-8'))

print('Wrote JSON file: {}'.format(json_filename))
