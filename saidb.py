import apsw
import time

create_sql = """

-- textchunks (articles, forum comments, a handful of chat lines, parts of a very long text)
CREATE TABLE IF NOT EXISTS chunks (
  id INTEGER PRIMARY KEY AUTOINCREMENT, -- higher number means more recently added chunk
  ctime FLOAT,    -- creation time of this db entry (not to be used for sorting)
  module INTEGER  -- module id that can fetch and parse the content
);

-- word lookup table (only words that were individually clicked on, entered or accepted by the user)
CREATE TABLE IF NOT EXISTS words (
  id INTEGER PRIMARY KEY,
  name VARCHAR
);
CREATE INDEX IF NOT EXISTS words_name_index ON words (name);

-- log every time an article is displayed
CREATE TABLE IF NOT EXISTS shown (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  chunk INTEGER,
  time FLOAT,
  mode INTEGER -- shownHeadline | shownFulltext | articleTagged | articleRated
);
CREATE INDEX IF NOT EXISTS shown_chunk_index ON shown (chunk);

-- article tags (or keywords) that were entered or acknowledged by the user
CREATE TABLE IF NOT EXISTS tags (
  chunk INTEGER,    -- the textchunk being tagged
  word INTEGER,     -- word clicked on (or entered by user, or auto-substituted)
  rank INTEGER      -- rank (1 for the first, etc)
);
CREATE INDEX IF NOT EXISTS tags_chunk_index ON tags (chunk);
-- maybe create index on words?

CREATE TABLE IF NOT EXISTS ratings (
  word INTEGER,         -- the word being rated
  chunk INTEGER,        -- the textchunk that was active while rating (representing the context in which the rating occured)
  rating FLOAT,
  mtime FLOAT           -- last modification (could be used to give less importance to old ratings)
);
CREATE INDEX IF NOT EXISTS ratings_word_index ON ratings (word);

-- TODO: read status of an article (mark as unread; mark for later reading; mark as special...?)
--       (implicit marks when following an article url, etc.)

"""

shownModeDict = {'headline':100, 'fulltext':200, 'tagged':300, 'rated':400, 'linkfollowed':500}
moduleNames = ['rss']

class SAIDB:
    # for shown.mode
    # the chunk.module integer refers to the index of this list

    def __init__(self, dbfile='data/sai.db'):
        self.dbfile = dbfile
        self.con = self.connection()

    def close(self):
        self.con.close()

    def connection(self):
        con = apsw.Connection(self.dbfile)
        con.setbusytimeout(5000)
        cur = con.cursor()
        cur.execute(create_sql)
        return con

    def getNewWordId(self, word):
        word = word.lower()
        cur = self.con.cursor()
        cur.execute("SELECT id FROM words WHERE name = ?", (word,))
        try:
            return cur.next()[0]
        except StopIteration: 
            cur.execute("INSERT INTO words(name) VALUES (?)", (word,))
            return self.con.last_insert_rowid()
    
    def getChunk(self, chunk_id):
        int(chunk_id) # make sure we get no tuple
        cur = self.con.cursor()
        cur.execute("SELECT module FROM chunks WHERE id = ?", (chunk_id,))
        module = cur.next()[0]
        module = __import__(moduleNames[module])
        return module.Chunk(self, chunk_id)

    def updateSources(self):
        for name in moduleNames:
            module = __import__(name)
            module.update(self)


class Chunk:
    """
    Base class for textchunks.
    There are specialized classes in all modules (for rss, mail, ...)
    """
    def __init__(self, saidb, chunk_id):
        self.saidb = saidb
        self.id = chunk_id
        self.update()
        self.tagsModified = False

    def update(self):
        cur = self.saidb.con.cursor()
        # tags
        cur.execute("""
        SELECT w.name FROM tags AS t, words AS w
        WHERE t.chunk = ? AND t.word = w.id
        ORDER BY t.rank
        """, (self.id,))
        self.tags = [x[0] for x in cur]

    def shown(self, mode):
        mode = shownModeDict[mode]
        cur = self.saidb.con.cursor()
        cur.execute("INSERT INTO shown(chunk, time, mode) VALUES (?, ?, ?)", (self.id,time.time(),mode))

    def getCtime(self):
        cur = self.saidb.con.cursor()
        cur.execute("SELECT ctime FROM chunks WHERE id = ?", (self.id,))
        return cur.next()[0]
        
    def setTags(self, tags):
        cur = self.saidb.con.cursor()
        cur.execute("BEGIN")
        cur.execute("DELETE FROM tags WHERE chunk = ?", (self.id,))
        for rank, word in enumerate(tags):
            word_id = self.saidb.getNewWordId(word)
            cur.execute("INSERT INTO tags(chunk, word, rank) VALUES (?, ?, ?)", (self.id, word_id, rank))
        if not self.tagsModified:
            self.shown('tagged')
            self.tagsModified = True
        cur.execute("COMMIT")
        self.tags = tags[:]

    def setRating(self, word, rating):
        cur = self.saidb.con.cursor()
        cur.execute("BEGIN")
        word_id = self.saidb.getNewWordId(word)
        cur.execute("DELETE FROM ratings WHERE word = ? AND chunk = ?", (word_id, self.id))
        cur.execute("INSERT INTO ratings(word, chunk, rating, mtime) VALUES (?, ?, ?, ?)", (word_id, self.id, rating, time.time()))
        cur.execute("COMMIT")
