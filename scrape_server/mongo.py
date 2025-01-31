from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any
from pydantic import BaseModel
from bson.objectid import ObjectId
import env

class MongoDBClient:
    def __init__(self, db_name: str, collection_name: str):
        self.uri = f"mongodb+srv://{env.mongo_username}:{env.mongo_pass}@cluster0.82dnw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        self.db_name = db_name
        self.col_name = collection_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.collection = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.uri, serverSelectionTimeoutMS=5000)
            # Verify connection
            await self.client.server_info()
            self.db = self.client[self.db_name]
            self.collection = self.db[self.col_name]
            print("Connected to MongoDB")
        except Exception as e:
            print(f"Could not connect to MongoDB: {e}")
            raise

    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("Closed MongoDB connection")

    async def get_document(self, filter_dict: Dict):
        """Get a single document from collection"""
        return await self.collection.find_one(filter_dict)

    async def get_documents(self, filter_dict: Dict):
        """Get multiple documents from collection"""
        cursor = self.collection.find(filter_dict)
        return await cursor.to_list(length=None)

    async def insert_document(self, document: Dict):
        """Insert a single document into collection"""
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def update_document(self, filter_dict: Dict, update_dict: Dict):
        """Update a single document in collection"""
        result = await self.collection.update_one(filter_dict, {"$set": update_dict})
        return result.modified_count

    async def delete_document(self, filter_dict: Dict):
        """Delete a single document from collection"""
        result = await self.collection.delete_one(filter_dict)
        return result.deleted_count
