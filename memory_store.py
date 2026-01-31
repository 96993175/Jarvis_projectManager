from datetime import datetime
from mongo_client import db
from bson import ObjectId
import secrets

def save_memory(team_name: str, mem_type: str, data: dict):
    """
    Simplified token-based storage
    - Teams collection: team documents
    - Members collection: member documents with tokens
    - No more member_id/team_id confusion
    """
    if mem_type.upper() == "TEAM":
        # Create team document
        team_doc = {
            "_id": ObjectId(),
            "team_name": team_name,
            "problem_statement": data.get("problem_statement", ""),
            "duration_hours": data.get("duration_hours", 24),
            "created_at": datetime.utcnow()
        }
        result = db["teams"].insert_one(team_doc)
        return result.inserted_id
        
    elif mem_type.upper() == "MEMBER":
        # Generate unique token for this member
        token = secrets.token_urlsafe(16)
        
        # Create member document with token
        member_doc = {
            "_id": ObjectId(),
            "token": token,  # 🔑 Only identifier exposed externally
            "team_id": data.get("team_id"),
            "name": data.get("name", ""),
            "role": data.get("role", "Team Member"),
            "skills": data.get("skills", []),
            "chat_history": [],
            "created_at": datetime.utcnow()
        }
        db["members"].insert_one(member_doc)
        return token  # Return token for frontend linking
        
    else:
        # Generic storage
        doc = {
            "team_name": team_name,
            "type": mem_type,
            "data": data,
            "created_at": datetime.utcnow()
        }
        result = db["generic_memory"].insert_one(doc)
        return result.inserted_id