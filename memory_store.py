from datetime import datetime
from mongo_client import db

def save_memory(team_name: str, mem_type: str, data: dict):
    # Use standardized collections inside jarvis_memory database
    collection_map = {
        "TEAM": "teams",
        "MEMBER": "members", 
        "TASK": "tasks",
        "SYSTEM": "system",
        "EVENT": "events",
        "CONVERSATION": "conversations",
        "HABIT": "habits",
        "CONVERSATION_SNAPSHOT": "conversation_snapshots",
        "AUTOMATION_LOG": "automation_logs"
    }
    
    collection_name = collection_map.get(mem_type.upper(), "miscellaneous")
    collection = db[collection_name]

    # Special handling for TEAM type to match the required schema
    if mem_type.upper() == "TEAM":
        from datetime import datetime as dt
        import uuid
        
        # Create the team document with the specified schema
        team_doc = {
            "_id": f"TEAM_{str(uuid.uuid4().hex[:4]).upper()}",
            "problem_statement": data.get("problem_statement", ""),
            "hackathon": {
                "start_time": dt.utcnow().isoformat() + "Z",
                "duration_hours": data.get("duration_hours", 24)
            },
            "summary": {
                "goal": "",
                "architecture": "",
                "tech_stack": []
            },
            "last_updated": dt.utcnow().isoformat() + "Z"
        }
        
        collection.insert_one(team_doc)
    elif mem_type.upper() == "MEMBER":
        from datetime import datetime as dt
        import uuid
        
        # Create the member document with the specified schema
        member_doc = {
            "_id": f"MEM_{str(uuid.uuid4().hex[:2]).upper()}",
            "team_id": f"TEAM_{str(uuid.uuid4().hex[:4]).upper()}",
            "identity": {
                "name": data.get("name", ""),
                "role": data.get("role", "Team Member"),
                "skills": data.get("skills", []),
                "experience_level": "intermediate"
            },
            "preferences": {
                "communication": "whatsapp",
                "work_style": "deep_focus",
                "reminder_tolerance": "strict"
            },
            "status": {
                "current_task_id": None,
                "availability": "active",
                "last_active_at": dt.utcnow().isoformat() + "Z",
                "idle_minutes": 0
            },
            "performance": {
                "tasks_completed": 0,
                "tasks_delayed": 0,
                "avg_response_minutes": 0
            },
            "meta": {
                "joined_at": dt.utcnow().isoformat() + "Z",
                "link_token_hash": "•••",
                "is_leader": False
            }
        }
        
        collection.insert_one(member_doc)
    elif mem_type.upper() == "HABIT":
        from datetime import datetime as dt
        import uuid
        
        # Create the habit document with the specified schema
        habit_doc = {
            "_id": f"HABIT_MEM_{str(uuid.uuid4().hex[:2]).upper()}",
            "member_id": data.get("member_id", "MEM_01"),
            "team_id": data.get("team_id", "TEAM_92AF"),
            "work_patterns": {
                "best_focus_window": "morning",
                "average_session_minutes": 45,
                "context_switching": "low"
            },
            "response_behavior": {
                "avg_response_minutes": 6,
                "response_consistency": "high",
                "needs_reminders": False
            },
            "deadline_behavior": {
                "on_time_rate": 0.83,
                "last_minute_tendency": "medium"
            },
            "confidence_score": 0.81,
            "last_updated": dt.utcnow().isoformat() + "Z"
        }
        
        collection.insert_one(habit_doc)
    elif mem_type.upper() == "CONVERSATION_SNAPSHOT":
        from datetime import datetime as dt
        import uuid
        
        # Create the conversation snapshot document with the specified schema
        snapshot_doc = {
            "_id": f"SNAP_{str(uuid.uuid4().hex[:3]).upper()}",
            "team_id": data.get("team_id", "TEAM_92AF"),
            "member_id": data.get("member_id", "MEM_01"),
            "related_task_id": data.get("related_task_id", "TASK_01"),
            "snapshot": {
                "progress": data.get("progress", ""),
                "blocker": data.get("blocker", ""),
                "next_step": data.get("next_step", "")
            },
            "confidence": data.get("confidence", 0.87),
            "source": data.get("source", "CHAT_SUMMARY"),
            "created_at": dt.utcnow().isoformat() + "Z"
        }
        
        collection.insert_one(snapshot_doc)
    elif mem_type.upper() == "AUTOMATION_LOG":
        from datetime import datetime as dt
        import uuid
        
        # Create the automation log document with the specified schema
        log_doc = {
            "_id": f"AUTO_{str(uuid.uuid4().hex[:2]).upper()}",
            "team_id": data.get("team_id", "TEAM_92AF"),
            "member_id": data.get("member_id", "MEM_01"),
            "task_id": data.get("task_id", "TASK_01"),
            "action": {
                "type": data.get("action_type", "TASK_ASSIGN"),
                "channel": data.get("channel", "whatsapp"),
                "intent": data.get("intent", "ESCALATION")
            },
            "reason": {
                "trigger": data.get("trigger", "TASK_DEADLINE_MISSED"),
                "details": data.get("details", "No update after deadline")
            },
            "outcome": {
                "status": data.get("status", "COMPLETED"),
                "response": data.get("response", "Action completed")
            },
            "confidence": data.get("confidence", 0.91),
            "created_at": dt.utcnow().isoformat() + "Z"
        }
        
        collection.insert_one(log_doc)
    else:
        collection.insert_one({
            "team_name": team_name,
            "type": mem_type,
            "data": data,
            "created_at": datetime.utcnow()
        })

