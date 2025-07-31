from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain.chains import create_sql_query_chain
from langchain_community.tools import QuerySQLDatabaseTool
from operator import itemgetter
from typing import Dict, Any, List
import time
import asyncio

load_dotenv()

# Import logger
from logger_service import get_logger
LOGGER = get_logger()

app = FastAPI(title="Sample Multi Agent RAG LLM Chatbot API", description="A sample multi-agent RAG LLM chatbot with specialized AI agents using LangChain", docs_url=None, redoc_url=None)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    source: str  # "sql", "vector", "llm"

class RAGChatbot:
    def __init__(self):
        self.llm = None
        self.embeddings = None
        self.vector_store = None
        self.retriever = None
        self.db = None
        self.sql_chain = None
        self.vector_chain = None
        self.router_chain = None
        self.initialize_components()
        
    def initialize_components(self):
        """Initialize all LangChain components"""
        LOGGER.info("Initializing RAG Chatbot components...")
        
        # Get NVIDIA API key from environment
        self.nvidia_api_key = os.getenv("NVIDIA_API_KEY")
        if not self.nvidia_api_key:
            LOGGER.error("NVIDIA_API_KEY not found in environment variables")
            raise ValueError("NVIDIA_API_KEY environment variable is required")
        
        # Initialize LLM with environment variable
        model_name = "mistralai/mixtral-8x22b-instruct-v0.1"
        self.llm = ChatNVIDIA(
            model=model_name,
            nvidia_api_key=self.nvidia_api_key,
            temperature=0.7,
            max_tokens=1024
        )
        LOGGER.info("✓ LLM initialized with API key from environment")
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        LOGGER.info("✓ Embeddings initialized")
        
        # Initialize vector store
        try:
            self.vector_store = Chroma(persist_directory="./chroma_db", embedding_function=self.embeddings)
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
            self._setup_vector_chain()
            LOGGER.info("✓ Vector store and retriever initialized")
        except Exception as e:
            LOGGER.warning(f"⚠ Vector store initialization failed: {e}")
            
        # Initialize SQL database
        try:
            self.db = SQLDatabase.from_uri("sqlite:///products.db")
            self._setup_sql_chain()
            LOGGER.info("✓ SQL database initialized")
        except Exception as e:
            LOGGER.warning(f"⚠ SQL database initialization failed: {e}")
            
        # Setup router
        self._setup_router()
        LOGGER.info("✓ RAG Chatbot fully initialized")
        
    def _setup_vector_chain(self):
        """Setup LangChain for vector search"""
        if not self.retriever:
            return
            
        vector_prompt = ChatPromptTemplate.from_template("""
        You are a helpful assistant. Answer the user's question based on the provided context.
        If the context doesn't contain enough information to answer the question, say so.
        
        Context: {context}
        
        Question: {question}
        
        Answer:
        """)
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
            
        self.vector_chain = (
            {
                "context": itemgetter("question") | self.retriever | format_docs,
                "question": itemgetter("question")
            }
            | vector_prompt
            | self.llm
            | StrOutputParser()
        )
        
    def _setup_sql_chain(self):
        """Setup LangChain for SQL queries"""
        if not self.db:
            return
            
        # Create custom SQL query generation chain with proper table info
        sql_query_prompt = PromptTemplate.from_template(
           """Given an input question, first create a syntactically correct SQLite query to run.
           Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 5 results.
           You can order the results by a relevant column to return the most interesting examples in the database.
           Never query for all columns from a specific table, only return the relevant columns given the question.
           
           IMPORTANT: The database has these tables:
           - products (id, name, description, price, category_id)
           - categories (id, name) 
           - retailers (id, name, product_id, stock)
           
           To get category names, you MUST JOIN with categories table using category_id.

           Here are correct examples:
           - List all products: SELECT p.name, c.name as category, p.price FROM products p JOIN categories c ON p.category_id = c.id LIMIT 5;
           - Show me electronics: SELECT p.name, p.price FROM products p JOIN categories c ON p.category_id = c.id WHERE c.name = 'Electronics' LIMIT 5;
           - What retailers sell products: SELECT r.name, p.name FROM retailers r JOIN products p ON r.product_id = p.id LIMIT 5;

           Question: {question}
           SQLQuery:""")
        
        sql_query_chain = (
            sql_query_prompt
            | self.llm.bind(stop=["\nSQLResult:"])
            | StrOutputParser()
        )
        
        # Create SQL execution tool
        sql_tool = QuerySQLDatabaseTool(db=self.db)
        
        # Create response generation prompt
        sql_response_prompt = ChatPromptTemplate.from_template("""
        Based on the user's question and the SQL query results, provide a natural language response.
        
        Question: {question}
        SQL Result: {result}
        
        Provide a clear and helpful answer:
        """)
        
        # Chain everything together
        self.sql_chain = (
            {
                "question": itemgetter("question"),
                "result": itemgetter("question") | sql_query_chain | sql_tool
            }
            | sql_response_prompt
            | self.llm
            | StrOutputParser()
        )
        
    def _setup_router(self):
        """Setup intelligent routing between SQL and Vector search"""
        router_prompt = ChatPromptTemplate.from_template("""
        You are an expert at routing user questions to the appropriate data source.
        
        Given a user question, choose the best source:
        - Use "SQL" for questions about specific product information, prices, categories, stock, retailers
        - Use "VECTOR" for general questions, recommendations, comparisons, or conceptual queries
        - Use "LLM" for greetings, general conversation, or questions unrelated to products
        
        Question: {question}
        
        Respond with only one word: SQL, VECTOR, or LLM
        """)
        
        self.router_chain = (
            {"question": itemgetter("question")}
            | router_prompt 
            | self.llm 
            | StrOutputParser()
        )
        
    def _get_product_image(self, product_name: str, category: str) -> str:
        """Get dummy image URL based on product name and category"""
        # Using picsum.photos for dummy images with different seeds for variety
        product_lower = product_name.lower()
        
        # Map products to appropriate image IDs from picsum
        image_map = {
            'laptop': '1',
            'smartphone': '2', 
            'phone': '2',
            'book': '3',
            'novel': '3',
            'cookbook': '4',
            'coffee': '5',
            'maker': '5',
            'chair': '6',
            'desk': '6',
            'tablet': '7',
            'watch': '8',
            'headphones': '9',
            'speaker': '10',
            'camera': '11',
            'mouse': '12',
            'keyboard': '13',
            'monitor': '14',
            'printer': '15'
        }
        
        # Find matching image ID
        image_id = '16'  # default
        for keyword, img_id in image_map.items():
            if keyword in product_lower:
                image_id = img_id
                break
        
        # Return placeholder image URL
        return f"https://picsum.photos/200/200?random={image_id}"

    def _format_product_results(self, raw_result: str) -> str:
        """Format SQL results into a beautiful product display"""
        try:
            import re
            
            # Check if this is a categories result like [('Electronics',), ('Books',), ('Home Goods',)]
            category_pattern = r"\('([^']+)',\)"
            category_matches = re.findall(category_pattern, raw_result)
            
            if category_matches:
                return self._format_category_results(category_matches)
            
            # Check if this is a simple product list (name, category only)
            simple_pattern = r"\('([^']+)',\s*'([^']+)'\)"
            simple_matches = re.findall(simple_pattern, raw_result)
            
            if simple_matches and not any(char.isdigit() for char in raw_result if char not in "(),'"):
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
            
            # Check if this is a retailers result like [('MobileWorld', 'Smartphone', 100)]
            retailer_pattern = r"\('([^']+)',\s*'([^']+)',\s*([0-9]+)\)"
            retailer_matches = re.findall(retailer_pattern, raw_result)
            
            if retailer_matches and not raw_result.count('.') > 0:  # No decimal prices, likely retailers
                return self._format_retailer_results(retailer_matches)
            
            # Extract products from tuple format like ('Laptop', 'Electronics', 1200.0)
            pattern = r"\('([^']+)',\s*'([^']+)',\s*([0-9.]+)\)"
            matches = re.findall(pattern, raw_result)
            
            if not matches:
                # Fallback for different formats
                return f"Here are the results:\n\n{raw_result}"
            
            formatted_products = []
            for i, (name, category, price) in enumerate(matches):
                # Get dummy image
                image_url = self._get_product_image(name, category)
                
                # Format price
                price_float = float(price)
                if price_float >= 1000:
                    price_formatted = f"${price_float:,.0f}"
                else:
                    price_formatted = f"${price_float:.2f}"
                
                # Create product card
                product_card = f"""🛍️ **{name}**
📂 Category: {category}
💰 Price: {price_formatted}
🖼️ Image: {image_url}

"""
                formatted_products.append(product_card)
            
            # Create header
            count = len(matches)
            header = f"🔍 **Found {count} product{'s' if count != 1 else ''}:**\n\n"
            
            # Combine all
            result = header + "".join(formatted_products)
            
            # Add footer with suggestions
            footer = "💡 *Try asking for specific categories like 'electronics' or 'books'*"
            
            return result + footer
            
        except Exception as e:
            LOGGER.warning(f"[Format] Failed to format results: {e}")
            return f"Here are the products I found:\n\n{raw_result}"

    def _format_category_results(self, categories: list) -> str:
        """Format category results into a beautiful display"""
        try:
            # Category icons mapping
            category_icons = {
                'electronics': '💻',
                'books': '📚',
                'home goods': '🏠',
                'clothing': '👕',
                'sports': '⚽',
                'toys': '🧸',
                'automotive': '🚗',
                'beauty': '💄',
                'health': '💊',
                'food': '🍕',
                'music': '🎵',
                'games': '🎮'
            }
            
            # Category descriptions
            category_descriptions = {
                'electronics': 'Laptops, smartphones, gadgets & tech accessories',
                'books': 'Fiction, non-fiction, educational & reference books',
                'home goods': 'Furniture, kitchen appliances & home decor',
                'clothing': 'Fashion, apparel & accessories',
                'sports': 'Sports equipment & fitness gear',
                'toys': 'Kids toys, games & educational items',
                'automotive': 'Car accessories & automotive tools',
                'beauty': 'Cosmetics, skincare & beauty products',
                'health': 'Health supplements & wellness products',
                'food': 'Groceries, snacks & beverages',
                'music': 'Musical instruments & audio equipment',
                'games': 'Video games & board games'
            }
            
            formatted_categories = []
            for category in categories:
                category_lower = category.lower()
                icon = category_icons.get(category_lower, '📁')
                description = category_descriptions.get(category_lower, 'Various products and items')
                
                category_card = f"""{icon} **{category}**
📝 {description}
🔍 *Try: "Show me {category_lower}"*

"""
                formatted_categories.append(category_card)
            
            # Create header
            count = len(categories)
            header = f"🏪 **Available Categories ({count}):**\n\n"
            
            # Combine all
            result = header + "".join(formatted_categories)
            
            # Add footer with navigation help
            footer = """🎯 **Quick Actions:**
• Ask "Show me electronics" to see tech products
• Ask "What laptops do you have?" for specific items
• Ask "Show me books under $20" for filtered results"""
            
            return result + footer
            
        except Exception as e:
            LOGGER.warning(f"[Format] Failed to format category results: {e}")
            return f"Here are the available categories:\n\n{', '.join(categories)}"

    def _format_retailer_results(self, retailers: list) -> str:
        """Format retailer results into a beautiful display"""
        try:
            # Retailer type icons mapping
            retailer_icons = {
                'amazon': '📦',
                'walmart': '🛒',
                'target': '🎯',
                'bestbuy': '🔌',
                'apple': '🍎',
                'samsung': '📱',
                'mobilworld': '📱',
                'mobileworld': '📱',
                'techstore': '💻',
                'bookstore': '📚',
                'homestore': '🏠',
                'electronics': '⚡',
                'gadget': '🔧',
                'phone': '📞',
                'computer': '💻'
            }
            
            # Stock status
            def get_stock_status(stock):
                stock_num = int(stock)
                if stock_num > 50:
                    return f"🟢 **In Stock** ({stock_num} available)"
                elif stock_num > 10:
                    return f"🟡 **Limited Stock** ({stock_num} available)"
                elif stock_num > 0:
                    return f"🟠 **Low Stock** ({stock_num} available)"
                else:
                    return "🔴 **Out of Stock**"
            
            # Get retailer icon
            def get_retailer_icon(retailer_name):
                retailer_lower = retailer_name.lower()
                for keyword, icon in retailer_icons.items():
                    if keyword in retailer_lower:
                        return icon
                return '🏪'  # Default store icon
            
            formatted_retailers = []
            for retailer_name, product_name, stock in retailers:
                icon = get_retailer_icon(retailer_name)
                stock_status = get_stock_status(stock)
                
                retailer_card = f"""{icon} **{retailer_name}**
🛍️ Product: {product_name}
📊 {stock_status}
📍 *Contact store for pricing and availability*

"""
                formatted_retailers.append(retailer_card)
            
            # Create header
            count = len(retailers)
            product_name = retailers[0][1] if retailers else "products"
            header = f"🏬 **Retailers selling {product_name} ({count}):**\n\n"
            
            # Combine all
            result = header + "".join(formatted_retailers)
            
            # Add footer with tips
            footer = """💡 **Shopping Tips:**
• Check stock availability before visiting
• Compare prices across different retailers
• Ask about warranty and return policies
• Consider online vs in-store pickup options"""
            
            return result + footer
            
        except Exception as e:
            LOGGER.warning(f"[Format] Failed to format retailer results: {e}")
            return f"Here are the retailers:\n\n{', '.join([r[0] for r in retailers])}"

    def _route_question(self, question: str) -> str:
        """Route question to appropriate chain"""
        LOGGER.debug(f"[Router] Analyzing question: {question}")
        
        if not self.router_chain:
            # Fallback to simple keyword routing
            LOGGER.debug("[Router] Using keyword-based routing (no LLM router available)")
            if any(keyword in question.lower() for keyword in 
                   ["product", "price", "stock", "category", "laptop", "smartphone", "cost", "buy"]):
                LOGGER.debug("[Router] Keyword match -> SQL")
                return "SQL"
            elif any(keyword in question.lower() for keyword in 
                     ["recommend", "suggest", "best", "compare", "like", "similar"]):
                LOGGER.debug("[Router] Keyword match -> VECTOR")
                return "VECTOR"
            else:
                LOGGER.debug("[Router] No keyword match -> LLM")
                return "LLM"
        
        try:
            LOGGER.debug("[Router] Using LLM-based routing")
            route = self.router_chain.invoke({"question": question}).strip().upper()
            LOGGER.debug(f"[Router] LLM suggested route: {route}")
            
            if route in ["SQL", "VECTOR", "LLM"]:
                LOGGER.info(f"[Router] Final route decision: {route}")
                return route
            
            LOGGER.warning(f"[Router] Invalid route '{route}' from LLM, defaulting to LLM")
            return "LLM"  # Default fallback
        except Exception as e:
            LOGGER.warning(f"[Router] LLM routing failed: {e}, falling back to keyword routing")
            # Fallback to keyword routing
            if any(keyword in question.lower() for keyword in 
                   ["product", "price", "stock", "category", "laptop", "smartphone", "cost", "buy"]):
                return "SQL"
            elif any(keyword in question.lower() for keyword in 
                     ["recommend", "suggest", "best", "compare", "like", "similar"]):
                return "VECTOR"
            else:
                return "LLM"
            
    def _handle_rate_limit_error(self, error_msg: str) -> Dict[str, Any]:
        """Handle rate limit errors with helpful messages"""
        if "429" in str(error_msg) or "Too Many Requests" in str(error_msg):
            LOGGER.warning(f"[Rate Limit] NVIDIA API rate limit exceeded: {error_msg}")
            return {
                "response": "I'm happy you're chatting with me! However, the NVIDIA API rate limit has been exceeded. Please try again in a few seconds. 😊\n\nAlternatively, you can ask:\n• 'What products do you have?' (answered from database)\n• General questions about products and categories",
                "source": "rate_limit"
            }
        LOGGER.error(f"[Error Handler] Unhandled error: {error_msg}")
        return {
            "response": f"Sorry, I encountered an error: {str(error_msg)}", 
            "source": "error"
        }

    async def _retry_with_backoff(self, func, *args, max_retries=2, **kwargs):
        """Retry function with exponential backoff for rate limits"""
        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "Too Many Requests" in error_str:
                    if attempt < max_retries:
                        wait_time = (2 ** attempt) + 1  # 1, 3, 5 seconds
                        LOGGER.warning(f"Rate limit hit, waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                        await asyncio.sleep(wait_time)
                        continue
                raise e

    def chat(self, message: str) -> Dict[str, Any]:
        """Main chat function using LangChain with rate limit handling"""
        try:
            # Route the question
            route = self._route_question(message)
            LOGGER.debug(f"Routing to: {route}")
            
            # For SQL and Vector routes, try without LLM first (no rate limits)
            if route == "SQL" and self.sql_chain:
                try:
                    # Try to get SQL results without LLM processing first
                    from langchain_community.tools import QuerySQLDatabaseTool
                    sql_tool = QuerySQLDatabaseTool(db=self.db)
                    
                    # Simple product queries that can be answered directly from SQL
                    if any(word in message.lower() for word in ["products", "laptop", "smartphone", "price", "categories", "retailers", "electronics", "books"]):
                        sql_query = None
                        if "laptop" in message.lower():
                            sql_query = "SELECT p.name, c.name as category, MIN(r.price) as min_price, MAX(r.price) as max_price FROM products p JOIN categories c ON p.category_id = c.id JOIN retailers r ON p.id = r.product_id WHERE p.name LIKE '%Laptop%' GROUP BY p.id LIMIT 5;"
                        elif "smartphone" in message.lower():
                            sql_query = "SELECT p.name, c.name as category, MIN(r.price) as min_price, MAX(r.price) as max_price FROM products p JOIN categories c ON p.category_id = c.id JOIN retailers r ON p.id = r.product_id WHERE p.name LIKE '%Smartphone%' GROUP BY p.id LIMIT 5;"
                        elif "electronics" in message.lower():
                            sql_query = "SELECT p.name, c.name as category, MIN(r.price) as min_price, MAX(r.price) as max_price FROM products p JOIN categories c ON p.category_id = c.id JOIN retailers r ON p.id = r.product_id WHERE c.name = 'Electronics' GROUP BY p.id LIMIT 5;"
                        elif "books" in message.lower():
                            sql_query = "SELECT p.name, c.name as category, MIN(r.price) as min_price, MAX(r.price) as max_price FROM products p JOIN categories c ON p.category_id = c.id JOIN retailers r ON p.id = r.product_id WHERE c.name = 'Books' GROUP BY p.id LIMIT 5;"
                        elif "categories" in message.lower():
                            sql_query = "SELECT name FROM categories;"
                        elif "retailers" in message.lower():
                            sql_query = "SELECT r.name, p.name as product, r.price, r.stock FROM retailers r JOIN products p ON r.product_id = p.id LIMIT 5;"
                        elif "what products" in message.lower() or "products available" in message.lower():
                            sql_query = "SELECT p.name, c.name as category FROM products p JOIN categories c ON p.category_id = c.id ORDER BY c.name, p.name;"
                        elif "products" in message.lower():
                            sql_query = "SELECT p.name, c.name as category, MIN(r.price) as min_price, MAX(r.price) as max_price FROM products p JOIN categories c ON p.category_id = c.id JOIN retailers r ON p.id = r.product_id GROUP BY p.id LIMIT 10;"
                        
                        if sql_query:
                            LOGGER.info(f"[SQL Direct] Executing query: {sql_query}")
                            result = sql_tool.run(sql_query)
                            LOGGER.info(f"[SQL Direct] Query result: {result[:200]}..." if len(str(result)) > 200 else f"[SQL Direct] Query result: {result}")
                            
                            if result:
                                # Parse and format the SQL result for better presentation
                                formatted_response = self._format_product_results(result)
                                LOGGER.info(f"[SQL Direct] Formatted response length: {len(formatted_response)} chars")
                                return {"response": formatted_response, "source": "sql_direct"}
                        else:
                            # Use the full SQL chain with retry
                            LOGGER.info(f"[SQL Chain] Processing complex query: {message}")
                            response = self.sql_chain.invoke({"question": message})
                            LOGGER.info(f"[SQL Chain] Response: {response[:200]}..." if len(str(response)) > 200 else f"[SQL Chain] Response: {response}")
                            return {"response": response, "source": "sql"}
                    
                    # For complex queries, use full chain with retry
                    response = self.sql_chain.invoke({"question": message})
                    return {"response": response, "source": "sql"}
                    
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "Too Many Requests" in error_str:
                        return self._handle_rate_limit_error(error_str)
                    LOGGER.warning(f"SQL chain failed: {e}")
                    # Fallback to vector search
                    route = "VECTOR"
            
            if route == "VECTOR" and self.vector_chain:
                try:
                    # For vector search, get docs first and create simple response
                    LOGGER.info(f"[Vector] Retrieving documents for query: {message}")
                    docs = self.retriever.invoke(message)
                    LOGGER.info(f"[Vector] Retrieved {len(docs)} documents")
                    
                    if docs:
                        # Log document details
                        for i, doc in enumerate(docs[:3]):  # Log first 3 docs
                            LOGGER.debug(f"[Vector] Doc {i+1}: {doc.page_content[:100]}...")
                        
                        context = "\n".join([doc.page_content for doc in docs[:2]])  # Limit context
                        simple_response = f"Based on your question, here's the relevant information:\n\n{context}\n\nWould you like to know about any specific product?"
                        LOGGER.info(f"[Vector Direct] Generated response length: {len(simple_response)} chars")
                        return {"response": simple_response, "source": "vector_direct"}
                    
                    # If no docs found, try with LLM
                    LOGGER.info(f"[Vector Chain] No relevant docs found, using LLM chain for: {message}")
                    response = self.vector_chain.invoke({"question": message})
                    LOGGER.info(f"[Vector Chain] LLM response: {response[:200]}..." if len(str(response)) > 200 else f"[Vector Chain] LLM response: {response}")
                    return {"response": response, "source": "vector"}
                    
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "Too Many Requests" in error_str:
                        return self._handle_rate_limit_error(error_str)
                    LOGGER.warning(f"Vector chain failed: {e}")
                    # Fallback to simple response
                    route = "SIMPLE"
            
            # Simple responses for common queries (no LLM needed)
            if route == "LLM" or route == "SIMPLE":
                LOGGER.info(f"[LLM/Simple] Processing general query: {message}")
                
                simple_responses = {
                    "hi": "Hello! I'm your shopping assistant and I can help you with product searches. You can ask me:\n• 'What products are available?'\n• 'Show me laptops'\n• 'Smartphone prices'",
                    "hello": "Hello! I'm your shopping assistant. How can I help you today?",
                    "help": "I can help you with:\n• Product search\n• Price information\n• Category-wise products\n• Retailer information\n• Product recommendations",
                    "thanks": "You're welcome! 😊 Is there anything else you'd like to know?",
                    "thank you": "I'm happy to help! 😊 Feel free to ask more questions."
                }
                
                message_lower = message.lower().strip()
                for key, response in simple_responses.items():
                    if key in message_lower:
                        LOGGER.info(f"[Simple Response] Matched keyword '{key}' -> returning pre-defined response")
                        return {"response": response, "source": "simple"}
                
                # Generic fallback without LLM
                LOGGER.info("[Fallback] No specific handler found, returning generic help message")
                return {
                    "response": "I didn't quite understand that. Please try asking something specific like:\n• 'Show me products'\n• 'Laptop prices'\n• 'What categories are available?'\n• 'Show me electronics'",
                    "source": "fallback"
                }
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "Too Many Requests" in error_str:
                return self._handle_rate_limit_error(error_str)
            LOGGER.error(f"Chat error: {e}")
            return {
                "response": f"Sorry, I encountered an error: {str(e)}", 
                "source": "error"
            }

# Initialize the chatbot and agent manager
chatbot = RAGChatbot()

# Initialize AI Agents
from agents.agent_manager import AgentManager
agent_manager = AgentManager()

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    import time
    start_time = time.time()
    
    LOGGER.info(f"[API] Received chat request: '{request.message}' (length: {len(request.message)} chars)")
    
    try:
        # Try AI agents first
        agent_result = agent_manager.route_query(request.message)
        
        if agent_result.get("routing_confidence") == "high":
            # Agent handled the query successfully
            processing_time = time.time() - start_time
            response_length = len(agent_result["response"])
            
            LOGGER.info(f"[API] Agent response - Agent: {agent_result.get('agent', 'Unknown')}, Source: {agent_result['source']}, Length: {response_length} chars, Time: {processing_time:.2f}s")
            
            return ChatResponse(
                response=agent_result["response"],
                source=f"{agent_result['source']} (via {agent_result.get('agent', 'AI Agent')})"
            )
        else:
            # Fallback to original chatbot
            LOGGER.info("[API] Falling back to original RAG chatbot")
            result = chatbot.chat(request.message)
            
            processing_time = time.time() - start_time
            response_length = len(result["response"])
            
            LOGGER.info(f"[API] Chatbot response - Source: {result['source']}, Length: {response_length} chars, Time: {processing_time:.2f}s")
            
            return ChatResponse(
                response=result["response"],
                source=result["source"]
            )
    except Exception as e:
        processing_time = time.time() - start_time
        LOGGER.error(f"[API] Chat endpoint failed after {processing_time:.2f}s: {e}")
        
        return ChatResponse(
            response=f"Sorry, I encountered an error: {str(e)}",
            source="api_error"
        )

@app.get("/")
def read_root():
    return {
        "message": "RAG Chatbot API is running!",
        "features": ["SQL Database", "Vector Search", "LangChain Integration"],
        "endpoints": ["/api/chat", "/health"]
    }

@app.get("/health")
def health_check():
    # Get agent health status
    agent_health = agent_manager.health_check()
    
    return {
        "status": "healthy",
        "components": {
            "llm": chatbot.llm is not None,
            "vector_store": chatbot.vector_store is not None,
            "sql_database": chatbot.db is not None,
            "sql_chain": chatbot.sql_chain is not None,
            "vector_chain": chatbot.vector_chain is not None,
            "router": chatbot.router_chain is not None
        },
        "agents": agent_health
    }

@app.get("/agents")
def get_agents_info():
    """Get information about all available AI agents"""
    return agent_manager.get_all_agents_info()

@app.get("/agents/health")
def get_agents_health():
    """Get detailed health check for all agents"""
    return agent_manager.health_check()

