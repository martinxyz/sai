con = sqlite.connect(dbfile)

def create_tables(con):
    con.execute("""
    CREATE TABLE items (
      id INTEGER PRIMARY KEY,
      name VARCHAR,
      creation_time FLOAT
    )""")

    con.execute("""
    CREATE TABLE texts (
      id INTEGER PRIMARY KEY,
      source INTEGER,
      text VARCHAR,
      info VARCHAR,
      url  VARCHAR
    )""")

    con.execute("""
    CREATE TABLE sources (
      id INTEGER PRIMARY KEY,
      name VARCHAR,
      url VARCHAR,
      type VARCHAR,
      check_time FLOAT
    )""")

    con.execute("""
    CREATE TABLE relations (
      src INTEGER,
      dst INTEGER,
      type VARCHAR,
      strength FLOAT
    )
    """)

    con.execute("CREATE INDEX items_name_index ON items (name)")
    con.execute("CREATE INDEX relations_src_index ON relations (src)")

def add_feed(con, name, url, type='rss'):
    i = con.execute("SELECT MAX(id) + 1 FROM items").fetchall()[0][0]
    con.execute("INSERT INTO items VALUES (?, 'SOURCE', ?)", (i, time.time()))
    con.execute("INSERT INTO sources VALUES (?, ?, ?, ?, 0.0)", (i, name, url, type))

