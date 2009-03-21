import random, time, math
import saidb, utils
import os
os.nice(10)

create_sql = """
CREATE TABLE IF NOT EXISTS evaluator_scores (
      id INTEGER PRIMARY KEY, -- chunkid
      score FLOAT,
      mtime FLOAT,
      report VARCHAR
    );
CREATE TABLE IF NOT EXISTS evaluator_index (
      word   INTEGER, -- wordid
      chunk  INTEGER, -- chunkid
      pos    INTEGER  -- number of words preceding this one (becomes inaccurate if utils.textsplit is modified)
    );
CREATE INDEX IF NOT EXISTS evaluator_index_word_index ON evaluator_index (word);
"""

def evaluate(db, chunk):
    cur = db.con.cursor()
    #print '---'
    #print 'evaluating chunk', chunk.id
    #print chunk.text
    report = ''
    report_list = []
    total_rating = 0.0
    total_weight = 0.0
    found = {}
    for word in utils.textsplit(chunk.text):
        word = word.lower()
        wordid = db.getNewWordId(word)
        cur.execute('select sum(r.rating*r.rating*r.rating) from ratings as r where r.word = ?', (wordid,))
        try:
            rating = cur.next()[0]
        except StopIteration:
            rating = 0.0
        if rating:
            if word not in found:
                found[word] = 1
                
                # calculate score for this word
                cur.execute('select count(*) from (select count(*) from evaluator_index where word = ? group by chunk)', (wordid,))
                wordfreq = cur.next()[0] 
                cur.execute('select count(*) from chunks')
                N = cur.next()[0] 
                idf = math.log(float(N+1)/float(wordfreq+1))

                weight = idf
                report_list.append((weight, '%s (%+d*%3.1f, wordfreq %d)\n' % (word, rating, idf, wordfreq)))
                total_rating += rating*weight
                total_weight += weight

    # bias for texts without / with few rated words
    total_rating += 0.0
    total_weight += 30.0

    age = time.time() - chunk.getCtime()
    age_factor = math.exp(-age/(60.0*60*24*300))

    report += 'Age Factor: %1.6f (%s)\n' % (age_factor, utils.age2str(age))
    total_rating /= total_weight
    total_rating *= age_factor
    report += 'Total Score: %3.3f\n' % total_rating
    report_list.sort()
    report_list.reverse()
    report += ''.join([s for score, s in report_list])
    print '---'
    print report
    cur.execute('BEGIN')
    cur.execute('DELETE FROM evaluator_scores WHERE id = ?', (chunk.id,))
    cur.execute('INSERT INTO evaluator_scores(id, mtime, score, report) VALUES (?, ?, ?, ?)', (chunk.id, time.time(), total_rating, report))
    cur.execute('COMMIT')

def index(db, chunk):
    print 'indexing', chunk
    cur = db.con.cursor()
    cur.execute('BEGIN')
    cur = db.con.cursor()
    cur.execute('DELETE FROM evaluator_index WHERE chunk = ?', (chunk.id,))
    for pos, word in enumerate(utils.textsplit(chunk.text)):
        word = word.lower()
        wordid = db.getNewWordId(word)
        cur.execute('INSERT INTO evaluator_index(word, chunk, pos) VALUES (?, ?, ?)', (wordid, chunk.id, pos))
    cur.execute('COMMIT')

db = saidb.SAIDB()
cur = db.con.cursor()
cur.execute(create_sql)

#cur.execute('SELECT id FROM chunks')
#for chunk_id in list(cur):
#    chunk = db.getChunk(chunk_id[0])
#    index(db, chunk)

cur.execute('SELECT id FROM chunks') # WHERE not evaluated
#chunk_id = random.choice(list(cur))
for chunk_id in list(cur):
    chunk = db.getChunk(chunk_id[0])
    evaluate(db, chunk)

db.close()
