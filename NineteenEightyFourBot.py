#!/usr/bin/python -u


import praw
import praw.helpers
import time


version = "0.1"
user_agent = "NineteenEightyFourBot v%s by /u/AnSq" % version


reddit = praw.Reddit(user_agent=user_agent)
reddit.login()


i = 0
try:
	stream = praw.helpers.comment_stream(reddit, "news+worldnews+politics+technology+conspiracy")
	for c in stream:
		if "1984" in c.body.split() or "big brother" in c.body.lower() or "police state" in c.body.lower() or "thought police" in c.body.lower():
			print "%d: %d points by /u/%s in /r/%s at %s - %s" % (i, c.score, c.author.name, c.subreddit.display_name, time.asctime(time.localtime(c.created)), c.permalink)
		i += 1
except Exception as e:
	print "%s : %s" % (type(e).__name__, e)
