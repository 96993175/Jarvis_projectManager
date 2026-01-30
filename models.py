from pydantic import BaseModel
from typing import List, Union

class Member(BaseModel):
    name: str
    email: str
    phone: str = ""
    role: str = "Team Member"
    skills: Union[str, List[str]] = ""

class RegisterRequest(BaseModel):
    team_name: str
    problem_statement: str
    duration_hours: int
    members: List[Member]
