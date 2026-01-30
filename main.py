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

@app.options("/{path:path}")
def options_handler(path: str):
    return {}

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
    # TEMP mock (for now)
    return {
        "success": True,
        "member": {
            "id": member_id,
            "name": "Test Member",
            "role": "Backend Developer",
            "skills": "Python, FastAPI"
        }
    }
@app.get("/api/team/info")
def get_team_info():
    return {
        "success": True,
        "team": {
            "team_id": "TEAM_92AF",
            "team_name": "Jarvis Hackers",
            "problem_statement": "Task & Project Collaboration Tool",
            "hackathon_duration_hours": 36
        }
    }
@app.get("/debug/routes")
def debug_routes():
    return {"routes": ["health", "api/member/{id}", "api/team/info"]}

from fastapi import Body

@app.post("/api/member/welcome")
def member_welcome(data: dict = Body(...)):
    team = data.get("team")        # full team object
    member = data.get("member")    # full member object

    if not team or not member:
        return {"success": False, "message": "Missing data"}

    # 🔹 AI PROMPT (THIS IS THE MAGIC)
    prompt = f"""
You are Jarvis, an AI hackathon project coordinator.

Welcome a team member in a friendly, motivating way.

Member details:
Name: {member['name']}
Role: {member['role']}
Skills: {member.get('skills', 'N/A')}

Team details:
Team name: {team['team_name']}
Problem statement: {team['problem_statement']}
Hackathon duration: {team['duration_hours']} hours

Guidelines:
- Use the member's name
- Explain why their role is important
- Motivate them to collaborate
- Keep it short, warm, and confident
- Do NOT mention IDs or technical terms
"""
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    # 🔹 GROQ AI CALL
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are Jarvis, a helpful AI coordinator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6,
        max_tokens=200
    )

    ai_message = response.choices[0].message.content

    return {
        "success": True,
        "message": ai_message
    }
