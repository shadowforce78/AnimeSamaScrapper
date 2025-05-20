import pymongo
import dotenv
import os

dotenv.load_dotenv()

URL = os.getenv("MONGO_URL")