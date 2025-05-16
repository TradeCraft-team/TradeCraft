"""
[TODO] make DBHandler work, for at least MongoDB services.
Each game should be recorded in a collection named game.gamename
Write all docuements in format:
{name:name, index: index, timestamp: time, event:event, msg:message}
"""
import random
from .config import (DB_NAME, DB_HOST, DB_PORT, DB_SPEC)
from pymongo import MongoClient
from pymongo.collection import Collection


client = MongoClient(str(DB_HOST), int(DB_PORT))
# client = MongoClient()

dbs = {}
for key in DB_SPEC:
    dbs[key] = client[key]

DB_COLLECTIONS = {}
# DB_SPEC = {"dba": [collection1, collection2,...], ...}
for key, val in DB_SPEC.items():
    for col in val:
        DB_COLLECTIONS[f"{key}.{col}"] = dbs[key][col]


try:
    print("::: Checking MongoDB Connection to", f"{DB_NAME}:{DB_HOST}")
    x = dbs[random.choice(list(DB_SPEC.keys()))].list_collection_names()
    IS_CONN = True
    print("::: MongoDB Connected")
except Exception:
    IS_CONN = False
    print("::: MongoDB NOT Connected")
