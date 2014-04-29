#!/usr/bin/python


import praw


version = "0.1"
user_agent = "NineteenEightyFourBot v%s by /u/AnSq" % version


reddit = praw.Reddit(user_agent=user_agent)
reddit.login()
