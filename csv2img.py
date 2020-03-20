# Make sure you've got orca installed:
# npm install -g electron@6.1.4 orca


import plotly.graph_objects as go
import sys
import csv


for filename in sys.argv[1:]:
	if '.png' in filename: continue

	with open(filename, newline='') as f:
		r = csv.DictReader(f)
		cells = []

		# Data is stored in columns rather than rows
		rows = []
		for row in r:
			rows.append(row)

		for col in r.fieldnames:
			t = []
			for row in rows:
				t.append(row[col])
			cells.append(t)

		fig = go.Figure(
			data=[
				go.Table(
					header=dict(values=r.fieldnames),
					cells=dict(values=cells),
				)
			],
			layout=dict(autosize=True)
		)

		#fig.show()

		fig.write_image(filename + '.png', width=1600, height=300+(len(rows)*20), scale=1)