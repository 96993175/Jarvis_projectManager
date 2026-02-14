from datetime import datetime, timezone
import sys
import os

# Add parent directory to path to allow imports if run directly
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Conditional import to handle both package and direct execution
try:
    from backend.mongo_client import db
except ImportError:
    from mongo_client import db

class MemoryService:
    @staticmethod
    def get_user_context(token: str):
        """
        Retrieves comprehensive context from the new detailed schema:
        1. Member Profile (members)
        2. Team Info (teams)
        3. Recent Chat History (member_chat)
        4. Active Goals (Active_goals)
        5. Manager Instructions (instruction_team)
        6. Chat Summaries (member_chat_summery)
        """
        if db is None:
            raise Exception("Database not connected")

        # 1. Get Member Profile
        member = db.members.find_one({"token": token})
        if not member: return None
        
        # 2. Get Team
        team = db.teams.find_one({"team_name": member["team_name"]})
        if not team: team = {"team_name": "Unknown", "problem_statement": "Unknown"}

        # 3. Get Recent Chat History (Last 10 messages from member_chat)
        chat_doc = db.member_chat.find_one({"token": token})
        recent_chat = chat_doc.get("messages", [])[-10:] if chat_doc else []

        # 4. Get Active Goals
        goals_cursor = db.Active_goals.find({"token": token, "status": "active"})
        active_goals = [g["goal_text"] for g in goals_cursor]

        # 5. Get Instructions (Targeted + All)
        instructions_cursor = db.instruction_team.find({
            "$or": [
                {"target_member_token": token},
                {"target_member_token": "all"}
            ],
            "active": True
        })
        instructions = [i["instruction_text"] for i in instructions_cursor]

        # 6. Get Latest Summary (Context)
        summary_doc = db.member_chat_summery.find_one(
            {"token": token},
            sort=[("timestamp", -1)]
        )
        latest_summary = summary_doc["summary_text"] if summary_doc else "No previous summary."

        return {
            "member": member,
            "team": team,
            "chat_history": recent_chat,
            "active_goals": active_goals,
            "instructions": instructions,
            "latest_summary": latest_summary,
            "insights": []
        }

    @staticmethod
    def append_chat_history(token: str, user_msg: str, ai_msg: str, ai_service=None):
        """
        Appends to member_chat.
        Logic:
        1. Add new messages.
        2. if total > 20 (10 turns):
           - Take oldest 10 messages (5 turns).
           - Summarize them using AI.
           - Store summary in member_chat_summery.
           - Remove them from member_chat.
        """
        if db is None: return

        timestamp = datetime.now(timezone.utc)
        
        entry = [
            {"role": "user", "message": user_msg, "timestamp": timestamp},
            {"role": "jarvis", "message": ai_msg, "timestamp": timestamp}
        ]

        # Update member_chat
        db.member_chat.update_one(
            {"token": token},
            {
                "$push": {"messages": {"$each": entry}},
                "$set": {"last_updated": timestamp}
            },
            upsert=True
        )
        
        # Check for Summarization Trigger
        chat_doc = db.member_chat.find_one({"token": token})
        messages = chat_doc.get("messages", [])
        msg_count = len(messages)
        
        # Trigger if we have more than 20 messages (10 turns).
        # We want to keep the "Last 5" (10 msgs), so we summarize everything before that.
        if msg_count >= 20 and ai_service:
            # We want to keep the NEWEST 10 messages (5 turns).
            # So we summarize the OLDEST (Total - 10) messages.
            # But the user said "when all new 5 conversations added... summarize that all 5".
            # So let's extract the FIRST 10 messages (Oldest 5 turns).
            
            msgs_to_summarize = messages[:10]
            msgs_to_keep = messages[10:]
            
            MemoryService.generate_and_save_summary(token, msgs_to_summarize, ai_service)
            
            # Replace the array with just the kept messages
            db.member_chat.update_one(
                {"token": token},
                {"$set": {"messages": msgs_to_keep}}
            )
            print(f"[MEMORY] Cleaned up chat. Kept {len(msgs_to_keep)} messages.")
            return msgs_to_keep

        # Return the updated history (last 10 items) for the UI
        return messages[-10:]

    @staticmethod
    def generate_and_save_summary(token: str, messages: list, ai_service):
        """
        Generates a summary of the provided messages and saves to member_chat_summery.
        """
        summary_text = ai_service.summarize_chat(messages)
        
        member = db.members.find_one({"token": token})
        member_name = member.get("name", "Unknown") if member else "Unknown"

        db.member_chat_summery.insert_one({
            "token": token,
            "member_name": member_name,
            "summary_text": summary_text,
            "timestamp": datetime.now(timezone.utc)
        })
        print(f"[MEMORY] Summary Generated for {member_name}")

    @staticmethod
    def append_manager_chat_history(user_msg: str, ai_msg: str, ai_service=None):
        """
        Appends to manager_chat (Main Jarvis).
        Logic:
        1. Add new messages.
        2. if total > 20 (10 turns):
           - Summarize oldest 10 messages.
           - Store summary in manager_chat_summery.
           - Keep newest 10 messages.
        """
        if db is None: return

        timestamp = datetime.now(timezone.utc)
        
        entry = [
            {"role": "user", "message": user_msg, "timestamp": timestamp},
            {"role": "jarvis", "message": ai_msg, "timestamp": timestamp}
        ]

        # Update manager_chat
        # We use a fixed ID for the manager, or just a single document if we want.
        # Let's assume a single document or simple collection. 
        # Using a fixed "token" or "id" for manager makes it consistent.
        manager_id = "MANAGER_MAIN"

        db.manager_chat.update_one(
            {"manager_id": manager_id},
            {
                "$push": {"messages": {"$each": entry}},
                "$set": {"last_updated": timestamp}
            },
            upsert=True
        )
        
        # Check for Summarization Trigger
        chat_doc = db.manager_chat.find_one({"manager_id": manager_id})
        messages = chat_doc.get("messages", [])
        msg_count = len(messages)
        
        if msg_count >= 20 and ai_service:
            msgs_to_summarize = messages[:10]
            msgs_to_keep = messages[10:]
            
            # Generate Summary
            summary_text = ai_service.summarize_chat(msgs_to_summarize)
            
            # Save Summary
            db.manager_chat_summery.insert_one({
                "manager_id": manager_id,
                "summary_text": summary_text,
                "timestamp": datetime.now(timezone.utc)
            })
            print(f"[MEMORY] Manager Chat Summarized.")
            
            # Cleanup
            db.manager_chat.update_one(
                {"manager_id": manager_id},
                {"$set": {"messages": msgs_to_keep}}
            )
            return msgs_to_keep

        return messages[-10:]

    @staticmethod
    def save_insight(token: str, insight_text: str):
        # Deprecated or mapped to generic insights if needed
        pass
