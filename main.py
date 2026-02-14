from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from fastapi import Body
from models import RegisterRequest
from memory_store import save_memory

# Import Services
from services.memory_service import MemoryService
from services.intelligence_service import IntelligenceService

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# Initialize Intelligence Service (Global)
ai_service = IntelligenceService()

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

# 🔹 MAIN REGISTER ENDPOINT (Unchanged)
@app.post("/api/register")
def register(req: RegisterRequest):
    team = req.team_name

    # 1️⃣ Save TEAM memory
    save_memory(team, "TEAM", {
        "team_name": team,
        "problem_statement": req.problem_statement,
        "duration_hours": req.duration_hours
    })

    # 2️⃣ Save MEMBERS
    member_tokens = []
    for i, member in enumerate(req.members):
        member_data = member.dict()
        member_data.update({
            "member_index": i + 1,
            "is_leader": (i == 0)
        })
        token = save_memory(team, "MEMBER", member_data)
        member_tokens.append({
            "name": member.name,
            "role": member.role,
            "token": token
        })

    return {
        "status": "registered", 
        "members": member_tokens
    }

# 🔹 CHAT INITIALIZATION ENDPOINT
@app.get("/api/chat/init")
def chat_init(token: str):
    """Initialize chat session - get member and team data"""
    try:
        context = MemoryService.get_user_context(token)
        if not context:
            return {"success": False, "error": "Invalid token"}
        
        member = context["member"]
        team = context["team"]

        return {
            "success": True,
            "member": {
                "name": member.get("name", ""),
                "role": member.get("role", ""),
                "chat_history": member.get("chat_history", [])
            },
            "team": {
                "team_name": team.get("team_name", ""),
                "problem_statement": team.get("problem_statement", "")
            }
        }
    except Exception as e:
        print(f"Init Error: {e}")
        return {"success": False, "error": str(e)}

# 🔹 BACKGROUND TASK: The "Insight Loop"
def process_user_insight(token: str, user_msg: str, ai_msg: str):
    """
    Background task to analyze the interaction and save insights.
    Does not block the response to the user.
    """
    try:
        # Get fresh context
        context = MemoryService.get_user_context(token)
        if not context: return

        # Analyze
        insight = ai_service.analyze_behavior(user_msg, ai_msg, context)
        
        # Save if valid
        if insight:
            MemoryService.save_insight(token, insight)
            
    except Exception as e:
        print(f"Background Insight Error: {e}")

# 🔹 CHAT MESSAGE ENDPOINT
@app.post("/api/chat")
def chat(background_tasks: BackgroundTasks, message_data: dict = Body(...)):
    """
    Handle chat interactions with Dual-Loop Architecture.
    1. Generate Response (Interaction Loop)
    2. Schedule Insight Analysis (Insight Loop)
    """
    token = message_data.get("token")
    message = message_data.get("message")
    # minimal support for 'is_welcome' - for now we treat it as normal flow or skip
    is_welcome = message_data.get("is_welcome", False)
    
    if not token or not message:
        return {"success": False, "error": "Missing token or message"}
    
    try:
        # 1. Get Context (Includes past Insights!)
        context = MemoryService.get_user_context(token)
        if not context:
            return {"success": False, "error": "Invalid token"}

        # 2. Generate AI Response
        if is_welcome:
            # Simple welcome logic reusing the gen-ai but with a welcome preamble
            ai_response = ai_service.generate_response(
                f"[SYSTEM: This is the first interaction. WELCOME the user to the team {context['team']['team_name']}. Message: {message}]", 
                context
            )
        else:
            ai_response = ai_service.generate_response(message, context)
            
        # 3. Save Chat Log
        updated_history = MemoryService.append_chat_history(token, message, ai_response, ai_service)
        
        # 4. Schedule Background Insight Extraction (The "Crazy Part")
        # We run this in the background so the user gets their answer fast!
        background_tasks.add_task(process_user_insight, token, message, ai_response)

        return {
            "success": True,
            "response": ai_response,
            "chat_history": updated_history
        }
        
    except Exception as e:
        print(f"Chat Error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/debug/routes")
def debug_routes():
    return {"routes": ["health", "api/register", "api/chat/init", "api/chat"]}