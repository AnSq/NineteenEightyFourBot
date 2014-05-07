#!/usr/bin/python -u


import praw
import praw.helpers
import time
import calendar
import sqlite3


version = "0.6"
user_agent = "NineteenEightyFourBot v%s by /u/AnSq" % version


def thing_id(id):
	return praw.helpers.convert_id36_to_numeric_id(id)


class DataAccessObject (object):
	def __init__(self, dbname):
		self.db = db = sqlite3.connect(dbname + ".sqlite")
		self.phrase_table = dict(db.execute("SELECT lower(phrase),id FROM phrases").fetchall())

		self.db.execute("PRAGMA foreign_keys = ON")
		self.db.commit()

	def insert_into_comments(self, comment):
		c = comment
		data = (
			thing_id(c.id),
			c.__hash__(),
			c.approved_by,
			c.author.name,
			c.author_flair_css_class,
			c.author_flair_text,
			c.banned_by,
			c.body,
			c.body_html,
			c.created,
			c.created_utc,
			c.distinguished,
			c.downs,
			c.edited,
			c.fullname,
			c.gilded,
			c.id,
			c.is_root,
			c.likes,
			c.link_author,
			c.link_id,
			c.link_title,
			c.link_url,
			c.name,
			c.num_reports,
			c.parent_id,
			c.permalink,
			c.saved,
			c.score,
			c.score_hidden,
			c.subreddit.display_name,
			c.subreddit_id,
			c.ups
		)
		self.db.execute("INSERT OR REPLACE INTO comments (" +
				"id," +
				"__hash__," +
				"approved_by," +
				"author," +
				"author_flair_css_class," +
				"author_flair_text," +
				"banned_by," +
				"body," +
				"body_html," +
				"created," +
				"created_utc," +
				"distinguished," +
				"downs," +
				"edited," +
				"fullname," +
				"gilded," +
				"id_b36," +
				"is_root," +
				"likes," +
				"link_author," +
				"link_id," +
				"link_title," +
				"link_url," +
				"name," +
				"num_reports," +
				"parent_id," +
				"permalink," +
				"saved," +
				"score," +
				"score_hidden," +
				"subreddit," +
				"subreddit_id," +
				"ups" +
			") VALUES (" + "?," * 32 + "?);",
			data
		)
		self.db.commit()

	def insert_comment_counts(self, c_id, counts):
		for phrase in counts:
			count = counts[phrase]
			if count[False] + count[True] > 0:
				data = (c_id, self.phrase_table[phrase], count[False], count[True])
				self.db.execute("INSERT OR REPLACE INTO comment_phrase (comment,phrase,unquoted,quoted) VALUES (?,?,?,?)", data)
				self.db.commit()

	def insert_into_subreddits(self, subreddit):
		s = subreddit
		data = (thing_id(s.id), s.id, s.display_name, s.subscribers)
		self.db.execute("INSERT OR REPLACE INTO subreddits (id, id_b36, display_name, subscribers) VALUES (?,?,?,?)", data)
		self.db.commit()


class Detector (object):
	def __init__(self, phrase):
		self.phrase = phrase.lower()

	def detect(self, comment):
		count = {False: 0, True: 0} # key is if it's quoted
		for line in comment.body.lower().splitlines():
			quoted = line.strip()[:4] == "&gt;"
			start = 0
			while start < len(line) and start != -1:
				index = line.find(self.phrase, start)
				if index == -1:
					break
				else:
					count[quoted] += 1
					start = index + 1
		return count


class FreeYearDetector (Detector):
	"""detects a year-like string when it doesn't have a month near it,
	another year near it, or another number next to it"""

	def __init__(self, phrase):
		super(FreeYearDetector, self).__init__(phrase)
		self.months = [m.lower() for m in calendar.month_name[1:] + calendar.month_abbr[1:]]
		self.search_len = max([len(m) for m in self.months]) + 5

	def search_numbers(self, line, index, radius, length):
		start = max(index - radius, 0)
		end = index + len(self.phrase) + radius
		pre = line[start:index]
		post = line[index + len(self.phrase) : end]
		str = pre + " " + post
		return "1"*length in "".join(["1" if c.isdigit() else "0" for c in str])

	def detect(self, comment):
		count = {False: 0, True: 0} # key is if it's quoted
		for line in comment.body.lower().splitlines():
			quoted = line.strip()[:4] == "&gt;"
			start = 0
			while start < len(line) and start != -1:
				index = line.find(self.phrase, start)
				if index == -1:
					break

				#search for months
				start = max(index - self.search_len, 0)
				end = index + len(self.phrase) + self.search_len
				found_month = any([m in line[start:end] for m in self.months])

				#search for numbers
				found_year = self.search_numbers(line, index, self.search_len, 4)
				found_number = self.search_numbers(line, index, 2, 1)

				if not found_month and not found_year and not found_number:
					count[quoted] += 1
				start = index + 1
		return count


class DetectorMaker (object):
	def __init__(self):
		pass

	def get_detector(self, phrase):
		# add other detectors here
		if (phrase == "1984"):
			return FreeYearDetector(phrase)
		else:
			return Detector(phrase)

	def get_detectors(self, phrases):
		detectors = []
		for p in phrases:
			detectors.append(self.get_detector(p))
		return detectors


class CommentHandler (object):
	def __init__(self, dao):
		self.dao = dao
		self.detectors = DetectorMaker().get_detectors(dao.phrase_table.keys())

	def any(self, counts):
		"""Flattens the doubly-nested dict of counts into a
		single bool representing if any at all are > 0.
		See https://stackoverflow.com/questions/952914/making-a-flat-list-out-of-list-of-lists-in-python """
		return sum([number for outlist in [inlist.values() for inlist in counts.values()] for number in outlist]) > 0

	def handle(self, comment):
		counts = {}
		for d in self.detectors:
			counts[d.phrase] = d.detect(comment)

		if self.any(counts):
			t = time.asctime(time.localtime())
			print "%s: /u/%s in /r/%s (%d) - %s" % (t, comment.author.name, comment.subreddit.display_name, comment.subreddit.subscribers, comment.permalink)
			self.dao.insert_into_comments(comment)
			self.dao.insert_comment_counts(thing_id(comment.id), counts)
			self.dao.insert_into_subreddits(comment.subreddit)


def main():
	print user_agent
	reddit = praw.Reddit(user_agent=user_agent)
	print "Logging in...",
	reddit.login()
	print reddit.user.name

	handler = CommentHandler(DataAccessObject("test"))

	i = 0
	stream = praw.helpers.comment_stream(reddit, "all", verbosity=3)
	for comment in stream:
		handler.handle(comment)
		i += 1


if __name__ == "__main__":
	main()
