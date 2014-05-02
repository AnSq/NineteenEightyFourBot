#!/usr/bin/python -u


import praw
import praw.helpers
import time
import sqlite3


version = "0.2"
user_agent = "NineteenEightyFourBot v%s by /u/AnSq" % version


reddit = praw.Reddit(user_agent=user_agent)
reddit.login()

db = sqlite3.connect("test.sqlite")

i = 0
try:
	stream = praw.helpers.comment_stream(reddit, "all", verbosity=3) #"news+worldnews+politics+technology+conspiracy")
	for c in stream:
		if "1984" in c.body.split() or "big brother" in c.body.lower() or "police state" in c.body.lower() or "thought police" in c.body.lower():
			print "%d: %d points by /u/%s in /r/%s at %s - %s" % (i, c.score, c.author.name, c.subreddit.display_name, time.asctime(time.localtime(c.created)), c.permalink)
			db.execute("INSERT OR REPLACE INTO comments (" +
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
				") values (" + "?," * 32 + "?);",
				(
					praw.helpers.convert_id36_to_numeric_id(c.id),
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
			)
			db.commit()
		i += 1
except Exception as e:
	print "%s : %s" % (type(e).__name__, e)
