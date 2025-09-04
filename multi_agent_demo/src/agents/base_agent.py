from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
import logging

class BaseAgent(ABC):
    """Base class for specialized agents with security integration"""

    def __init__(self, 
                 name: str, 
                 tools: List[BaseTool], 
                 system_prompt: str,
                 security_manager=None,
                 model_name: str = "gpt-4"):

        self.name = name
        self.tools = tools
        self.system_prompt = system_prompt
        self.security_manager = security_manager
        self.logger = logging.getLogger(f"Agent.{name}")

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0,
            timeout=30
        )

        # Create agent with memory
        self.memory = MemorySaver()

        # Set system prompt in the LLM
        self.llm_with_prompt = self.llm.with_config(
            {"system_prompt": system_prompt}
        )

        # Create agent with memory
        self.agent_executor = create_react_agent(
            self.llm_with_prompt, 
            self.tools, 
            checkpointer=self.memory
        )

    def execute(self, user_input: str, thread_id: str, user_goal: str = "") -> Dict[str, Any]:
        """Execute agent action with security checks"""
        try:
            # Security check on input
            if self.security_manager:
                input_check = self.security_manager.scan_user_input(user_input, thread_id)
                if not input_check["is_safe"]:
                    return {
                        "status": "blocked",
                        "reason": "Security violation detected",
                        "details": input_check,
                        "agent": self.name
                    }

            # Configure thread for conversation persistence
            config = {"configurable": {"thread_id": thread_id}}

            # Create a HumanMessage from user input
            from langchain_core.messages import HumanMessage
            user_message = HumanMessage(content=user_input)

            # Add user input to security trace first
            if self.security_manager:
                self.security_manager.add_to_trace(thread_id, user_message)

            # Execute agent
            response = self.agent_executor.invoke(
                {"messages": [{"role": "user", "content": user_input}]}, 
                config
            )

            # Add AI response to security trace
            if self.security_manager:
                self.security_manager.add_to_trace(thread_id, response["messages"][-1])

                # Check alignment if user goal provided
                if user_goal:
                    alignment_check = self.security_manager.check_agent_alignment(thread_id, user_goal)
                    if not alignment_check["is_safe"]:
                        return {
                            "status": "alignment_violation",
                            "reason": "Agent behavior misaligned with user goal",
                            "details": alignment_check,
                            "agent": self.name
                        }

            return {
                "status": "success",
                "response": response["messages"][-1].content,
                "agent": self.name,
                "thread_id": thread_id
            }

        except Exception as e:
            self.logger.error(f"Error executing agent {self.name}: {e}")
            return {
                "status": "error",
                "reason": f"Agent execution failed: {str(e)}",
                "agent": self.name
            }

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        pass

    @abstractmethod
    def validate_request(self, user_input: str) -> bool:
        """Validate if request is appropriate for this agent"""
        pass
