from datetime import datetime
from mongo_client import db
from bson import ObjectId
import secrets

def save_memory(team_name: str, mem_type: str, data: dict):
    if db is None:
        print("❌ Error: Database not connected. Cannot save memory.")
        return None

    # Simplified structure: teams + members collections
    if mem_type.upper() == "TEAM":
        collection = db["teams"]
        # Create team document with simplified schema
        team_doc = {
            "team_name": team_name,
            "problem_statement": data.get("problem_statement", ""),
            "hackathon": {
                "start_time": datetime.utcnow(),
                "duration_hours": data.get("duration_hours", 24)
            },
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
            "token": chat_token,  # Unique token for chat access
            "team_name": team_name,  # Direct team name reference
            
            "name": data.get("name", ""),
            "role": data.get("role", "Team Member"),
            "phone": data.get("phone", ""),
            "gmail": data.get("email", ""),  # Using gmail field as requested
            "skills": data.get("skills", []),
            
            "chat_history": [],
            "joined_at": datetime.utcnow(),
            "last_active_at": datetime.utcnow()
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