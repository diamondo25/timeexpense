import arrow
import argparse
import csv
import os

avg_liter_per_km = 1.0 / 8
avg_liter_price = 1.63
refunded_per_km = 0.19

avg_price_per_km = avg_liter_per_km * avg_liter_price

def read_float_with_comma(num):
	return float(num.replace(',', '.'))

class Trip:
		def __init__(self, date, price):
				self.date = date
				self.price = price

class Route:
		def __init__(self, name, route_type, km_per_trip, refund_per_km, price_per_km):
				self.km_per_trip = km_per_trip
				self.refund_per_km = refund_per_km
				self.name = name
				self.trips = []
				self.price_per_km = price_per_km
				self.route_type = route_type

		def add_trip(self, date, price):
				if price is None:
						price = self.km_per_trip * self.price_per_km
				self.trips.append(Trip(date, price))
				print('Adding trip for {} date {}'.format(self.name, date.format('YYYY-MM-DD')))

		def total_km(self):
				return len(self.trips) * self.km_per_trip

		def total_price(self):
				sum = 0.0
				for trip in self.trips:
						sum += trip.price
				return sum

		def total_refund_per_km(self):
				if self.refund_per_km:
						return self.total_km() * refunded_per_km
				else:
						return 0.0

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

		def report(self):
				if len(self.trips) == 0:
					print('No trips for {} ({})'.format(self.name, self.route_type))
					return

				print('Trip: {} ({})'.format(self.name, self.route_type))
				print(' - Trips: {}'.format(len(self.trips)))
				print(' - Total KM: {}'.format(self.total_km()))
				print(' - Total price: {} euro'.format(self.total_price()))
				if self.refund_per_km:
						print(' - Total refund per km: {} euro'.format(self.total_refund_per_km()))
				first_date = self.get_first_date()
				last_date = self.get_last_date()
				trip_date_text = ''
				if first_date == last_date:
					trip_date_text = 'on ' + first_date.format('YYYY-MM-DD')
				else:
					trip_date_text = 'between %s and %s' % (
						self.get_first_date().format('YYYY-MM-DD'),
						self.get_last_date().format('YYYY-MM-DD')
					)
					
				print(' - Comment: {}, {} trips {}'.format(
						self.name,
						len(self.trips),
						trip_date_text
						)
				)

delftTrips = Route('Delft <> Huizen', 'Car', 100.0, True, avg_price_per_km)
amsterdamCarTrips = Route('Amsterdam Zeeburg <> Huizen', 'Car', 40.0, True, avg_price_per_km)
amsterdamOVTrips = Route('Amsterdam OV', 'Public Transit', 4.5, False, 0.0)
amsterdamParking = Route('Amsterdam Zeeburg parking', 'Parking', 0.0, False, 0.0)

parser = argparse.ArgumentParser(description='Calculate expenses')
parser.add_argument('--ov-csv', nargs='*', type=argparse.FileType('r'))
parser.add_argument('--fromday', default=arrow.now().shift(months=-1).format('YYYY-MM-DD'))
parser.add_argument('--today', default=arrow.now().format('YYYY-MM-DD'))
parser.add_argument('--euro95-price', default=avg_liter_price, type=int)
parser.add_argument('--skipday', nargs='*')
parser.add_argument('--sub-a-day', action='store_true')

args = parser.parse_args()

# print(repr(args))
avg_liter_price = args.euro95_price

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
			if not line:
				break

			elems = line.split("\t")
			x = arrow.get(elems[0], 'YYYY-MM-DD')
			y = arrow.get(elems[1], 'YYYY-MM-DD')
			for r in get_weekdays_from_range(x, y):
				skipdays.append(r)

for x in skipdays:
	print('Skipping %s' % (x.format('YYYY-MM-DD (dddd)')))

weekdays = []

days = 0
for r in get_weekdays_from_range(fromday, today):
	if r in skipdays:
		continue

	print('Adding weekday %s' % (r.format('YYYY-MM-DD (dddd)')))
	weekdays.append(r)
	days = days + 1

print('Total weekdays: %d' % days)


daysInAmsterdam = []
earlyDaysInAmsterdam = []
newestDateInCSV = arrow.get('1999-12-31', 'YYYY-MM-DD')

# Parsing OV CSVs
if args.ov_csv is not None:
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

print('Adding car trips....')

for day in set(daysInAmsterdam):
		# From and to
		amsterdamCarTrips.add_trip(day, None)
		amsterdamCarTrips.add_trip(day, None)
		if day in earlyDaysInAmsterdam:
			# Late checkins are more expensive
			amsterdamParking.add_trip(day, 8.0)
		else:
			amsterdamParking.add_trip(day, 1.0)

leftoverDays = []

print('Removing days that were not weekdays...')

amsterdamCarTrips.remove_trips_not_in_days(weekdays, leftoverDays)
amsterdamOVTrips.remove_trips_not_in_days(weekdays, leftoverDays)
amsterdamParking.remove_trips_not_in_days(weekdays, leftoverDays)

print('Adding trips to delft...')

for day in set(leftoverDays):
		# From and to
		delftTrips.add_trip(day, None)
		delftTrips.add_trip(day, None)

print('Also cleaning up delft trips...')
delftTrips.remove_trips_not_in_days(weekdays, None)

sumkm = 0.0
sumprice = 0.0
refundprice = 0.0

print('')
print('')
print('')
print('--- Trips:')
print('')

for trip in [amsterdamOVTrips, amsterdamParking, amsterdamCarTrips, delftTrips]:
		trip.report()
		sumkm += trip.total_km()
		sumprice += trip.total_price()
		refundprice += trip.total_refund_per_km()

print('Total KM: {}'.format(sumkm))
print('Total Price: {}'.format(sumprice))
print('Total refundable price: {}'.format(refundprice))

print('Newest date in CSV: {}'.format(newestDateInCSV))
