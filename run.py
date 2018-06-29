import sys
import arrow
import argparse
import csv
import locale


avg_liter_per_km = 37.62 / 400.0
avg_liter_price = 1.70
refunded_per_km = 0.19

avg_price_per_km = avg_liter_per_km * avg_liter_price

def read_float_with_comma(num):
    return float(num.replace(",", "."))

class Trip:
        def __init__(self, date, price):
                self.date = date
                self.price = price

class Route:
        def __init__(self, name, km_per_trip, refund_per_km, price_per_km):
                self.km_per_trip = km_per_trip
                self.refund_per_km = refund_per_km
                self.name = name
                self.trips = []
                self.price_per_km = price_per_km

        def add_trip(self, date, price):
                if price is None:
                        price = self.km_per_trip * self.price_per_km
                self.trips.append(Trip(date, price))
                print("Adding trip for {} date {}".format(self.name, date.format('YYYY-MM-DD')))

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
                print("Trip: {}".format(self.name))
                print(" - Trips: {}".format(len(self.trips)))
                print(" - Total KM: {}".format(self.total_km()))
                print(" - Total price: {} euro".format(self.total_price()))
                if self.refund_per_km:
                        print(" - Total refund per km: {} euro".format(self.total_refund_per_km()))
                        print(" - Comment: {}, {} trips between {} and {}".format(
                                self.name,
                                len(self.trips),
                                self.get_first_date().format('YYYY-MM-DD'),
                                self.get_last_date().format('YYYY-MM-DD')
                                )
                        )

delftTrips = Route("Delft <> Huizen", 100.0, True, avg_price_per_km)
amsterdamCarTrips = Route("Amsterdam Zeeburg <> Huizen", 40.0, True, avg_price_per_km)
amsterdamOVTrips = Route("Amsterdam OV", 4.5, False, 0.0)


parser = argparse.ArgumentParser(description='Calculate expenses')
parser.add_argument('--ov-csv', nargs='*', type=argparse.FileType('r'))
parser.add_argument('--fromday', default=arrow.now().shift(months=-1).format('YYYY-MM-DD'))
parser.add_argument('--today', default=arrow.now().format('YYYY-MM-DD'))

args = parser.parse_args()

print(repr(args))

fromday = arrow.get(args.fromday, 'YYYY-MM-DD')
today =  arrow.get(args.today, 'YYYY-MM-DD')

print("From day: %s" % fromday.format('YYYY-MM-DD'))
print("To day:   %s" % today.format('YYYY-MM-DD'))

weekdays = []

days = 0
for r in arrow.Arrow.range('day', fromday, today):
	wd = r.isoweekday()
	if wd >= 1 and wd <= 5:
		print(r.format('YYYY-MM-DD (dddd)'))
		weekdays.append(r)
		days = days + 1

print("Total weekdays: %d" % days)


daysInAmsterdam = []

# Parsing OV CSVs
if args.ov_csv is not None:
        for f in args.ov_csv:
                reader = csv.reader(f, delimiter=';')
                for row in reader:
                        if row[0] == "Datum": continue
                        print(', '.join(row))
                        from_station = row[2]
                        to_station = row[4]

                        date = arrow.get(row[0], 'DD-MM-YYYY')
                        amsterdamOVTrips.add_trip(date, read_float_with_comma(row[5]))

                        if (
                                (from_station == 'Centraal Station' and to_station == 'Zuiderzeeweg') or
                                (to_station == 'Centraal Station' and from_station == 'Zuiderzeeweg')
                        ):
                                daysInAmsterdam.append(date)

for day in set(daysInAmsterdam):
        amsterdamCarTrips.add_trip(day, None)
        amsterdamCarTrips.add_trip(day, None)

leftoverDays = []

amsterdamCarTrips.remove_trips_not_in_days(weekdays, leftoverDays)
amsterdamOVTrips.remove_trips_not_in_days(weekdays, leftoverDays)

for day in set(leftoverDays):
        delftTrips.add_trip(day, None)
        delftTrips.add_trip(day, None)

delftTrips.remove_trips_not_in_days(weekdays, None)

sumkm = 0.0
sumprice = 0.0
refundprice = 0.0

for trip in [amsterdamCarTrips, amsterdamOVTrips, delftTrips]:
        trip.report()
        sumkm += trip.total_km()
        sumprice += trip.total_price()
        refundprice += trip.total_refund_per_km()

print("Total KM: {}".format(sumkm))
print("Total Price: {}".format(sumprice))
print("Total refundable price: {}".format(refundprice))

