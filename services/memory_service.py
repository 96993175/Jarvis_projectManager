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
            "latest_summary": latest_summary
        }

    @staticmethod
    def append_chat_history(token: str, user_msg: str, ai_msg: str):
        """
        Appends to member_chat collection and triggers summarization every 5 messages.
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
        # Get current message count
        chat_doc = db.member_chat.find_one({"token": token})
        msg_count = len(chat_doc.get("messages", []))
        
        # Basic trigger: Every 5 interactions (10 messages total: 5 user + 5 AI)
        # We check if (msg_count / 2) % 5 == 0? Or just simply msg_count > 0 and msg_count % 10 == 0
        if msg_count > 0 and msg_count % 10 == 0:
            MemoryService.generate_and_save_summary(token, chat_doc.get("messages", []))

        # Return the updated history (last 10 items) for the UI
        return chat_doc.get("messages", [])[-10:]

    @staticmethod
    def generate_and_save_summary(token: str, all_messages: list):
        """
        Generates a summary of the recent conversation and saves to member_chat_summery.
        """
        # Take the last 10 messages for summary
        recent_msgs = all_messages[-10:]
        
        # In a real scenario, this would call the LLM to summarize.
        # For now, we'll create a placeholder summary or simple concatenation.
        # TODO: Replace with actual LLM call
        summary_text = f"User discussed: {recent_msgs[0]['message'][:20]}... and {len(recent_msgs)} other messages."
        
        member = db.members.find_one({"token": token})
        member_name = member.get("name", "Unknown") if member else "Unknown"

        db.member_chat_summery.insert_one({
            "token": token,
            "member_name": member_name,
            "summary_text": summary_text,
            "timestamp": datetime.now(timezone.utc)
        })
        print(f"📝 Summary Generated for {member_name}")

    @staticmethod
    def save_insight(token: str, insight_text: str):
        # Deprecated or mapped to generic insights if needed
        pass
