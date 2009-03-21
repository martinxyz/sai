#!/usr/bin/env python
# encoding: utf8
"""
Module for RSS and Atom feeds (anything that feedparser can handle)
"""
import saidb
import os, time, re, traceback
import feedparser

HOUR = 60*60.0
DAY = 24*HOUR
max_check_interval = 60*DAY
min_check_interval = 0.5*HOUR

create_sql = """
CREATE TABLE IF NOT EXISTS rss_sources (
      id INTEGER PRIMARY KEY,
      name VARCHAR,
      url VARCHAR,
      check_interval FLOAT DEFAULT 0.0, -- how often to check (dynamically adapted)
      check_time FLOAT DEFAULT 0.0,     -- last time a fetch was started
      fetch_time FLOAT DEFAULT 0.0      -- last time a fetch was successfully completed
    );
CREATE TABLE IF NOT EXISTS rss_articles (
      id INTEGER PRIMARY KEY, -- same as textchunk.id
      source INTEGER,
      title VARCHAR,
      text VARCHAR,
      url VARCHAR
    );
"""

class Chunk(saidb.Chunk):
    def __init__(self, db, chunk_id):
        saidb.Chunk.__init__(self, db, chunk_id)
        cur = db.con.cursor()
        cur.execute("SELECT text, title, url FROM rss_articles WHERE id = ?", (self.id,))
        self.content, self.title, self.url = cur.next()
        self.text = self.title + '\n\n' + self.content 
        # strip markup (for now)
        self.text = re.sub(r'<img[^>]*>', '[img] ', self.text)
        self.text = re.sub(r'<[^>]*>', '', self.text)
        self.text = self.text.replace('  ', ' ')
        self.text = self.text.replace('  ', ' ')
        self.text = self.text.replace('\n\n\n', '\n\n')
        self.text = self.text.replace('\n\n\n', '\n\n')
        
def add(db, name, url):
    cur = db.con.cursor()
    cur.execute(create_sql)
    cur.execute("SELECT name FROM rss_sources WHERE url=?", (url,))
    try:
        trash = cur.next()
    except:
        print 'adding', name, url
        cur.execute("INSERT INTO rss_sources(name, url, check_time, fetch_time, check_interval) VALUES (?, ?, 0, 0, 0)", (name, url))

def update(db):
    print 'updating rss...'
    cur = db.con.cursor()
    q = cur.execute
    q(create_sql)
    while True:
        q("BEGIN")
        t = time.time()
        q("SELECT id, name, url FROM rss_sources WHERE fetch_time + check_interval < ? AND check_time + ? < ?", (t,min_check_interval,t))
        try:
            source_id, name, url = cur.next()
        except StopIteration:
            # all finished
            q("ROLLBACK")
            print 'updating rss finished.'
            return
        q("UPDATE rss_sources SET check_time = ? WHERE id = ?", (t,source_id))
        q("COMMIT")

        print 'Updating', name, 'feed...'
        try:
            # now the time-consuming call
            feed = feedparser.parse(url)

            q("BEGIN")
            new = 0
            duplicates = 0
            for entry in feed.entries:
                url  = entry.link
                text = unicode(entry.description)
                title = unicode(entry.title)

                # FIXME: this ignores articles with known title.
                # Cannot compare text because of feedburner variation.
                # THIS SCREWS UP READING GOOGLE NEWSGROUP FEEDS!!!
                q("SELECT id FROM rss_articles WHERE source = ? AND title = ?", (source_id, title))
                try:
                    cur.next()
                    duplicates += 1
                except StopIteration:
                    q("INSERT INTO chunks(ctime, module) values (?, ?)", (time.time(), saidb.moduleNames.index('rss')))
                    chunk_id = db.con.last_insert_rowid()
                    q("INSERT INTO rss_articles(id, source, title, text, url) VALUES (?, ?, ?, ?, ?)", (chunk_id, source_id, title, text, url))
                    #con.execute("INSERT INTO items(id, name, creation_time) VALUES (?, 'TEXT', ?)", (new_id, time.time()))
                    # TODO: update article db
                    new += 1
        except Exception, e:
            traceback.print_exc()

        # adapt check_interval
        q("SELECT check_interval, ? - fetch_time FROM rss_sources WHERE id = ?", (t, source_id))
        check_interval, real_interval = [float(x) for x in cur.next()]
        assert real_interval >= check_interval
        if new == 0:
            guessed_interval = real_interval * 2
        else:
            guessed_interval = real_interval / new
        check_interval = 0.5 * check_interval + 0.5 * guessed_interval
        if check_interval > max_check_interval: check_interval = max_check_interval
        if check_interval < min_check_interval: check_interval = min_check_interval
        q("UPDATE rss_sources SET check_interval = ? WHERE id = ?", (check_interval,source_id))

        q("UPDATE rss_sources SET fetch_time = ? WHERE id = ?", (time.time(),source_id))
        q("COMMIT")
        print 'done', duplicates, 'duplicates', new, 'new items'
