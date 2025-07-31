"""
Retailers Agent - Specializes in retailer-related queries
"""

from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_community.tools import QuerySQLDatabaseTool
from .base_agent import BaseAgent, LOGGER

class RetailersAgent(BaseAgent):
    """AI Agent specialized in handling retailer-related queries"""
    
    def __init__(self):
        # Initialize database first, before calling super().__init__()
        self.db = SQLDatabase.from_uri("sqlite:///products.db")
        self.sql_tool = QuerySQLDatabaseTool(db=self.db)
        
        # Now call parent constructor
        super().__init__(
            agent_name="Retailers",
            specialization="Store locations, stock levels, and retailer information"
        )
    
    def _initialize_tools(self) -> List[Any]:
        """Initialize retailer-specific tools"""
        return [self.sql_tool]
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Create retailer-specific prompt template"""
        return ChatPromptTemplate.from_template("""
        You are a Retailers Expert AI Assistant. Your specialty is helping users find stores, check stock availability, and get retailer information.
        
        Your capabilities:
        - Find retailers selling specific products
        - Check stock levels and availability
        - Provide store information
        - Suggest best places to buy products
        - Compare retailer options
        
        Database Schema:
        - retailers (id, name, product_id, stock)
        - products (id, name, description, price, category_id)
        
        User Query: {query}
        Database Results: {db_results}
        
        Provide helpful information about retailers, stock levels, and where to buy products. 
        Be practical and give actionable advice about shopping and availability.
        """)
    
    def get_keywords(self) -> List[str]:
        """Keywords this agent specializes in"""
        return [
            "retailer", "retailers", "store", "stores", "shop", "shops",
            "where to buy", "who sells", "stock", "availability", "in stock",
            "store location", "buy from", "purchase from"
        ]
    
    def get_capabilities(self) -> List[str]:
        """Retailers agent capabilities"""
        return [
            "Find retailers by product",
            "Check stock availability",
            "Store information and locations",
            "Retailer comparisons",
            "Purchase recommendations"
        ]
    
    def process_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process retailer-related queries"""
        try:
            LOGGER.info(f"[Retailers Agent] Processing query: {query}")
            
            # Generate SQL query based on user request
            sql_query = self._generate_sql_query(query)
            LOGGER.info(f"[Retailers Agent] Generated SQL: {sql_query}")
            
            # Execute SQL query
            db_results = self.sql_tool.run(sql_query)
            LOGGER.info(f"[Retailers Agent] DB Results: {db_results}")
            
            # Generate AI response
            response = self.chain.invoke({
                "query": query,
                "db_results": db_results
            })
            
            # Format the response
            formatted_response = self._format_retailer_response(db_results, response)
            
            return {
                "response": formatted_response,
                "source": "retailers_agent",
                "agent": self.agent_name,
                "data": db_results
            }
            
        except Exception as e:
            LOGGER.error(f"[Retailers Agent] Error: {e}")
            return {
                "response": f"Sorry, I encountered an error while finding retailers: {str(e)}",
                "source": "retailers_agent_error",
                "agent": self.agent_name
            }
    
    def _generate_sql_query(self, query: str) -> str:
        """Generate appropriate SQL query based on user query"""
        query_lower = query.lower()
        
        if "smartphone" in query_lower or "phone" in query_lower:
            return """
            SELECT r.name, p.name as product, r.price, r.stock, r.location, r.rating
            FROM retailers r 
            JOIN products p ON r.product_id = p.id 
            WHERE p.name LIKE '%Smartphone%' OR p.name LIKE '%Phone%'
            ORDER BY r.price ASC;
            """
        elif "laptop" in query_lower:
            return """
            SELECT r.name, p.name as product, r.price, r.stock, r.location, r.rating
            FROM retailers r 
            JOIN products p ON r.product_id = p.id 
            WHERE p.name LIKE '%Laptop%'
            ORDER BY r.price ASC;
            """
        elif "book" in query_lower:
            return """
            SELECT r.name, p.name as product, r.price, r.stock, r.location, r.rating
            FROM retailers r 
            JOIN products p ON r.product_id = p.id 
            JOIN categories c ON p.category_id = c.id
            WHERE c.name = 'Books'
            ORDER BY r.price ASC;
            """
        elif "cheapest" in query_lower or "lowest price" in query_lower:
            return """
            SELECT r.name, p.name as product, r.price, r.stock, r.location, r.rating
            FROM retailers r 
            JOIN products p ON r.product_id = p.id 
            ORDER BY r.price ASC 
            LIMIT 10;
            """
        else:
            # Default: show all retailers with best ratings first
            return """
            SELECT r.name, p.name as product, r.price, r.stock, r.location, r.rating
            FROM retailers r 
            JOIN products p ON r.product_id = p.id 
            ORDER BY r.rating DESC, r.price ASC
            LIMIT 10;
            """
    
    def _format_retailer_response(self, db_results: str, ai_response: str) -> str:
        """Format retailer response beautifully"""
        try:
            import re
            
            # Extract retailers from new tuple format (name, product, price, stock, location, rating)
            pattern = r"'([^']+)',\s*'([^']+)',\s*([0-9.]+),\s*([0-9]+),\s*'([^']*)',\s*([0-9.]+)"
            matches = re.findall(pattern, db_results)
            
            if not matches:
                return ai_response
            
            # Retailer icons
            retailer_icons = {
                'amazon': '📦', 'walmart': '🛒', 'target': '🎯', 'bestbuy': '🔌', 
                'mobileworld': '📱', 'techstore': '💻', 'gadgethub': '🔧',
                'booknook': '📚', 'kitchenplus': '🍳', 'audiostore': '🎵'
            }
            
            formatted_retailers = []
            for retailer_name, product_name, price, stock, location, rating in matches:
                icon = self._get_retailer_icon(retailer_name, retailer_icons)
                stock_status = self._get_stock_status(int(stock))
                
                # Format price
                price_float = float(price)
                if price_float >= 1000:
                    price_formatted = f"${price_float:,.0f}"
                else:
                    price_formatted = f"${price_float:.2f}"
                
                # Format rating
                rating_stars = "⭐" * int(float(rating))
                rating_display = f"{rating_stars} ({rating}/5.0)"
                
                retailer_card = f"""{icon} **{retailer_name}**
🛍️ Product: {product_name}
💰 Price: {price_formatted}
📊 {stock_status}
📍 Location: {location}
⭐ Rating: {rating_display}

"""
                formatted_retailers.append(retailer_card)
            
            product_name = matches[0][1] if matches else "products"
            header = f"🏬 **Retailers selling {product_name} ({len(matches)}):**\n\n"
            retailers_list = "".join(formatted_retailers)
            
            # Add comparison tips
            if len(matches) > 1:
                prices = [float(match[2]) for match in matches]
                min_price = min(prices)
                max_price = max(prices)
                savings = max_price - min_price
                
                if savings > 0:
                    footer = f"\n{ai_response}\n\n💡 **Price Comparison:**\n• Cheapest: ${min_price:.2f}\n• Most Expensive: ${max_price:.2f}\n• Potential Savings: ${savings:.2f}"
                else:
                    footer = f"\n{ai_response}\n\n💡 *All retailers offer the same price for this product!*"
            else:
                footer = f"\n{ai_response}\n\n💡 *This is the only retailer currently selling this product.*"
            
            return header + retailers_list + footer
            
        except Exception as e:
            LOGGER.warning(f"[Retailers Agent] Formatting error: {e}")
            return ai_response
    
    def _get_retailer_icon(self, retailer_name: str, icon_map: Dict[str, str]) -> str:
        """Get appropriate icon for retailer"""
        retailer_lower = retailer_name.lower()
        for keyword, icon in icon_map.items():
            if keyword in retailer_lower:
                return icon
        return '🏪'  # Default store icon
    
    def _get_stock_status(self, stock: int) -> str:
        """Get stock status with color coding"""
        if stock > 50:
            return f"🟢 **In Stock** ({stock} available)"
        elif stock > 10:
            return f"🟡 **Limited Stock** ({stock} available)"
        elif stock > 0:
            return f"🟠 **Low Stock** ({stock} available)"
        else:
            return "🔴 **Out of Stock**"