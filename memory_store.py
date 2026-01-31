from datetime import datetime
from mongo_client import db
from bson import ObjectId
import secrets

def save_memory(team_name: str, mem_type: str, data: dict):
    # Simplified structure: teams + members collections
    if mem_type.upper() == "TEAM":
        collection = db["teams"]
        # Create team document with simplified schema
        team_doc = {
            "_id": ObjectId(),  # MongoDB ObjectId
            "team_name": team_name,
            "problem_statement": data.get("problem_statement", ""),
            "duration_hours": data.get("duration_hours", 24),
            "created_at": datetime.utcnow()
        }
        result = collection.insert_one(team_doc)
        return result.inserted_id
        
    elif mem_type.upper() == "MEMBER":
        collection = db["members"]
        # Generate unique chat token
        chat_token = secrets.token_urlsafe(16)
        
        # Create member document with simplified schema
        member_doc = {
            "_id": ObjectId(),  # MongoDB ObjectId
            "token": chat_token,  # Unique token for chat access
            "team_id": data.get("team_id"),  # Reference to team ObjectId
            "name": data.get("name", ""),
            "role": data.get("role", "Team Member"),
            "skills": data.get("skills", []),
            "chat_history": [],
            "created_at": datetime.utcnow()
        }
        result = collection.insert_one(member_doc)
        # Return the token, not the MongoDB ObjectId
        return chat_token
        
    else:
        # For other memory types, use a simple generic collection
        collection = db["generic_memory"]
        doc = {
            "team_name": team_name,
            "type": mem_type,
            "data": data,
            "created_at": datetime.utcnow()
        }
        result = collection.insert_one(doc)
        return result.inserted_id