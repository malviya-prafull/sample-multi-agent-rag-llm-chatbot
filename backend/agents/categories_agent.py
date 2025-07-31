"""
Categories Agent - Specializes in category-related queries
"""

from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_community.tools import QuerySQLDatabaseTool
from .base_agent import BaseAgent, LOGGER

class CategoriesAgent(BaseAgent):
    """AI Agent specialized in handling category-related queries"""
    
    def __init__(self):
        # Initialize database first, before calling super().__init__()
        self.db = SQLDatabase.from_uri("sqlite:///products.db")
        self.sql_tool = QuerySQLDatabaseTool(db=self.db)
        
        # Now call parent constructor
        super().__init__(
            agent_name="Categories",
            specialization="Product categories, browsing, and navigation"
        )
    
    def _initialize_tools(self) -> List[Any]:
        """Initialize category-specific tools"""
        return [self.sql_tool]
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Create category-specific prompt template"""
        return ChatPromptTemplate.from_template("""
        You are a Categories Expert AI Assistant. Your specialty is helping users discover and navigate product categories.
        
        Your capabilities:
        - List all available categories
        - Explain what products are in each category
        - Suggest categories based on user needs
        - Provide category-based recommendations
        
        Database Schema:
        - categories (id, name)
        - products (id, name, description, price, category_id)
        
        User Query: {query}
        Database Results: {db_results}
        
        Provide a helpful, engaging response about categories. Be enthusiastic about helping users explore different product categories.
        """)
    
    def get_keywords(self) -> List[str]:
        """Keywords this agent specializes in"""
        return [
            "categories", "category", "browse", "explore", "types", "kinds",
            "what do you have", "what's available", "sections", "departments"
        ]
    
    def get_capabilities(self) -> List[str]:
        """Categories agent capabilities"""
        return [
            "List all product categories",
            "Explain category contents",
            "Category-based recommendations",
            "Navigation assistance",
            "Category comparisons"
        ]
    
    def process_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process category-related queries"""
        try:
            LOGGER.info(f"[Categories Agent] Processing query: {query}")
            
            # Execute SQL query to get categories
            if "categories" in query.lower() or "what do you have" in query.lower():
                sql_query = "SELECT name FROM categories;"
                db_results = self.sql_tool.run(sql_query)
                LOGGER.info(f"[Categories Agent] DB Results: {db_results}")
            else:
                # For other category queries, get categories with product counts
                sql_query = """
                SELECT c.name, COUNT(p.id) as product_count 
                FROM categories c 
                LEFT JOIN products p ON c.id = p.category_id 
                GROUP BY c.id, c.name
                ORDER BY product_count DESC;
                """
                db_results = self.sql_tool.run(sql_query)
                LOGGER.info(f"[Categories Agent] DB Results with counts: {db_results}")
            
            # Generate AI response
            response = self.chain.invoke({
                "query": query,
                "db_results": db_results
            })
            
            # Format the response
            formatted_response = self._format_category_response(db_results, response)
            
            return {
                "response": formatted_response,
                "source": "categories_agent",
                "agent": self.agent_name,
                "data": db_results
            }
            
        except Exception as e:
            LOGGER.error(f"[Categories Agent] Error: {e}")
            return {
                "response": f"Sorry, I encountered an error while fetching categories: {str(e)}",
                "source": "categories_agent_error",
                "agent": self.agent_name
            }
    
    def _format_category_response(self, db_results: str, ai_response: str) -> str:
        """Format category response beautifully"""
        try:
            import re
            
            # Extract categories from SQL result
            category_pattern = r"'([^']+)'"
            categories = re.findall(category_pattern, db_results)
            
            if not categories:
                return ai_response
            
            # Category icons
            category_icons = {
                'electronics': '💻',
                'books': '📚',
                'home goods': '🏠',
                'clothing': '👕',
                'sports': '⚽',
                'toys': '🧸'
            }
            
            formatted_categories = []
            for category in categories:
                icon = category_icons.get(category.lower(), '📁')
                formatted_categories.append(f"{icon} **{category}**")
            
            header = f"🏪 **Available Categories ({len(categories)}):**\n\n"
            category_list = "\n".join(formatted_categories)
            
            footer = f"\n\n{ai_response}\n\n💡 *Try asking: \"Show me electronics\" or \"What's in the books category?\"*"
            
            return header + category_list + footer
            
        except Exception as e:
            LOGGER.warning(f"[Categories Agent] Formatting error: {e}")
            return ai_response