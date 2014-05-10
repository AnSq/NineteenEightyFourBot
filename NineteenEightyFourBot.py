#!/usr/bin/python -u


import praw
import praw.helpers
import time
import calendar
import sqlite3
import sys


version = "0.8.4"
user_agent = "NineteenEightyFourBot v%s by /u/AnSq" % version


def thing_id(id):
	return praw.helpers.convert_id36_to_numeric_id(id)


class DataAccessObject (object):
	def __init__(self, dbname):
		self.db = db = sqlite3.connect(dbname + ".sqlite")
		self.phrase_table = dict(db.execute("SELECT lower(phrase), id FROM phrases").fetchall())
		self._pending_requests = []

		self.db.execute("PRAGMA foreign_keys = ON")
		self.commit()

	def close(self):
		self.push_pending()
		self.db.close()

	def commit(self):
		while True:
			try:
				self.db.commit()
				break
			except Exception as e:
				print "%s: %s" % (tyep(e).__name__, e)
				time.sleep(0.1)

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
		self.db.execute(
			"INSERT OR REPLACE INTO comments (" +
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
		self.commit()

	def insert_comment_counts(self, c_id, counts):
		for phrase in counts:
			count = counts[phrase]
			if count[False] + count[True] > 0:
				data = (c_id, self.phrase_table[phrase], count[False], count[True])
				self.db.execute("INSERT OR REPLACE INTO comment_phrase (comment, phrase, unquoted, quoted) VALUES (?,?,?,?)", data)
		self.commit()

	def update_subreddit_comment_count(self, subreddit):
		#this happens so often I want to save some of it up so it doesn't constantly hit the database
		s = subreddit
		self._pending_requests.append(("INSERT OR IGNORE INTO subreddits (display_name) VALUES (?)", (s.display_name,)))
		self._pending_requests.append(
			("UPDATE subreddits SET scanned_comments = scanned_comments + 1 WHERE display_name == ?",
			(s.display_name,))
		)

	def push_pending(self):
		#print len(self._pending_requests)
		for i in range(0, len(self._pending_requests)):
			self.db.execute(self._pending_requests[i][0], self._pending_requests[i][1])
		self.commit()
		self._pending_requests = []

	def update_subreddit_subscribers(self, subreddit):
		"""use with caution, this makes a network call for unfetched subreddits"""
		s = subreddit
		self.db.execute("UPDATE subreddits SET subscribers = ? WHERE display_name == ?", (s.subscribers, s.display_name))
		self.commit()


class Detector (object):
	def __init__(self, phrase):
		self.phrase = phrase.lower()

	def filter(self, line, index):
		return True

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
					if self.filter(line, index):
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

	def filter(self, line, index):
		#search for months
		start = max(index - self.search_len, 0)
		end = index + len(self.phrase) + self.search_len
		found_month = any([m in line[start:end] for m in self.months])

		#search for numbers
		found_year = self.search_numbers(line, index, self.search_len, 4)
		found_number = self.search_numbers(line, index, 2, 1)

		return not found_month and not found_year and not found_number


class WordDetector (Detector):
	"""detects a word only when it's surrounded by non-word chars"""

	def filter(self, line, index):
		pre = index - 1
		post = index + len(self.phrase)
		return (pre < 0 or not line[pre].isalpha()) and (post >= len(line) or not line[post].isalpha())


class DetectorMaker (object):
	def __init__(self):
		pass

	def get_detector(self, phrase):
		# add other detectors here
		if phrase == "1984":
			return FreeYearDetector(phrase)
		elif phrase == "stasi" \
		or   phrase == "police state" \
		or   phrase == "illuminati":
			return WordDetector(phrase)
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
		self.times_called = 0
		self.time_pushed = time.time()

	def close(self):
		self.dao.close()

	def any(self, counts):
		"""Flattens the doubly-nested dict of counts into a
		single bool representing if any at all are > 0.
		See https://stackoverflow.com/questions/952914/making-a-flat-list-out-of-list-of-lists-in-python """
		return sum([number for outlist in [inlist.values() for inlist in counts.values()] for number in outlist]) > 0

	def handle(self, comment):
		self.times_called += 1

		self.dao.update_subreddit_comment_count(comment.subreddit)

		if self.times_called % 1000 == 0 or time.time() - self.time_pushed > 10:
			self.dao.push_pending()
			self.time_pushed = time.time()

		counts = {}
		for d in self.detectors:
			#start = time.time()
			counts[d.phrase] = d.detect(comment)
			#print d.phrase,time.time()-start

		if self.any(counts):
			t = time.asctime(time.localtime())
			print "%s: /u/%s in /r/%s - %s" % (t, comment.author.name, comment.subreddit.display_name, comment.permalink)
			self.dao.insert_into_comments(comment)
			self.dao.insert_comment_counts(thing_id(comment.id), counts)
			self.dao.update_subreddit_subscribers(comment.subreddit)


def get_praw_handler():
	handler = None
	if len(sys.argv) > 1 and sys.argv[1] == "-m":
		handler = praw.handlers.MultiprocessHandler()
	else:
		handler = praw.handlers.DefaultHandler()
	return handler


def main():
	try:
		handler = CommentHandler(DataAccessObject("test"))

		print user_agent
		print time.asctime(time.localtime())
		reddit = praw.Reddit(user_agent=user_agent, handler=get_praw_handler())
		print "Logging in...",
		reddit.login()
		print reddit.user.name

		i = 0
		stream = praw.helpers.comment_stream(reddit, "all", verbosity=3)
		#for comment in stream:
		while True:
			comment = None
			while True:
				try:
					comment = stream.next()
					break
				except StopIteration as e:
					print "StopIteration"
					time.sleep(0.1)
					#stream = praw.helpers.comment_stream(reddit, "all", verbosity=3)
				except Exception as e:
					print "\r%s: %s" % (type(e).__name__, e),
					time.sleep(0.1)
			#start = time.time()
			try:
				handler.handle(comment)
			except Exception as e:
				print "%s: %s" % (type(e).__name__, e)
			#print round(time.time()-start,4),
			i += 1
	except KeyboardInterrupt as e:
		print "\nclosing"
		handler.close()
		exit()


if __name__ == "__main__":
	main()
