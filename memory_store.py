from datetime import datetime
try:
    from backend.mongo_client import db
except ImportError:
    from mongo_client import db
from bson import ObjectId
import secrets

def save_memory(team_name: str, mem_type: str, data: dict):
    if db is None:
        print("❌ Error: Database not connected. Cannot save memory.")
        return None

    timestamp = datetime.utcnow()

    # 1. TEAM Collection
    if mem_type.upper() == "TEAM":
        collection = db["teams"]
        team_doc = {
            "team_name": team_name,
            "problem_statement": data.get("problem_statement", ""),
            "hackathon": {
                "start_time": timestamp,
                "duration_hours": data.get("duration_hours", 24)
            },
            "created_at": timestamp
        }
        result = collection.insert_one(team_doc)
        return result.inserted_id
        
    # 2. MEMBER Collection (Profile Only)
    elif mem_type.upper() == "MEMBER":
        collection = db["members"]
        # Generate unique chat token
        chat_token = secrets.token_urlsafe(16)
        
        member_doc = {
            "token": chat_token,
            "team_name": team_name,
            "name": data.get("name", ""),
            "role": data.get("role", "Team Member"),
            "email": data.get("email", ""), # Storing email/gmail
            "phone": data.get("phone", ""),
            "skills": data.get("skills", []),
            "joined_at": timestamp,
            "last_active_at": timestamp
        }
        collection.insert_one(member_doc)

        # Initialize empty Member Chat
        db["member_chat"].insert_one({
            "token": chat_token,
            "member_name": data.get("name", ""),
            "messages": [], # Raw chat logs
            "last_updated": timestamp
        })

        # Initialize empty Goal (Optional, or created later)
        # We can create a default goal if provided
        
        return chat_token
    
    # 3. GOALS Collection
    elif mem_type.upper() == "GOAL":
        collection = db["Active_goals"]
        goal_doc = {
            "token": data.get("token"), # Link to member
            "member_name": data.get("member_name"),
            "goal_text": data.get("goal_text"),
            "status": "active", # active, completed
            "time_start": timestamp,
            "created_at": timestamp
        }
        result = collection.insert_one(goal_doc)
        return result.inserted_id

    # 4. INSTRUCTION Collection
    elif mem_type.upper() == "INSTRUCTION":
        collection = db["instruction_team"]
        instruction_doc = {
            "manager_token": data.get("manager_token"),
            "target_member_token": data.get("target_member_token", "all"), # "all" or specific token
            "instruction_text": data.get("instruction_text"),
            "active": True,
            "created_at": timestamp
        }
        result = collection.insert_one(instruction_doc)
        return result.inserted_id

    # Reference to Generic Memory
    else:
        collection = db["generic_memory"]
        doc = {
            "team_name": team_name,
            "type": mem_type,
            "data": data,
            "created_at": timestamp
        }
        result = collection.insert_one(doc)
        return result.inserted_id