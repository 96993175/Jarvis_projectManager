from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
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
    team_id = str(team_result)

    # 2️⃣ Save MEMBERS with proper team linking
    for i, member in enumerate(req.members):
        member_data = member.dict()
        member_data.update({
            "team_id": team_id,
            "member_index": i + 1,
            "is_leader": (i == 0)  # First member is team leader
        })
        save_memory(team, "MEMBER", member_data)

    # 3️⃣ Update team members_count
    from mongo_client import db
    db["team_details"].update_one(
        {"_id": team_id},
        {"$set": {"members_count": len(req.members)}}
    )

    # 4️⃣ Save EVENT for registration
    save_memory(team, "EVENT", {
        "event": "TEAM_REGISTERED",
        "members_count": len(req.members)
    })
    
    # 5️⃣ Save simple registration completion event
    save_memory(team, "REGISTRATION_COMPLETE", {
        "status": "success",
        "message": "Team registration completed successfully",
        "timestamp": datetime.utcnow()
    })



    # 8️⃣ Start timer
    #start_desktop_timer(req.duration_hours)

    # 9️⃣ Activate Jarvis Orb via command file
    import os
    import json
    import time
    
    # Get absolute paths
    current_dir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.dirname(current_dir)
    
    print(f"DEBUG: Backend current directory: {current_dir}")
    print(f"DEBUG: Project root: {project_root}")
    
    # Create command file to activate the orb
    command_file_path = os.path.join(project_root, "memory", "commands.json")
    
    print(f"DEBUG: Attempting to create command file at: {command_file_path}")
    
    # Ensure the memory directory exists
    memory_dir = os.path.join(project_root, "memory")
    os.makedirs(memory_dir, exist_ok=True)
    print(f"DEBUG: Memory directory ensured at: {memory_dir}")
    
    command_data = {
        "action": "START_JARVIS",
        "team": team,
        "timestamp": time.time()
    }
    
    try:
        with open(command_file_path, "w") as f:
            json.dump(command_data, f)
        print(f"Jarvis Orb activation command sent for team: {team}")
        print(f"Command written to: {command_file_path}")
    except Exception as e:
        print(f"ERROR writing command file: {e}")
        import traceback
        print(traceback.format_exc())

    return {"status": "registered"}

@app.get("/api/member/{member_id}")
def get_member(member_id: str):
    from mongo_client import db

    member = db.members.find_one({"member_id": member_id})
    if not member:
        return {"success": False, "message": "Member not found"}

    member["_id"] = str(member["_id"])  # Convert ObjectId to string for JSON
    return {"success": True, "member": member}

@app.get("/api/team/{team_id}")
def get_team(team_id: str):
    from mongo_client import db

    team = db.team_details.find_one({"_id": team_id})
    if not team:
        return {"success": False, "message": "Team not found"}

    team["_id"] = str(team["_id"])
    return {"success": True, "team": team}

@app.post("/api/chat")
def chat(message_data: dict = Body(...)):
    """Handle all chat interactions including welcome messages"""
    member_id = message_data.get("member_id")
    message = message_data.get("message")
    is_welcome = message_data.get("is_welcome", False)
    
    if not member_id or not message:
        return {"success": False, "error": "Missing member_id or message"}
    
    from mongo_client import db
    from groq import Groq
    import json
    
    # Get member and team data
    member = db.members.find_one({"member_id": member_id})
    if not member:
        return {"success": False, "error": "Member not found"}
    
    team = db.team_details.find_one({"_id": member["team_id"]})
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
        {"_id": member_id},
        {"$set": {"chat_history": conversation_history, "last_active_at": datetime.utcnow()}}
    )
    
    return {
        "success": True,
        "response": ai_response,
        "chat_history": conversation_history
    }

@app.get("/debug/routes")
def debug_routes():
    return {"routes": ["health", "api/member/{id}", "api/team/{id}", "api/chat"]}

from fastapi import Body

