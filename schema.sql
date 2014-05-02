PRAGMA foreign_keys = ON;


DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS phrases;
DROP TABLE IF EXISTS comment_phrase;


CREATE TABLE comments (
	id INTEGER PRIMARY KEY,
	__hash__ INTEGER,
	approved_by TEXT,
	author TEXT,
	author_flair_css_class TEXT,
	author_flair_text TEXT,
	banned_by TEXT,
	body TEXT,
	body_html TEXT,
	created REAL,
	created_utc REAL,
	distinguished TEXT,
	downs INTEGER,
	edited REAL,
	fullname TEXT,
	gilded INTEGER,
	id_b36 TEXT,
	is_root BOOLEAN,
	likes BOOLEAN,
	link_author TEXT,
	link_id TEXT,
	link_title TEXT,
	link_url TEXT,
	name TEXT,
	num_reports TEXT,
	parent_id TEXT,
	permalink TEXT,
	saved BOOLEAN,
	score INTEGER,
	score_hidden BOOLEAN,
	subreddit TEXT,
	subreddit_id TEXT,
	ups INTEGER
);


CREATE TABLE phrases (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	phrase TEXT UNIQUE NOT NULL
);


CREATE TABLE comment_phrase (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	comment INTEGER NOT NULL,
	phrase INTEGER NOT NULL,
	count INTEGER NOT NULL DEFAULT 0,
	FOREIGN KEY (comment) REFERENCES comment (id),
	FOREIGN KEY (phrase) REFERENCES phrases (id)
);
