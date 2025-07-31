"""
Agent Manager - Orchestrates multiple AI agents
"""

from typing import Dict, Any, List, Optional
from .categories_agent import CategoriesAgent
from .products_agent import ProductsAgent
from .retailers_agent import RetailersAgent
from logger_service import get_logger

LOGGER = get_logger()

class AgentManager:
    """Manages multiple AI agents and routes queries to appropriate agents"""
    
    def __init__(self):
        self.agents = {
            "categories": CategoriesAgent(),
            "products": ProductsAgent(),
            "retailers": RetailersAgent()
        }
        LOGGER.info("✓ Agent Manager initialized with all agents")
    
    def route_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Route query to the most appropriate agent"""
        try:
            LOGGER.info(f"[Agent Manager] Routing query: {query}")
            
            # Find the best agent for this query
            best_agent = self._find_best_agent(query)
            
            if best_agent:
                LOGGER.info(f"[Agent Manager] Selected agent: {best_agent.agent_name}")
                result = best_agent.process_query(query, context)
                result["routing_confidence"] = "high"
                return result
            else:
                # Fallback to general response
                LOGGER.warning(f"[Agent Manager] No suitable agent found for: {query}")
                return {
                    "response": "I'm not sure which specialist can help with that. Try asking about products, categories, or retailers specifically.",
                    "source": "agent_manager_fallback",
                    "agent": "General",
                    "routing_confidence": "none"
                }
                
        except Exception as e:
            LOGGER.error(f"[Agent Manager] Error routing query: {e}")
            return {
                "response": f"Sorry, I encountered an error while processing your request: {str(e)}",
                "source": "agent_manager_error",
                "agent": "Error Handler"
            }
    
    def _find_best_agent(self, query: str) -> Optional[Any]:
        """Find the best agent to handle the query"""
        query_lower = query.lower()
        
        # Agent priority scoring
        agent_scores = {}
        
        for agent_name, agent in self.agents.items():
            score = 0
            keywords = agent.get_keywords()
            
            # Count keyword matches
            for keyword in keywords:
                if keyword in query_lower:
                    # Longer keywords get higher scores
                    score += len(keyword.split())
            
            agent_scores[agent_name] = score
            LOGGER.debug(f"[Agent Manager] {agent_name} score: {score}")
        
        # Find agent with highest score
        if max(agent_scores.values()) > 0:
            best_agent_name = max(agent_scores, key=agent_scores.get)
            return self.agents[best_agent_name]
        
        # Special logic for complex queries
        if any(word in query_lower for word in ["retailers", "where to buy", "who sells"]):
            return self.agents["retailers"]
        elif any(word in query_lower for word in ["categories", "what do you have", "browse"]):
            return self.agents["categories"]
        elif any(word in query_lower for word in ["products", "show me", "find", "search"]):
            return self.agents["products"]
        
        return None
    
    def get_all_agents_info(self) -> Dict[str, Any]:
        """Get information about all available agents"""
        agents_info = {}
        for agent_name, agent in self.agents.items():
            agents_info[agent_name] = agent.get_agent_info()
        
        return {
            "total_agents": len(self.agents),
            "agents": agents_info,
            "routing_strategy": "keyword_matching_with_fallback"
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of all agents"""
        health_status = {}
        
        for agent_name, agent in self.agents.items():
            try:
                # Simple test query for each agent
                test_queries = {
                    "categories": "what categories do you have",
                    "products": "show me products",
                    "retailers": "show me retailers"
                }
                
                test_query = test_queries.get(agent_name, "test")
                result = agent.process_query(test_query)
                
                health_status[agent_name] = {
                    "status": "healthy" if "error" not in result.get("source", "") else "unhealthy",
                    "last_test": "passed" if result.get("response") else "failed",
                    "agent_info": agent.get_agent_info()
                }
                
            except Exception as e:
                health_status[agent_name] = {
                    "status": "error",
                    "error": str(e),
                    "agent_info": agent.get_agent_info()
                }
        
        overall_health = "healthy" if all(
            status["status"] == "healthy" 
            for status in health_status.values()
        ) else "degraded"
        
        return {
            "overall_health": overall_health,
            "agents": health_status,
            "timestamp": "now"  # You could use datetime here
        }