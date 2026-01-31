from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
from groq import Groq
from memory_store import save_memory
from dotenv import load_dotenv

# Load environment
load_dotenv()

app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

# MINIMAL REGISTRATION
@app.post("/api/register")
def register(data: dict = Body(...)):
    """
    Minimal registration:
    - Create team
    - Create members with tokens
    - Return member tokens
    """
    # Create team
    team_id = save_memory(data["team_name"], "TEAM", {
        "problem_statement": data["problem_statement"],
        "duration_hours": data["duration_hours"]
    })
    
    # Create members
    member_tokens = []
    for member_data in data["members"]:
        token = save_memory(data["team_name"], "MEMBER", {
            "team_id": team_id,
            "name": member_data["name"],
            "role": member_data["role"],
            "skills": member_data["skills"]
        })
        member_tokens.append({
            "name": member_data["name"],
            "token": token
        })
    
    return {"status": "registered", "members": member_tokens}

# MINIMAL CHAT
@app.post("/api/chat")
def chat(data: dict = Body(...)):
    """
    Minimal chat:
    - Token validation
    - Groq AI response
    - MongoDB storage
    """
    token = data.get("token")
    message = data.get("message")
    
    if not token or not message:
        return {"success": False, "error": "Missing token or message"}
    
    from mongo_client import db
    
    # Validate token and get member
    member = db.members.find_one({"token": token})
    if not member:
        return {"success": False, "error": "Invalid token"}
    
    # Get team
    team = db.teams.find_one({"_id": member["team_id"]})
    if not team:
        return {"success": False, "error": "Team not found"}
    
    # Build AI prompt
    prompt = f"""
You are Jarvis, an AI hackathon assistant.

Team: {team['team_name']}
Member: {member['name']} ({member['role']})
Problem: {team['problem_statement']}

Message: {message}

Respond helpfully and concisely.
"""
    
    # Call Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=200
    )
    
    ai_response = response.choices[0].message.content
    
    # Store conversation
    db.members.update_one(
        {"_id": member["_id"]},
        {
            "$push": {
                "chat_history": {
                    "user": message,
                    "jarvis": ai_response,
                    "timestamp": datetime.utcnow()
                }
            }
        }
    )
    
    return {"success": True, "response": ai_response}

@app.get("/debug/routes")
def debug_routes():
    return {"routes": ["/health", "/api/register", "/api/chat"]}
