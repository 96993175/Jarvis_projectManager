import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class IntelligenceService:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("⚠️ WARNING: GROQ_API_KEY not found. AI features will fail.")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
            
    def generate_response(self, user_message: str, context: dict) -> str:
        """
        Generates the helpful response for the user.
        Uses: Hackathon Info + Member Profile + Past Behavior Insights.
        """
        if not self.client: return "AI Error: API Key missing."

        member = context["member"]
        team = context["team"]
        insights = context["insights"]
        
        # Format insights as a bulleted list
        insights_text = "\n".join([f"- {i}" for i in insights]) if insights else "No prior behavioral data."
        
        # Get recent chat history (last 5 messages)
        recent_history = member.get("chat_history", [])[-5:]
        history_text = "\n".join([f"{msg['role'].upper()}: {msg['message']}" for msg in recent_history])

        prompt = f"""
You are Jarvis, an elite AI hackathon coordinator.

=== CURRENT CONTEXT ===
User: {member.get('name')} ({member.get('role')})
Team: {team.get('team_name')}
Problem Statement: {team.get('problem_statement')}
Deadline Duration: {team.get('hackathon', {}).get('duration_hours', 24)}h

=== USER BEHAVIOR & WORK HISTORY ===
(What the user has been working on recently)
{insights_text}

=== RECENT CONVERSATION ===
{history_text}

=== NEW MESSAGE ===
USER: {user_message}

=== INSTRUCTIONS ===
1. Respond naturally and helpfully.
2. Use the 'User Behavior' context to be specific (e.g., if they were debugging earlier, ask if it's fixed).
3. Keep it concise (max 70 words).
4. Be motivating but technical.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are Jarvis. Be helpful, concise, and context-aware."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ AI Gen Error: {e}")
            return "I'm having trouble connecting to my brain right now. Please try again."

    def analyze_behavior(self, user_message: str, ai_response: str, context: dict) -> str:
        """
        The 'Insight Loop'. Analyzes the specific User Request + AI Response pair.
        Extracts: What is the user working on? What is their state?
        """
        if not self.client: return None

        prompt = f"""
Analyze this interaction to extract a 'Behavioral Insight' for the database.
This insight will be used to understand the user's progress in the next turn.

=== INTERACTION ===
USER: {user_message}
AI: {ai_response}

=== CONTEXT ===
Role: {context['member'].get('role')}
Problem: {context['team'].get('problem_statement')}

=== TASK ===
Summarize the user's current status/work in ONE short sentence.
Examples:
- "User is implementing the login schema."
- "User is stuck on a CORS error."
- "User is asking about the deadline."
- "User is brainstorming UI ideas."

OUTPUT ONLY THE SENTENCE. NO MARKDOWN.
"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Extract user status. brief."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3, # Lower temperature for factual extraction
                max_tokens=50
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ Analysis Error: {e}")
            return None

    def generate_project_plan(self, problem_statement: str, prev_context: str = None) -> str:
        """
        Generates a detailed, step-by-step project plan.
        Uses previous plan context if available (Recursive Memory).
        """
        if not self.client: return "AI Error"

        context_str = f"\nPREVIOUS PLAN CONTEXT:\n{prev_context}" if prev_context else ""

        prompt = f"""
You are an expert Project Manager. Create a solid, detailed Step-by-Step Plan to solve this problem.

=== PROBLEM ===
{problem_statement}
{context_str}

=== OUTPUT FORMAT ===
1. **Phase 1: Setup**
   - Step 1.1: ...
2. **Phase 2: MVP**
   - ...

Make it technical, actionable, and robust.
"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a senior tech project manager."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating plan: {e}"

    def summarize_plan(self, plan_text: str) -> str:
        """
        Summarizes the detailed plan into a concise context block.
        This summary is saved to DB to seed the NEXT planning cycle.
        """
        if not self.client: return "AI Error"

        prompt = f"""
Summarize this project plan into a high-level "Context Block" for future reference.
Focus on the key objectives and current phase.

=== PLAN ===
{plan_text[:4000]} # Truncate if too long

=== OUTPUT ===
Concise summary (max 100 words).
"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Summarize technical plans concisely."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=150
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error summarizing plan: {e}"
