from typing import Dict, List, Any, Optional
from .banking_agent import BankingAgent
from .travel_agent import TravelAgent  
from .email_agent import EmailAgent
from ..security.firewall_integration import SecurityManager
import logging
from datetime import datetime

class MultiAgentManager:
    """Orchestrates multiple specialized agents with security oversight"""
    
    def __init__(self):
        # Initialize security manager
        self.security_manager = SecurityManager()
        
        # Initialize specialized agents
        self.agents = {
            "banking": BankingAgent(self.security_manager),
            "travel": TravelAgent(self.security_manager),
            "email": EmailAgent(self.security_manager)
        }
        
        self.logger = logging.getLogger("MultiAgentManager")
        
        # Track active sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    def route_request(self, user_input: str, thread_id: str, user_goal: str = "") -> Dict[str, Any]:
        """Route user request to appropriate agent"""
        try:
            # Initialize session if new
            if thread_id not in self.active_sessions:
                self.active_sessions[thread_id] = {
                    "user_goal": user_goal,
                    "agent_history": [],
                    "created_at": datetime.now().isoformat()
                }
            
            # Determine best agent for request
            selected_agent = self._select_agent(user_input)
            
            if not selected_agent:
                return {
                    "status": "no_agent_match",
                    "message": "I'm not sure which service can help with that request. Could you be more specific?",
                    "available_agents": list(self.agents.keys())
                }
            
            # Track agent usage
            self.active_sessions[thread_id]["agent_history"].append({
                "agent": selected_agent.name,
                "request": user_input[:100],  # Truncate for logging
                "timestamp": datetime.now().isoformat()
            })
            
            # Execute request through selected agent
            result = selected_agent.execute(user_input, thread_id, user_goal)
            
            # Add orchestration metadata
            result.update({
                "routing_info": {
                    "selected_agent": selected_agent.name,
                    "thread_id": thread_id,
                    "session_length": len(self.active_sessions[thread_id]["agent_history"])
                }
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in request routing: {e}")
            return {
                "status": "routing_error",
                "message": "An error occurred while processing your request.",
                "error": str(e)
            }
    
    def _select_agent(self, user_input: str) -> Optional[Any]:
        """Select most appropriate agent based on input analysis"""
        # Score each agent's suitability
        agent_scores = {}
        
        for name, agent in self.agents.items():
            if agent.validate_request(user_input):
                # Simple scoring based on keyword matching
                score = self._calculate_agent_score(user_input, agent)
                agent_scores[name] = score
        
        # Return agent with highest score
        if agent_scores:
            best_agent_name = max(agent_scores, key=agent_scores.get)
            return self.agents[best_agent_name]
        
        return None
    
    def _calculate_agent_score(self, user_input: str, agent) -> float:
        """Calculate relevance score for agent selection"""
        # This could be enhanced with more sophisticated NLP
        capabilities = agent.get_capabilities()
        user_input_lower = user_input.lower()
        
        score = 0
        for capability in capabilities:
            capability_words = capability.lower().split()
            for word in capability_words:
                if word in user_input_lower:
                    score += 1
        
        return score / len(capabilities) if capabilities else 0
    
    def get_session_info(self, thread_id: str) -> Dict[str, Any]:
        """Get information about active session"""
        if thread_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[thread_id]
        security_summary = self.security_manager.get_trace_summary(thread_id)
        
        return {
            "session": session,
            "security_summary": security_summary,
            "available_agents": [
                {
                    "name": name,
                    "capabilities": agent.get_capabilities()
                }
                for name, agent in self.agents.items()
            ]
        }