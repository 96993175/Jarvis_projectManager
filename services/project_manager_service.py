import sys
import os

# Add parent directory to path to allow imports if run directly
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.intelligence_service import IntelligenceService
from services.memory_service import MemoryService
from services.whatsapp_service import WhatsAppService

class ProjectManagerService:
    def __init__(self):
        self.ai_service = IntelligenceService()

    def start_planning_cycle(self, token: str, problem_statement: str):
        """
        Orchestrates the 'Boss' cycle:
        1. Retrieve recursive context (if any).
        2. Generate Plan (AI).
        3. Summarize Plan (AI).
        4. Store Context (Memory).
        5. Broadcast Plan (WhatsApp).
        """
        print(f"🚀 [PM] Starting Planning Cycle for problem: {problem_statement[:50]}...")
        
        # 1. Get Recursive Context (Previous Plan Summary)
        last_context_doc = MemoryService.get_latest_plan_context()
        prev_summary = last_context_doc.get("summary_text") if last_context_doc else None
        
        if prev_summary:
            print("📜 [PM] Found previous plan context to build upon.")

        # 2. Generate Detailed Plan
        plan_text = self.ai_service.generate_project_plan(problem_statement, prev_summary)
        print("📝 [PM] detailed plan generated.")

        # 3. Summarize for Future Context
        summary_text = self.ai_service.summarize_plan(plan_text)
        print("🧠 [PM] Plan summarized for recursive memory.")

        # 4. Save to Database
        MemoryService.save_plan_context(token, plan_text, summary_text)

        # 5. Broadcast to WhatsApp Group
        whatsapp_message = f"""
🚀 *New Master Plan Generated* (Jarvis PM)

*Goal*: {problem_statement[:50]}...

{summary_text}

*Check the dashboard for the full step-by-step plan.*
(Broadcasting details...)
"""
        # We only send the summary + link or a chunk of the plan to avoid WhatsApp limits
        # For now, let's send the header and the First Phase
        
        # Simple extraction of Phase 1 for WhatsApp
        phase1_idx = plan_text.find("Phase 1")
        phase2_idx = plan_text.find("Phase 2")
        if phase1_idx != -1:
            end_idx = phase2_idx if phase2_idx != -1 else len(plan_text)
            whatsapp_body = plan_text[phase1_idx:end_idx].strip()
            whatsapp_message += f"\n\n---\n{whatsapp_body}\n---"

        success = WhatsAppService.broadcast_to_group(whatsapp_message)
        
        return {
            "success": success,
            "plan_text": plan_text,
            "summary_text": summary_text
        }
