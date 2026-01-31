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

# Initialize FastAPI app
app = FastAPI(title="Jarvis Hackathon API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/register")
def register_team(req: RegisterRequest):
    """
    Register new team with all members.
    Returns: {"success": True, "team_id": str, "member_ids": [str, ...]}
    """
    # Input validation
    if not req.team_name or not req.problem_statement:
        return {"success": False, "error": "Team name and problem statement required"}
    
    # Remove debug log lines
    if hasattr(req, 'debug_info'):
        delattr(req, 'debug_info')
    
    # Get team name
    team = req.team_name

    # 1️⃣ Save TEAM (hackathon + team) — now synchronous
    from datetime import datetime
    from memory_store import save_memory

    team_result = save_memory(team, "TEAM", {
        "problem_statement": req.problem_statement,
        "duration_hours": req.duration_hours
    })
    
    # Get the generated team ID
    team_id = str(team_result)

    # 2️⃣ Save MEMBERS with proper team linking
    member_ids = []
    for i, member in enumerate(req.members):
        member_data = member.dict()
        member_data.update({
            "team_id": team_id,
            "member_index": i + 1,
            "is_leader": (i == 0)  # First member is team leader
        })
        # This now returns the actual member_id string
        member_id = save_memory(team, "MEMBER", member_data)
        member_ids.append(member_id)

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

    # 6️⃣ Start timer (moved before orb activation)
    # start_desktop_timer(req.duration_hours)

    # 7️⃣ Activate Jarvis Orb via command file
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
    if not os.path.exists(memory_dir):
        os.makedirs(memory_dir)
        print(f"DEBUG: Created memory directory: {memory_dir}")
    
    if not os.path.exists(command_file_path):
        with open(command_file_path, "w") as f:
            f.write(json.dumps({"status": "init"}, indent=2))
            print(f"DEBUG: Created empty command file: {command_file_path}")
    
    # Check if orb already exists/running before launching
    # Remove the activation as requested in our previous conversation

    # Generate random member IDs for linking (should match MongoDB storage)
    # Remove the simulated orb startup log entries
    
    print("POST /api/register:")
    print("  - hackathon data ✅")
    print("  - saved members with links")
    print(f"  - timer will be auto-launched via .orb if on local mode")
    print("  - MEMORY: Use mongo integration or store key value - you make final choice")
    
    print()
    print("🟨 member.name keys in newMemory member is String")
    print("Please check each member input 'name'")
    
    for member_data in [req.members] if hasattr(req, 'members') else [m.__dict__ if hasattr(m, '__dict__') else dict(m) for m in getattr(req, 'members', [])]:
        if isinstance(member_data, list):
            for member in member_data:
                print(f"  - Member name: {member.get('name', 'N/A')}")
        else:
            print(f"  - Member name: {member_data.get('name', 'N/A')}")
    
    print()
    print("🟨 member.skills keys in newMemory member is List[str]")
    print("Please check each member input 'skills'")
    
    for member_data in [req.members] if hasattr(req, 'members') else [m.__dict__ if hasattr(m, '__dict__') else dict(m) for m in getattr(req, 'members', [])]:
        if isinstance(member_data, list):
            for member in member_data:
                print(f"  - Member skills: {member.get('skills', 'N/A')}")
        else:
            print(f"  - Member skills: {member_data.get('skills', 'N/A')}")
    
    print()
    print("🟨 member.email keys in newMemory member is String")
    print("Please check each member input 'email'")
    
    for member_data in [req.members] if hasattr(req, 'members') else [m.__dict__ if hasattr(m, '__dict__') else dict(m) for m in getattr(req, 'members', [])]:
        if isinstance(member_data, list):
            for member in member_data:
                print(f"  - Member email: {member.get('email', 'N/A')}")
        else:
            print(f"  - Member email: {member_data.get('email', 'N/A')}")
    
    print()
    print("🟨 member.phone keys in newMemory member is String")
    print("Please check each member input 'phone'")
    
    for member_data in [req.members] if hasattr(req, 'members') else [m.__dict__ if hasattr(m, '__dict__') else dict(m) for m in getattr(req, 'members', [])]:
        if isinstance(member_data, list):
            for member in member_data:
                print(f"  - Member phone: {member.get('phone', 'N/A')}")
        else:
            print(f"  - Member phone: {member_data.get('phone', 'N/A')}")
    
    print()
    print("🟨 member.role keys in newMemory member is String")
    print("Please check each member input 'role'")
    
    for member_data in [req.members] if hasattr(req, 'members') else [m.__dict__ if hasattr(m, '__dict__') else dict(m) for m in getattr(req, 'members', [])]:
        if isinstance(member_data, list):
            for member in member_data:
                print(f"  - Member role: {member.get('role', 'N/A')}")
        else:
            print(f"  - Member role: {member_data.get('role', 'N/A')}")
    
    print()
    print("✅ Registration completed successfully")
    print(f"Team ID: {team_id}")
    print(f"Member IDs: {member_ids}")
    
    return {
        "success": True, 
        "team_id": team_id,
        "member_ids": member_ids,
        "message": "Team registered successfully"
    }

