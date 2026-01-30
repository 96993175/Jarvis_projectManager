from pymongo import MongoClient
import os

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://krushimitra14_db_user:uSS5SI0k3eiPG4a6@teamdb.hdo4ebt.mongodb.net/?appName=TeamDB"
)

client = MongoClient(MONGO_URI)
db = client["jarvis_memory"]  # Single database for all memory