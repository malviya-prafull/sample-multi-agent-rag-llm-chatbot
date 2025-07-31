"""
Products Agent - Specializes in product-related queries
"""

from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_community.tools import QuerySQLDatabaseTool
from .base_agent import BaseAgent, LOGGER

class ProductsAgent(BaseAgent):
    """AI Agent specialized in handling product-related queries"""
    
    def __init__(self):
        # Initialize database first, before calling super().__init__()
        self.db = SQLDatabase.from_uri("sqlite:///products.db")
        self.sql_tool = QuerySQLDatabaseTool(db=self.db)
        
        # Now call parent constructor
        super().__init__(
            agent_name="Products",
            specialization="Product search, details, and recommendations"
        )
    
    def _initialize_tools(self) -> List[Any]:
        """Initialize product-specific tools"""
        return [self.sql_tool]
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Create product-specific prompt template"""
        return ChatPromptTemplate.from_template("""
        You are a Products Expert AI Assistant. Your specialty is helping users find, compare, and learn about products.
        
        Your capabilities:
        - Search for specific products
        - Filter products by category, price, or features
        - Provide product recommendations
        - Compare products
        - Explain product details
        
        Database Schema:
        - products (id, name, description, price, category_id)
        - categories (id, name)
        
        User Query: {query}
        Database Results: {db_results}
        
        Provide detailed, helpful information about the products. Include relevant details like pricing, categories, and recommendations.
        Be enthusiastic and knowledgeable about the products.
        """)
    
    def get_keywords(self) -> List[str]:
        """Keywords this agent specializes in"""
        return [
            "product", "products", "laptop", "smartphone", "phone", "book", "novel",
            "chair", "coffee", "maker", "show me", "find", "search", "price",
            "cost", "buy", "purchase", "electronics", "books", "furniture"
        ]
    
    def get_capabilities(self) -> List[str]:
        """Products agent capabilities"""
        return [
            "Product search and discovery",
            "Price information and comparisons",
            "Product recommendations",
            "Category-based filtering",
            "Product details and specifications"
        ]
    
    def process_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process product-related queries"""
        try:
            LOGGER.info(f"[Products Agent] Processing query: {query}")
            
            # Determine SQL query based on user request
            sql_query = self._generate_sql_query(query)
            LOGGER.info(f"[Products Agent] Generated SQL: {sql_query}")
            
            # Execute SQL query
            db_results = self.sql_tool.run(sql_query)
            LOGGER.info(f"[Products Agent] DB Results: {db_results[:200]}...")
            
            # Generate AI response
            response = self.chain.invoke({
                "query": query,
                "db_results": db_results
            })
            
            # Format the response
            formatted_response = self._format_product_response(db_results, response)
            
            return {
                "response": formatted_response,
                "source": "products_agent",
                "agent": self.agent_name,
                "data": db_results
            }
            
        except Exception as e:
            LOGGER.error(f"[Products Agent] Error: {e}")
            return {
                "response": f"Sorry, I encountered an error while searching for products: {str(e)}",
                "source": "products_agent_error",
                "agent": self.agent_name
            }
    
    def _generate_sql_query(self, query: str) -> str:
        """Generate appropriate SQL query based on user query"""
        query_lower = query.lower()
        
        if "laptop" in query_lower:
            return """
            SELECT p.name, c.name as category, MIN(r.price) as min_price, MAX(r.price) as max_price, COUNT(r.id) as retailer_count
            FROM products p 
            JOIN categories c ON p.category_id = c.id 
            JOIN retailers r ON p.id = r.product_id
            WHERE p.name LIKE '%Laptop%' 
            GROUP BY p.id, p.name, c.name
            LIMIT 5;
            """
        elif "smartphone" in query_lower or "phone" in query_lower:
            return """
            SELECT p.name, c.name as category, MIN(r.price) as min_price, MAX(r.price) as max_price, COUNT(r.id) as retailer_count
            FROM products p 
            JOIN categories c ON p.category_id = c.id 
            JOIN retailers r ON p.id = r.product_id
            WHERE p.name LIKE '%Smartphone%' OR p.name LIKE '%Phone%'
            GROUP BY p.id, p.name, c.name
            LIMIT 5;
            """
        elif "book" in query_lower:
            return """
            SELECT p.name, c.name as category, MIN(r.price) as min_price, MAX(r.price) as max_price, COUNT(r.id) as retailer_count
            FROM products p 
            JOIN categories c ON p.category_id = c.id 
            JOIN retailers r ON p.id = r.product_id
            WHERE c.name = 'Books' 
            GROUP BY p.id, p.name, c.name
            LIMIT 5;
            """
        elif "electronics" in query_lower:
            return """
            SELECT p.name, c.name as category, MIN(r.price) as min_price, MAX(r.price) as max_price, COUNT(r.id) as retailer_count
            FROM products p 
            JOIN categories c ON p.category_id = c.id 
            JOIN retailers r ON p.id = r.product_id
            WHERE c.name = 'Electronics' 
            GROUP BY p.id, p.name, c.name
            LIMIT 5;
            """
        elif "price" in query_lower or "cost" in query_lower:
            return """
            SELECT p.name, c.name as category, MIN(r.price) as min_price, MAX(r.price) as max_price, COUNT(r.id) as retailer_count
            FROM products p 
            JOIN categories c ON p.category_id = c.id 
            JOIN retailers r ON p.id = r.product_id
            GROUP BY p.id, p.name, c.name
            ORDER BY MIN(r.price) 
            LIMIT 10;
            """
        elif "available" in query_lower or "what products" in query_lower or "list products" in query_lower:
            # Simple list when user asks "what products are available"
            return """
            SELECT p.name, c.name as category
            FROM products p 
            JOIN categories c ON p.category_id = c.id 
            ORDER BY c.name, p.name;
            """
        else:
            # Default: show all products with price ranges for specific searches
            return """
            SELECT p.name, c.name as category, MIN(r.price) as min_price, MAX(r.price) as max_price, COUNT(r.id) as retailer_count
            FROM products p 
            JOIN categories c ON p.category_id = c.id 
            JOIN retailers r ON p.id = r.product_id
            GROUP BY p.id, p.name, c.name
            LIMIT 10;
            """
    
    def _format_product_response(self, db_results: str, ai_response: str) -> str:
        """Format product response beautifully"""
        try:
            import re
            
            # Check if this is a simple list query (name, category only)
            simple_pattern = r"\('([^']+)',\s*'([^']+)'\)"
            simple_matches = re.findall(simple_pattern, db_results)
            
            if simple_matches:
                # Simple product list format
                formatted_products = []
                current_category = ""
                
                for name, category in simple_matches:
                    if category != current_category:
                        if current_category:
                            formatted_products.append("")  # Empty line between categories
                        formatted_products.append(f"**{category}:**")
                        current_category = category
                    formatted_products.append(f"• {name}")
                
                products_list = "\n".join(formatted_products)
                return f"🛍️ **Available Products:**\n\n{products_list}\n\n💡 *Ask about specific products for pricing and retailer info!*"
            
            # Extract products from detailed tuple format (name, category, min_price, max_price, retailer_count)
            pattern = r"\('([^']+)',\s*'([^']+)',\s*([0-9.]+),\s*([0-9.]+),\s*([0-9]+)\)"
            matches = re.findall(pattern, db_results)
            
            if not matches:
                return ai_response
            
            formatted_products = []
            for name, category, min_price, max_price, retailer_count in matches:
                # Get dummy image
                image_url = self._get_product_image(name, category)
                
                # Format price range
                min_price_float = float(min_price)
                max_price_float = float(max_price)
                
                if min_price_float == max_price_float:
                    # Same price across all retailers
                    if min_price_float >= 1000:
                        price_formatted = f"${min_price_float:,.0f}"
                    else:
                        price_formatted = f"${min_price_float:.2f}"
                else:
                    # Price range
                    if min_price_float >= 1000:
                        price_formatted = f"${min_price_float:,.0f} - ${max_price_float:,.0f}"
                    else:
                        price_formatted = f"${min_price_float:.2f} - ${max_price_float:.2f}"
                
                # Retailer count info
                retailer_info = f"{retailer_count} retailer{'s' if int(retailer_count) != 1 else ''}"
                
                product_card = f"""🛍️ **{name}**
📂 Category: {category}
💰 Price Range: {price_formatted}
🏪 Available at: {retailer_info}
🖼️ Image: {image_url}

"""
                formatted_products.append(product_card)
            
            header = f"🔍 **Found {len(matches)} product{'s' if len(matches) != 1 else ''}:**\n\n"
            products_list = "".join(formatted_products)
            footer = f"\n{ai_response}\n\n💡 *Ask \"Who sells [product]?\" to see specific retailers and their prices!*"
            
            return header + products_list + footer
            
        except Exception as e:
            LOGGER.warning(f"[Products Agent] Formatting error: {e}")
            return ai_response
    
    def _get_product_image(self, product_name: str, category: str) -> str:
        """Get dummy image for product"""
        product_lower = product_name.lower()
        
        image_map = {
            'laptop': '1', 'smartphone': '2', 'phone': '2', 'book': '3',
            'novel': '3', 'cookbook': '4', 'coffee': '5', 'maker': '5',
            'chair': '6', 'desk': '6'
        }
        
        image_id = '16'  # default
        for keyword, img_id in image_map.items():
            if keyword in product_lower:
                image_id = img_id
                break
        
        return f"https://picsum.photos/200/200?random={image_id}"