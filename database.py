import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
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
            # Conexão segura com MongoDB
            self.client = MongoClient(settings.MONGO_URL, tls=True, tlsAllowInvalidCertificates=True)
            self.db = self.client[settings.DB_NAME]
            self.players_collection = self.db[settings.PLAYERS_COLLECTION]

mongo_db = MongoDB()

def get_db():
    try:
        if not mongo_db.client:
            mongo_db.connect()
        yield mongo_db
    finally:
        # Mantém a conexão aberta enquanto app estiver rodando
        pass
