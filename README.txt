sai (subscribe and ignore)

This is an RSS reader with the special ability that you can right-click
any word and directly assign a score to it.

The idea is that you can subscribe to hundred of news sources that you have
mild interest in, and ignore most posts until something interesting pops up.

Features:
- gtk GUI, can read one article at a time
- it just presents you the next unread article with the highest score
- score vs news tradeoff: old articles get lower score
- feeds that are quiet are checked less frequently
- open urls in external browser

This is unpolished software. I do use it weekly and it works. Maybe it
also works for you if you're lucky.

Usage:
edit populate.py and add your rss sources
run ./updater.py (run again if there is an error, it will skip the error feed) 
run ./reader.py
Start reading... right-click words to assign score.
run ./updater.py again to recalculate the scores.

Martin Renold, 2009

