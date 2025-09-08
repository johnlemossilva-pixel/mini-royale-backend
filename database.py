import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGO_URL = os.getenv("MONGO_URL")
    DB_NAME = os.getenv("DB_NAME", "mini_royale_db")
    PLAYERS_COLLECTION = "players"

settings = Settings()

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None
        self.players_collection = None
    
    def connect(self):
        if not self.client:
            self.client = MongoClient(settings.MONGO_URL)
            self.db = self.client[settings.DB_NAME]
            self.players_collection = self.db[settings.PLAYERS_COLLECTION]

mongo_db = MongoDB()
mongo_db.connect()
