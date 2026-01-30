from pydantic import BaseModel
from typing import List, Dict, Any


class Member(BaseModel):
    name: str
    email: str
    phone: str = ""
    role: str = "Team Member"
    skills: str = ""


class RegisterRequest(BaseModel):
    team_name: str
    problem_statement: str
    duration_hours: int
    members: List[Member]