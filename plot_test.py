#!/usr/bin/python

import matplotlib.pyplot as plt
import sqlite3


db = sqlite3.connect("test.sqlite")
rs = db.execute("SELECT activity_rate, k, subreddit FROM subreddit_stats WHERE subscribers NOT NULL")

x = []
y = []
subs = []

for row in rs:
	#print row
	x.append(row[0])
	y.append(row[1])
	subs.append(row[2])

plt.scatter(x, y, alpha=0.75, s=0.5)
for sub, x, y in zip(subs, x, y):
	plt.annotate(sub, xy=(x,y), alpha="0.4")
plt.show()

db.close()
