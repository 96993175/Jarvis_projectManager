import sys
import os

# Add parent directory to path to allow imports if run directly
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

# Import the fixed script
from fixed.send_message import send_message

class WhatsAppService:
    GROUP_NAME = "team techora+"  # Configurable group name

    @staticmethod
    def broadcast_to_group(message: str) -> bool:
        """
        Sends a message to the team WhatsApp group.
        Uses the deterministic keyboard-driven workflow.
        """
        print(f"📢 Broadcasting to WhatsApp Group: {WhatsAppService.GROUP_NAME}")
        return send_message(WhatsAppService.GROUP_NAME, message)

    @staticmethod
    def send_dm(contact_name: str, message: str) -> bool:
        """
        Sends a direct message to a specific contact.
        """
        print(f"📩 Sending DM to: {contact_name}")
        return send_message(contact_name, message)
