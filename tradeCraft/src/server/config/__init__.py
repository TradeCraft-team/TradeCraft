from .game import *
# Currently we use python to store configs,
# We may change it to a yaml loader later.
# I have one used in CivRealm project before.
# DB

DB_NAME = "MongoDB"
DB_HOST = "127.0.0.1"
DB_PORT = 27017
DB_SPEC = {"TradeCraft": {}, "LittleAlchemy2": {}}

LOG_FORMAT = "json"
