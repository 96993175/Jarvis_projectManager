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
        Retrieves all necessary context for the AI:
        1. Member Profile & Latest Chat History (from Members collection)
        2. Team/Hackathon Info (from Teams collection)
        3. Behavioral Insights (from MemberInsights collection)
        """
        if db is None:
            raise Exception("Database not connected")

        # 1. Get Member
        member = db.members.find_one({"token": token})
        if not member:
            return None
        
        # 2. Get Team
        team = db.teams.find_one({"team_name": member["team_name"]})
        if not team:
            # Fallback if team missing (shouldn't happen)
            team = {"team_name": "Unknown", "problem_statement": "Unknown"}

        # 3. Get Recent Insights (The "Behavioral Memory")
        # Fetch last 5 insights to give the AI context on what the user has been doing
        insights_cursor = db.member_insights.find(
            {"token": token}
        ).sort("timestamp", -1).limit(5)
        
        recent_insights = [insight["insight"] for insight in insights_cursor]
        # Reverse to chronological order (oldest -> newest) for the prompt
        recent_insights.reverse()

        return {
            "member": member,
            "team": team,
            "insights": recent_insights
        }

    @staticmethod
    def append_chat_history(token: str, user_msg: str, ai_msg: str):
        """
        Appends the interaction to the member's chat history.
        Also updates 'last_active_at'.
        """
        if db is None: return

        timestamp = datetime.now(timezone.utc)
        
        entry = [
            {"role": "user", "message": user_msg, "timestamp": timestamp},
            {"role": "jarvis", "message": ai_msg, "timestamp": timestamp}
        ]

        db.members.update_one(
            {"token": token},
            {
                "$push": {"chat_history": {"$each": entry}},
                "$set": {"last_active_at": timestamp}
            }
        )
        
        # Return the updated history (last 10 items) for the UI
        updated_member = db.members.find_one({"token": token}, {"chat_history": 1})
        return updated_member.get("chat_history", [])[-10:]

    @staticmethod
    def save_insight(token: str, insight_text: str):
        """
        Saves the extracted user behavior/insight to the dedicated collection.
        This is the result of the 'Insight Loop'.
        """
        if db is None: return
        
        # Look up member name/team for easier debugging of the DB
        member = db.members.find_one({"token": token}, {"name": 1, "team_name": 1})
        
        doc = {
            "token": token,
            "member_name": member.get("name", "Unknown") if member else "Unknown",
            "team_name": member.get("team_name", "Unknown") if member else "Unknown",
            "insight": insight_text,
            "timestamp": datetime.now(timezone.utc)
        }
        
        db.member_insights.insert_one(doc)
        print(f"🧠 Insight Saved: {insight_text[:50]}...")

    @staticmethod
    def save_plan_context(token: str, plan_text: str, summary_text: str):
        """
        Saves a project plan and its summary.
        Used for the 'Recursive Context' cycle.
        """
        if db is None: return

        doc = {
            "token": token,  # Who initiated/owned the plan
            "plan_text": plan_text,
            "summary_text": summary_text,
            "timestamp": datetime.now(timezone.utc)
        }
        db.plan_history.insert_one(doc)
        print("📅 Plan & Summary Saved to DB")

    @staticmethod
    def get_latest_plan_context() -> dict:
        """
        Retrieves the most recent plan summary to seed the next planning step.
        """
        if db is None: return None
        
        # Get the very last plan document
        doc = db.plan_history.find_one(sort=[("timestamp", -1)])
        return doc
