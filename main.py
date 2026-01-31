from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import sys
import os
from datetime import datetime
from groq import Groq
from fastapi import Body
from models import RegisterRequest
from memory_store import save_memory

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# ✅ CORS Configuration for Render Deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow ALL origins for hackathon
    allow_credentials=False,  # IMPORTANT: must be False with "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 Health check
@app.get("/health")
def health():
    return {"status": "ok"}


# 🔹 Timer endpoints
@app.post("/api/timer/start")
def start_timer(timer_request: dict):
    duration = timer_request.get("duration", 24)
    try:
        start_desktop_timer(duration)
        return {"success": True, "message": "Timer started successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}, 500

@app.post("/api/timer/stop")
def stop_timer():
    try:
        # Implementation for stopping timer would go here
        return {"success": True, "message": "Timer stopped successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}, 500

# 🔹 MAIN REGISTER ENDPOINT
@app.post("/api/register")
def register(req: RegisterRequest):

    team = req.team_name

    # 1️⃣ Save TEAM memory (Phase-1 simplified structure)
    team_result = save_memory(team, "TEAM", {
        "team_name": team,
        "problem_statement": req.problem_statement,
        "duration_hours": req.duration_hours
    })
    
    # Get the generated team ID
    team_id = team_result

    # 2️⃣ Save MEMBERS with proper team linking
    member_tokens = []
    for i, member in enumerate(req.members):
        member_data = member.dict()
        member_data.update({
            "team_id": team_id,
            "member_index": i + 1,
            "is_leader": (i == 0)  # First member is team leader
        })
        # save_memory returns the token for this member
        token = save_memory(team, "MEMBER", member_data)
        member_tokens.append({
            "name": member.name,
            "role": member.role,
            "token": token
        })

    # 3️⃣ Return member tokens for link generation
    return {
        "status": "registered", 
        "members": member_tokens
    }

# 🔹 CHAT INITIALIZATION ENDPOINT
@app.get("/api/chat/init")
def chat_init(token: str):
    """Initialize chat session - get member and team data"""
    from mongo_client import db

    # Get member using token
    member = db.members.find_one({"token": token})
    if not member:
        return {"success": False, "error": "Member not found or invalid token"}

    # Get team data
    team = db.teams.find_one({"_id": member["team_id"]})
    if not team:
        return {"success": False, "error": "Team not found"}

    # Convert ObjectId to string for JSON serialization
    member["_id"] = str(member["_id"])
    team["_id"] = str(team["_id"])

    return {
        "success": True,
        "member": member,
        "team": team
    }

# 🔹 CHAT MESSAGE ENDPOINT
@app.post("/api/chat")
def chat(data: dict = Body(...)):
    """Handle all chat interactions including welcome messages"""
    token = data.get("token")
    message = data.get("message")
    is_welcome = data.get("is_welcome", False)
    
    if not token or not message:
        return {"success": False, "error": "Missing token or message"}
    
    from mongo_client import db
    from groq import Groq
    import json
    
    # Get member using token - NO MORE member_id
    member = db.members.find_one({"token": token})
    if not member:
        return {"success": False, "error": "Invalid chat link"}
    
    # Get team data
    team = db.teams.find_one({"_id": member["team_id"]})
    if not team:
        return {"success": False, "error": "Team not found"}
    
    # Build conversation context
    conversation_history = member.get("chat_history", [])
    
    # Add current message to history
    conversation_history.append({
        "role": "user",
        "message": message,
        "timestamp": datetime.utcnow()
    })
    
    # Build prompt with context
    if is_welcome:
        # Welcome message prompt
        prompt = f"""
You are Jarvis, an AI hackathon project coordinator.

Welcome {member['name']} ({member['role']}) to the team!

Team: {team['team_name']}
Problem: {team['problem_statement']}
Duration: {team['duration_hours']} hours

Skills: {", ".join(member.get("skills", []))}

Create a warm, motivating welcome message that:
- Speaks directly to {member['name']}
- Explains how their role helps the team
- Sounds human, confident, and friendly
- Avoids generic phrases
"""

    else:
        # Regular chat prompt with memory
        recent_history = conversation_history[-5:]  # Last 5 messages for context
        history_text = "\n".join([f"{msg['role'].upper()}: {msg['message']}" for msg in recent_history[:-1]])
        
        prompt = f"""
You are Jarvis, an AI hackathon project coordinator having a conversation with {member['name']}.

Recent conversation:
{history_text}

Member's role: {member['role']}
Team: {team['team_name']}
Problem: {team['problem_statement']}

Respond naturally as a helpful AI assistant. Be conversational, remember context, and help with hackathon coordination.
"""
    
    # Call Groq API
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are Jarvis, a helpful AI coordinator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )
    
    ai_response = response.choices[0].message.content
    
    # Add AI response to chat history
    conversation_history.append({
        "role": "jarvis",
        "message": ai_response,
        "timestamp": datetime.utcnow()
    })
    
    # Update member document with new chat history
    db.members.update_one(
        {"_id": member["_id"]},
        {"$set": {"chat_history": conversation_history}}
    )
    
    return {
        "success": True,
        "response": ai_response,
        "chat_history": conversation_history
    }

@app.get("/debug/routes")
def debug_routes():
    return {"routes": ["health", "api/register", "api/chat/init", "api/chat"]}

from fastapi import Body