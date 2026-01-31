from datetime import datetime
from mongo_client import db
import uuid
import secrets

def save_memory(team_name: str, mem_type: str, data: dict):
    # Simplified structure: team_details + members collections
    if mem_type.upper() == "TEAM":
        collection = db["team_details"]
        # Create team document with simplified schema
        team_doc = {
            "_id": f"TEAM_{str(uuid.uuid4().hex[:4]).upper()}",
            "team_name": team_name,
            "problem_statement": data.get("problem_statement", ""),
            "hackathon": {
                "start_time": datetime.utcnow(),
                "duration_hours": data.get("duration_hours", 24)
            },
            "members_count": 0,  # Will be updated when members are added
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        }
        result = collection.insert_one(team_doc)
        return result.inserted_id
        
    elif mem_type.upper() == "MEMBER":
        collection = db["members"]
        # Create member document with simplified schema
        member_id = f"MEM_{str(uuid.uuid4().hex[:4]).upper()}"
        chat_token = secrets.token_urlsafe(16)  # Generate unique chat token
        member_doc = {
            "_id": member_id,  # MongoDB ObjectId
            "member_id": member_id,  # String ID for frontend lookup
            "team_id": data.get("team_id", "TEAM_UNKNOWN"),
            "member_index": data.get("member_index", 1),
            "is_leader": data.get("is_leader", False),
            "name": data.get("name", ""),
            "team_name": data.get("team_name", ""),
            "role": data.get("role", "Team Member"),
            "skills": data.get("skills", []),
            "chat_history": [],
            "chat_token": chat_token,  # Unique token for chat access
            "created_at": datetime.utcnow(),
            "last_active_at": datetime.utcnow()
        }
        result = collection.insert_one(member_doc)
        return result.inserted_id
        
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