# Add the rest of your existing endpoints here...
# I'll need to add them back from your original file

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

    team["_id"] = str(team["_id"])  # Convert ObjectId to string for JSON
    return {"success": True, "team": team}

@app.post("/api/chat")
def chat(message_data: dict = Body(...)):
    """Handle all chat interactions including welcome messages"""
    from mongo_client import db
    import json
    
    member_id = message_data.get("member_id")
    user_message = message_data.get("message", "")
    is_welcome = message_data.get("is_welcome", False)
    
    if not member_id:
        return {"success": False, "error": "member_id required"}
    
    # Get member and team data
    member = db.members.find_one({"member_id": member_id})
    if not member:
        return {"success": False, "error": "Member not found"}
    
    team = db.team_details.find_one({"_id": member["team_id"]})
    if not team:
        return {"success": False, "error": "Team not found"}
    
    # Get conversation history
    conversation_history = member.get("chat_history", [])
    
    # Add user message to history (except for welcome messages)
    if not is_welcome and user_message:
        conversation_history.append({
            "role": "user",
            "message": user_message,
            "timestamp": datetime.utcnow()
        })
    
    # Prepare prompt for AI
    if is_welcome:
        # Welcome message prompt
        prompt = f"""
You are Jarvis, an AI hackathon project coordinator.

Welcome {member['profile']['name']} ({member['profile']['role']}) to the team!

Team: {team['team_name']}
Problem: {team['problem_statement']}
Duration: {team['hackathon']['duration_hours']} hours

Skills: {", ".join(member.get('profile', {}).get('skills', []))}

Create a warm, motivating welcome message that:
- Speaks directly to {member['profile']['name']}
- Explains how their role helps the team
- Sounds human, confident, and friendly
- Avoids generic phrases
"""
    else:
        # Regular chat prompt with memory
        recent_history = conversation_history[-5:]  # Last 5 messages for context
        history_text = "\n".join([f"{msg['role'].upper()}: {msg['message']}" for msg in recent_history[:-1]])
        
        prompt = f"""
You are Jarvis, an AI hackathon project coordinator having a conversation with {member['profile']['name']}.

Recent conversation:
{history_text}

Member's role: {member['profile']['role']}
Team: {team['team_name']}
Problem: {team['problem_statement']}

Respond naturally to their message while being helpful and encouraging.
"""
    
    # Call Groq API
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": "You are Jarvis, a helpful AI assistant for hackathon teams."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500,
        )
        
        ai_response = completion.choices[0].message.content
        
        # Add AI response to conversation history
        if ai_response:
            conversation_history.append({
                "role": "assistant",
                "message": ai_response,
                "timestamp": datetime.utcnow()
            })
            
            # Update MongoDB with new conversation history
            db.members.update_one(
                {"member_id": member_id},
                {"$set": {"chat_history": conversation_history}}
            )
        
        return {"success": True, "response": ai_response}
        
    except Exception as e:
        print(f"Groq API error: {e}")
        return {"success": False, "error": "AI service unavailable"}

@app.get("/debug/routes")
def debug_routes():
    return {"routes": ["health", "api/member/{id}", "api/team/{id}", "api/chat"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)