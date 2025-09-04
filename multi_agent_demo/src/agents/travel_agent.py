from .base_agent import BaseAgent
from ..tools.travel_tools import travel_tools
from typing import List

class TravelAgent(BaseAgent):
    """Specialized agent for travel planning and booking"""
    
    def __init__(self, security_manager=None):
        system_prompt = """You are an expert travel planning assistant. Your role is to help users with:
        - Searching for flights and accommodations
        - Comparing travel options and prices
        - Making hotel and flight reservations
        
        IMPORTANT GUIDELINES:
        - Always provide multiple options when available
        - Confirm booking details before finalizing reservations
        - Be transparent about prices and policies
        - Consider user preferences and constraints
        - Alert users to any booking requirements or restrictions
        
        Focus on delivering helpful, accurate travel assistance while ensuring all bookings align with user intentions."""
        
        super().__init__(
            name="TravelAgent", 
            tools=travel_tools,
            system_prompt=system_prompt,
            security_manager=security_manager
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            "Search flights and hotels",
            "Compare travel options",
            "Book accommodations", 
            "Travel planning assistance"
        ]
    
    def validate_request(self, user_input: str) -> bool:
        """Check if request is travel-related"""
        travel_keywords = [
            "flight", "hotel", "travel", "book", "reservation", "trip",
            "vacation", "destination", "airport", "accommodation"
        ]
        
        user_input_lower = user_input.lower()
        return any(keyword in user_input_lower for keyword in travel_keywords)