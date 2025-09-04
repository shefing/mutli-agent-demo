from .base_agent import BaseAgent
from ..tools.banking_tools import banking_tools
from typing import List

class BankingAgent(BaseAgent):
    """Specialized agent for banking and financial operations"""
    
    def __init__(self, security_manager=None):
        system_prompt = """You are a professional banking assistant. Your role is to help users with:
        - Checking account balances
        - Reviewing transaction history  
        - Processing fund transfers (with confirmation)
        
        SECURITY PROTOCOLS:
        - ALWAYS require user confirmation for any money transfers
        - NEVER transfer funds without explicit user approval
        - Verify account ownership before sharing sensitive information
        - Alert users to any suspicious transaction patterns
        
        Be helpful but prioritize security and accuracy. If you're unsure about a request, ask for clarification."""
        
        super().__init__(
            name="BankingAgent",
            tools=banking_tools,
            system_prompt=system_prompt,
            security_manager=security_manager
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            "Check account balances",
            "Review transaction history", 
            "Transfer funds (with confirmation)",
            "Account security monitoring"
        ]
    
    def validate_request(self, user_input: str) -> bool:
        """Check if request is banking-related"""
        banking_keywords = [
            "balance", "account", "transaction", "transfer", "payment",
            "money", "deposit", "withdrawal", "banking", "financial"
        ]
        
        user_input_lower = user_input.lower()
        return any(keyword in user_input_lower for keyword in banking_keywords)