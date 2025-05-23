"""
[TODO] make DBHandler work, for at least MongoDB services.
Each game should be recorded in a collection named game.gamename
Write all docuements in format:
{name:name, index: index, timestamp: time, event:event, msg:message}
"""
import random
import os
import json
from bson import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection

IS_CONN = False
dbs = {}
client = None


def prepare_db(db_host: str = "mongodb://127.0.0.1",
               db_port: int = 27017,
               db_name="TradeCraft"):
    global IS_CONN, client, dbs
    # connect to the MongoDB serve
    client = MongoClient(str(db_host), int(db_port), connectTimeoutMS=5000)
    # client = MongoClient()

    dbs = {}
    # for key in DB_SPEC:
    #     dbs[key] = client[key]

    try:
        print("::: Checking MongoDB Connection to", f"{db_name}:{db_host}")
        # x = dbs[random.choice(list(DB_SPEC.keys()))].list_collection_names()
        IS_CONN = True
        print("::: MongoDB Connected")
    except Exception:
        IS_CONN = False
        print("::: MongoDB NOT Connected")
        return None

    collection_names = client[db_name].list_collection_names()
    return client[db_name], collection_names

def convert_document(document):
    for key, value in document.items():
        if isinstance(value, ObjectId):
            document[key] = str(value)
    return document

def parse_collection_name(collection_name: str) -> tuple[str, str]:
    """
    Parse a collection name into a database name and a collection name.
    """
    parts = collection_name.split("_")
    if len(parts) < 2:
        return ""
    elif len(parts[1]) == 8:
        return parts[1]
    return ""


def log_db_to_json(db: Collection,
                   collection_name: str,
                   prefix="./json_logs/") -> tuple:
    """
    Log a database to a JSON file.
    """

    if not IS_CONN:
        return []
    gamename = parse_collection_name(collection_name)
    os.makedirs(os.path.join(prefix, gamename), exist_ok=True)
    with open(os.path.join(prefix, gamename, f"{collection_name}.json"),
              "w") as f:
        json.dump([convert_document(x) for x in db[collection_name].find({})],
                  f,
                  default=str,
                  indent=4)

    return gamename, collection_name



def log_db_all(db: Collection, collection_names, log: str = "") -> dict:
    """
    Log all databases to a JSON file.
    """
    os.makedirs("json_logs", exist_ok=True)

    if not IS_CONN:
        return []

    games = {}
    for collection_name in collection_names:
        gamename, filename = log_db_to_json(db, collection_name)
        if gamename in games:
            games[gamename].append(filename)
        else:
            games[gamename] = [filename]

    if log != "":
        with open(log, "w") as f:
            json.dump(games, f, indent=4)
    print([(games, filenames) for games, filenames in games.items()
           if len(filenames) != 3])
    return games


if __name__ == "__main__":
    db, collection_names = prepare_db()
    log_db_all(db, collection_names, "json_logs/games.json")
    print(client["TradeCraft"].list_collection_names())
