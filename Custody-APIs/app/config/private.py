from pymongo import MongoClient

# MongoDB connection URI
uri = "mongodb://gewgawrav:catax1234@concur.cumulate.live/"

# Create a new client and connect to the server
client = MongoClient(uri)

# Access the specific database
db = client["custody-database"]

# Access the specific collection
user_wallet_details = db["user_wallet_details"]
signed_txn_collection = db["signed_txn_collection"]