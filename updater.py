#!/usr/bin/env python
#encoding: utf8
from saidb import SAIDB

def populate():
    import populate
    populate.populate(saidb)

saidb = SAIDB()
try:
    populate()
    saidb.updateSources()

finally:
    saidb.close()

import evaluator

