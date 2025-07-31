"""
Base Agent Class for AI Agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from logger_service import get_logger
import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
LOGGER = get_logger()

class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(self, agent_name: str, specialization: str):
        self.agent_name = agent_name
        self.specialization = specialization
        self.llm = self._initialize_llm()
        self.tools = self._initialize_tools()
        self.prompt_template = self._create_prompt_template()
        self.chain = self._create_chain()
        LOGGER.info(f"✓ {self.agent_name} Agent initialized - Specialization: {self.specialization}")
    
    def _initialize_llm(self) -> ChatNVIDIA:
        """Initialize the LLM for the agent"""
        nvidia_api_key = os.getenv("NVIDIA_API_KEY")
        if not nvidia_api_key:
            raise ValueError("NVIDIA_API_KEY environment variable is required")
        
        return ChatNVIDIA(
            model="mistralai/mixtral-8x22b-instruct-v0.1",
            nvidia_api_key=nvidia_api_key,
            temperature=0.3,  # Lower temperature for more focused responses
            max_tokens=1024
        )
    
    @abstractmethod
    def _initialize_tools(self) -> List[Any]:
        """Initialize agent-specific tools"""
        pass
    
    @abstractmethod
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Create agent-specific prompt template"""
        pass
    
    def _create_chain(self):
        """Create the agent's processing chain"""
        return self.prompt_template | self.llm | StrOutputParser()
    
    @abstractmethod
    def process_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process a query and return results"""
        pass
    
    def can_handle(self, query: str) -> bool:
        """Check if this agent can handle the given query"""
        return any(keyword in query.lower() for keyword in self.get_keywords())
    
    @abstractmethod
    def get_keywords(self) -> List[str]:
        """Return keywords this agent specializes in"""
        pass
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Return agent information"""
        return {
            "name": self.agent_name,
            "specialization": self.specialization,
            "keywords": self.get_keywords(),
            "capabilities": self.get_capabilities()
        }
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        pass