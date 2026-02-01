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
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

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

    # 2️⃣ Save MEMBERS with team_name reference
    member_tokens = []
    for i, member in enumerate(req.members):
        member_data = member.dict()
        member_data.update({
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

    try:
        # Get member using token
        member = db.members.find_one({"token": token})
        if not member:
            return {"success": False, "error": "Member not found or invalid token"}

        # Get team data using team_name
        team = db.teams.find_one({"team_name": member["team_name"]})
        if not team:
            return {"success": False, "error": "Team not found"}

        return {
            "success": True,
            "member": {
                "name": member.get("name", ""),
                "role": member.get("role", "")
            },
            "team": {
                "team_name": team.get("team_name", ""),
                "problem_statement": team.get("problem_statement", "")
            },
            "chat_history": member.get("chat_history", [])
        }
    except Exception as e:
        # Log the error for debugging
        print(f"Error in chat init endpoint: {str(e)}")
        return {"success": False, "error": f"An error occurred: {str(e)}"}

# 🔹 CHAT MESSAGE ENDPOINT
@app.post("/api/chat")
def chat(message_data: dict = Body(...)):
    """Handle all chat interactions including welcome messages"""
    token = message_data.get("token")
    message = message_data.get("message")
    is_welcome = message_data.get("is_welcome", False)
    
    if not token or not message:
        return {"success": False, "error": "Missing token or message"}
    
    from mongo_client import db
    from groq import Groq
    import json
    
    try:
        # Get member using token
        member = db.members.find_one({"token": token})
        if not member:
            return {"success": False, "error": "Member not found or invalid token"}

        # Get team data using team_name
        team = db.teams.find_one({"team_name": member["team_name"]})
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

Welcome {member.get('name', 'Team Member')} ({member.get('role', 'Team Member')}) to the team!

Team: {team['team_name']}
Problem: {team['problem_statement']}
Duration: {team.get('hackathon', {}).get('duration_hours', 24)} hours

Skills: {", ".join(member.get("skills", []))}

Create a warm, motivating welcome message that:
- Speaks directly to {member.get('name', 'Team Member')}
- Sounds human, confident, and friendly
- Avoids generic phrases
- Makes the message of max 50 words
"""

        else:
            # Regular chat prompt with memory
            recent_history = conversation_history[-10:]  # Last 10 messages for better context
            history_text = "\n".join([f"{msg['role'].upper()}: {msg['message']}" for msg in recent_history[:-1]])
            
            # Include team timing information
            hackathon_info = team.get('hackathon', {})
            timing_info = ""
            if hackathon_info.get('start_time') and hackathon_info.get('duration_hours'):
                from datetime import datetime, timedelta
                start_time = datetime.fromisoformat(str(hackathon_info["start_time"]).replace('Z', '+00:00')) if isinstance(hackathon_info["start_time"], str) else hackathon_info["start_time"]
                duration_hours = hackathon_info.get("duration_hours", 24)
                end_time = start_time + timedelta(hours=duration_hours)
                time_elapsed = datetime.utcnow() - start_time
                time_remaining = end_time - datetime.utcnow()
                
                timing_info = f"\nTime elapsed: {time_elapsed.total_seconds()/3600:.1f} hours"
                timing_info += f"\nTime remaining: {time_remaining.total_seconds()/3600:.1f} hours"
                timing_info += f"\nTotal duration: {duration_hours} hours"
            
            prompt = f"""
You are Jarvis, an AI hackathon project coordinator having a conversation with {member.get('name', 'Team Member')}.

Conversation history:
{history_text}

Member role: {member.get('role', 'Team Member')}
Skills: {", ".join(member.get("skills", []))}
Team: {team['team_name']}
Problem: {team['problem_statement']}{timing_info}

Respond naturally as a helpful AI assistant. Be conversational, remember previous context, help with hackathon coordination, and keep responses under 60 words. Use the conversation history to provide personalized and contextual responses.
"""
        
        # Call Groq API
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
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
            {"token": token},
            {"$set": {"chat_history": conversation_history, "last_active_at": datetime.utcnow()}}
        )
        
        return {
            "success": True,
            "response": ai_response,
            "chat_history": conversation_history
        }
    except Exception as e:
        # Log the error for debugging
        print(f"Error in chat endpoint: {str(e)}")
        return {"success": False, "error": f"An error occurred: {str(e)}"}

@app.get("/api/chat/history")
def get_chat_history(token: str):
    """Get chat history for a member"""
    from mongo_client import db

    try:
        # Get member using token
        member = db.members.find_one({"token": token})
        if not member:
            return {"success": False, "error": "Member not found or invalid token"}

        # Get chat history
        chat_history = member.get("chat_history", [])
        
        return {
            "success": True,
            "history": chat_history
        }
    except Exception as e:
        # Log the error for debugging
        print(f"Error in chat history endpoint: {str(e)}")
        return {"success": False, "error": f"An error occurred: {str(e)}"}

@app.get("/debug/routes")
def debug_routes():
    return {"routes": ["health", "api/register", "api/chat/init", "api/chat", "api/chat/history"]}