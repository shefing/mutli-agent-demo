from .base_agent import BaseAgent
from ..tools.email_tools import email_tools
from typing import List

class EmailAgent(BaseAgent):
    """Specialized agent for email management and communication"""
    
    def __init__(self, security_manager=None):
        system_prompt = """You are a professional email management assistant. Your role is to help users with:
        - Reading and organizing emails
        - Drafting professional responses
        - Managing email communications
        
        SECURITY AND PRIVACY PROTOCOLS:
        - NEVER send emails to external addresses without user confirmation
        - Protect sensitive information in email content
        - Maintain professional tone in all communications
        - Verify recipient addresses before sending
        - Ask for confirmation on important or sensitive emails
        
        Always prioritize user privacy and communication security while providing efficient email assistance."""
        
        super().__init__(
            name="EmailAgent",
            tools=email_tools, 
            system_prompt=system_prompt,
            security_manager=security_manager
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            "Read and organize emails",
            "Draft email responses",
            "Send emails (with confirmation)",
            "Email management assistance"
        ]
    
    def validate_request(self, user_input: str) -> bool:
        """Check if request is email-related"""
        email_keywords = [
            "email", "inbox", "message", "send", "reply", "draft",
            "compose", "mail", "correspondence"
        ]
        
        user_input_lower = user_input.lower()
        return any(keyword in user_input_lower for keyword in email_keywords)