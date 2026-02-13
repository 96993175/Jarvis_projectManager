import os
import json
from datetime import datetime, timezone
from groq import Groq
try:
    from backend.mongo_client import db
except ImportError:
    from mongo_client import db

class MemorySelector:
    """
    The 'Brain' of the AI Project Manager.
    Decides which memory collections are relevant for a given query.
    """
    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def get_relevant_context(self, user_query: str, current_goal: str = None) -> dict:
        """
        Analyzes the query and fetches relevant data from MongoDB.
        """
        print(f"🧠 [SELECTOR] Analyzing query: {user_query}")

        # 1. LLM Decision: Which collections to query?
        # We give it the schema summary and ask for a JSON selection.
        prompt = f"""
        You are the Memory Selector for an AI Project Manager.
        Your job is to decide which database collections are needed to answer the user's query.

        DATABASE SCHEMA:
        1. members: Profile details (Name, Role, Skills, Email).
        2. member_chat: Raw chat logs (Recent messages).
        3. Active_goals: Current active goals/tasks for members.
        4. teams: Project details (Name, Problem Statement, Deadline).
        5. member_chat_summery: Long-term insights/summaries of member chats.
        
        USER QUERY: "{user_query}"
        CURRENT GOAL: "{current_goal}"

        OUTPUT JSON ONLY:
        {{
            "needs_members": boolean,
            "target_member_name": "name" or null,
            "needs_chat_logs": boolean,
            "needs_active_goals": boolean,
            "needs_team_details": boolean,
            "needs_summaries": boolean
        }}
        """
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            decision = json.loads(response.choices[0].message.content)
            print(f"🧠 [SELECTOR] Decision: {decision}")
        except Exception as e:
            print(f"❌ [SELECTOR] Error deciding memory: {e}")
            # Fallback: Fetch everything if uncertain
            decision = {
                "needs_members": True, "needs_active_goals": True, "needs_team_details": True, 
                "needs_chat_logs": False, "needs_summaries": False, "target_member_name": None
            }

        context = {}

        # 2. Execute Queries based on decision
        if db is None:
            return {"error": "Database disconnected"}

        # Team Details
        if decision.get("needs_team_details"):
            team = db.teams.find_one({}, sort=[("created_at", -1)])
            context["team"] = team if team else "No team found."

        # Members (Targeted or All)
        target = decision.get("target_member_name")
        member_query = {}
        if target and isinstance(target, str) and target.lower() != "null":
            member_query["name"] = {"$regex": target, "$options": "i"}
        
        if decision.get("needs_members"):
            members = list(db.members.find(member_query, {"_id": 0, "token": 1, "name": 1, "role": 1, "skills": 1}))
            context["members"] = members

        # Active Goals
        if decision.get("needs_active_goals"):
            goals = list(db.Active_goals.find({"status": "active"}, {"_id": 0, "member_name": 1, "goal_text": 1, "time_start": 1}))
            context["active_goals"] = goals

        # Chat Logs (Only if specific member targeted, to avoid overflow)
        if decision.get("needs_chat_logs") and target:
             # Find token first
             mem = db.members.find_one(member_query)
             if mem:
                 chat = db.member_chat.find_one({"token": mem["token"]}, {"messages": {"$slice": -5}}) # Last 5
                 context["chat_logs"] = chat.get("messages") if chat else []

        # Summaries
        if decision.get("needs_summaries"):
             # If target, get theirs. If not, get recent 5 from anyone.
             q = {"token": mem["token"]} if target and 'mem' in locals() and mem else {}
             summaries = list(db.member_chat_summery.find(q, {"_id": 0, "member_name": 1, "summary_text": 1}).sort("timestamp", -1).limit(5))
             context["summaries"] = summaries

        return context
