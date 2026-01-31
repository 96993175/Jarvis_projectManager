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