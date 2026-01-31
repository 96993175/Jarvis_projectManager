from datetime import datetime
from mongo_client import db
import uuid

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
        # Create member document with flat schema
        from bson import ObjectId
        member_doc = {
            "_id": str(ObjectId()),
            "team_id": data.get("team_id", "TEAM_UNKNOWN"),
            "name": data.get("name", ""),
            "role": data.get("role", "Team Member"),
            "skills": data.get("skills", []),
            "chat_history": [],
            "created_at": datetime.utcnow()
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