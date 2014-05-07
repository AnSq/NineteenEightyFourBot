PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS comments;
CREATE TABLE comments (
	id                     INTEGER PRIMARY KEY,
	__hash__               INTEGER,
	approved_by            TEXT,
	author                 TEXT,
	author_flair_css_class TEXT,
	author_flair_text      TEXT,
	banned_by              TEXT,
	body                   TEXT,
	body_html              TEXT,
	created                REAL,
	created_utc            REAL,
	distinguished          TEXT,
	downs                  INTEGER,
	edited                 REAL,
	fullname               TEXT,
	gilded                 INTEGER,
	id_b36                 TEXT,
	is_root                BOOLEAN,
	likes                  BOOLEAN,
	link_author            TEXT,
	link_id                TEXT,
	link_title             TEXT,
	link_url               TEXT,
	name                   TEXT,
	num_reports            TEXT,
	parent_id              TEXT,
	permalink              TEXT,
	saved                  BOOLEAN,
	score                  INTEGER,
	score_hidden           BOOLEAN,
	subreddit              TEXT,
	subreddit_id           TEXT,
	ups                    INTEGER
);

DROP TABLE IF EXISTS phrases;
CREATE TABLE phrases (
	id     INTEGER PRIMARY KEY AUTOINCREMENT,
	phrase TEXT UNIQUE NOT NULL,
	report BOOLEAN DEFAULT 1
);

INSERT INTO phrases (phrase) VALUES ("1984");
INSERT INTO phrases (phrase) VALUES ("thought police");
INSERT INTO phrases (phrase) VALUES ("police state");
INSERT INTO phrases (phrase) VALUES ("fascis");
INSERT INTO phrases (phrase) VALUES ("Orwell");
INSERT INTO phrases (phrase) VALUES ("Snowden");
INSERT INTO phrases (phrase) VALUES ("The NSA");
INSERT INTO phrases (phrase) VALUES ("Illuminati");
INSERT INTO phrases (phrase) VALUES ("Monsanto");
INSERT INTO phrases (phrase,report) VALUES ("AnSq", 0);
INSERT INTO phrases (phrase) VALUES ("Huxley");
INSERT INTO phrases (phrase) VALUES ("Brave New World");

DROP TABLE IF EXISTS comment_phrase;
CREATE TABLE comment_phrase (
	comment  INTEGER NOT NULL REFERENCES comments (id),
	phrase   INTEGER NOT NULL REFERENCES phrases (id),
	unquoted INTEGER NOT NULL DEFAULT 0,
	quoted   INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY (comment, phrase)
);

DROP TABLE IF EXISTS subreddits;
CREATE TABLE subreddits (
	id           INTEGER PRIMARY KEY,
	id_b36       TEXT,
	display_name TEXT,
	subscribers  INTEGER
);

DROP VIEW IF EXISTS comments_basic;
CREATE VIEW comments_basic AS
SELECT id, author, subreddit, link_title, body, score, ups, downs, permalink
FROM comments
ORDER BY id DESC;

DROP VIEW IF EXISTS comment_phrase_view;
CREATE VIEW comment_phrase_view AS
SELECT comment, author, subreddit, link_title, body, phrases.phrase, (unquoted+quoted) AS total, unquoted, quoted, permalink
FROM comment_phrase
JOIN phrases ON comment_phrase.phrase == phrases.id
JOIN comments ON comments.id == comment_phrase.comment
WHERE total != 0
ORDER BY comment DESC;

DROP VIEW IF EXISTS phrases_by_subreddit;
CREATE VIEW phrases_by_subreddit AS
SELECT phrases.phrase, comments.subreddit, sum(unquoted+quoted) AS count, subscribers, CAST (sum(unquoted+quoted) AS FLOAT)/(CAST (subreddits.subscribers AS FLOAT)/100000) AS per_100000
FROM phrases
JOIN comment_phrase ON phrases.id == comment_phrase.phrase
JOIN comments ON comment_phrase.comment == comments.id
LEFT OUTER JOIN subreddits ON comments.subreddit == subreddits.display_name
GROUP BY phrases.phrase, comments.subreddit
ORDER BY count DESC;

DROP VIEW IF EXISTS phrase_counts;
CREATE VIEW phrase_counts AS
SELECT phrases.phrase, sum(unquoted+quoted) AS count
FROM phrases
JOIN comment_phrase ON phrases.id == comment_phrase.phrase
GROUP BY phrases.phrase
ORDER BY count DESC;

DROP VIEW IF EXISTS subreddit_counts;
CREATE VIEW subreddit_counts AS
SELECT comments.subreddit, sum(unquoted+quoted) AS count, subscribers, CAST (sum(unquoted+quoted) AS FLOAT)/(CAST (subreddits.subscribers AS FLOAT)/100000) AS per_100000
FROM phrases
JOIN comment_phrase ON phrases.id == comment_phrase.phrase
JOIN comments ON comments.id == comment_phrase.comment
LEFT OUTER JOIN subreddits ON comments.subreddit == subreddits.display_name
GROUP BY comments.subreddit
ORDER BY per_100000 DESC;

DROP VIEW IF EXISTS user_counts;
CREATE VIEW user_counts AS
SELECT comments.author, sum(unquoted+quoted) AS count
FROM phrases
JOIN comment_phrase ON phrases.id == comment_phrase.phrase
JOIN comments ON comments.id == comment_phrase.comment
GROUP BY comments.author
ORDER BY count DESC;
