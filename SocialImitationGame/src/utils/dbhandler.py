"""
[TODO] make DBHandler work, for at least MongoDB services.
Each game should be recorded in a collection named game.gamename
Write all docuements in format:
{name:name, index: index, timestamp: time, event:event, msg:message}
"""
import random

from pymongo import MongoClient
from pymongo.collection import Collection
from .str_print import print

DB_NAME = "MongoDB"
DB_HOST = "127.0.0.1"
DB_PORT = 27017
DB_SPEC = {"TradeCraft": {}, "LittleAlchemy2": {}}

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


def save_log_to_db(collection, msg):
    """
    Save `message` to database in `collection`
    """

    if not IS_CONN:
        print("Database is NOT CONNECTED!", s=1)
        return

    db_col = dbs["TradeCraft"][collection]
    db_col.insert_one(msg)
