# 🛍️ Sample Multi Agent RAG LLM Chatbot - System Architecture Documentation

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [RAG (Retrieval-Augmented Generation)](#rag-retrieval-augmented-generation)
3. [Vector Database](#vector-database)
4. [AI Agents Architecture](#ai-agents-architecture)
5. [System Flow](#system-flow)
6. [Technical Stack](#technical-stack)
7. [Trade-offs and Design Decisions](#trade-offs-and-design-decisions)
8. [API Documentation](#api-documentation)
9. [Deployment Guide](#deployment-guide)

---

## 🎯 System Overview

This is a **sample-multi-agent-rag-llm-chatbot** that combines RAG (Retrieval-Augmented Generation) with specialized AI agents to provide intelligent product search, category browsing, and retailer information.

### Key Features:
- **🤖 Multi-Agent AI System** - Specialized agents for different domains
- **📊 RAG Implementation** - Combines structured (SQL) and unstructured (Vector) data
- **🎨 Modern Frontend** - React-based chat interface with rich formatting
- **🔍 Intelligent Routing** - Smart query routing to appropriate agents
- **📱 Real-time Chat** - WebSocket-like experience with typing indicators

### Architecture Diagram:
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React         │    │   FastAPI        │    │   AI Agents     │
│   Frontend      │◄──►│   Backend        │◄──►│   System        │
│                 │    │                  │    │                 │
│ • Chat UI       │    │ • API Routes     │    │ • Categories    │
│ • Price Display │    │ • Agent Manager  │    │ • Products      │
│ • Retailer Cards│    │ • RAG Pipeline   │    │ • Retailers     │
│ • Responsive    │    │ • Rate Limiting  │    │ • Price Compare │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │
                               ▼
                      ┌──────────────────┐
                      │   Enhanced       │
                      │   Data Layer     │
                      │                  │
                      │ • SQLite DB      │
                      │   - Products     │
                      │   - Categories   │
                      │   - Retailers*   │
                      │ • ChromaDB       │
                      │ • NVIDIA LLM     │
                      └──────────────────┘
                      *Price at retailer level
```

---

## 🧠 RAG (Retrieval-Augmented Generation)

### What is RAG?
RAG is a technique that enhances Large Language Models (LLMs) by providing them with relevant context from external knowledge sources before generating responses.

### Our RAG Implementation:

#### 1. **Dual Data Sources:**
```python
# Structured Data (SQL)
SQLite Database → Product info, categories, retailers, stock levels

# Unstructured Data (Vector)
ChromaDB → Product descriptions, reviews, detailed specifications
```

#### 2. **RAG Pipeline:**
```
User Query → Router → Data Retrieval → Context Injection → LLM Generation → Response
```

#### 3. **Smart Routing Logic:**
- **SQL Route**: Specific product queries, pricing, stock levels
- **Vector Route**: Recommendations, comparisons, detailed descriptions
- **Hybrid Route**: Complex queries requiring both data types

### Benefits of RAG:
✅ **Accuracy**: Real-time access to current product data  
✅ **Relevance**: Context-aware responses  
✅ **Flexibility**: Handles both structured and unstructured queries  
✅ **Transparency**: Can cite sources and show confidence levels

---

## 🗃️ Vector Database

### Why ChromaDB?

We chose **ChromaDB** as our vector database for several reasons:

#### **Pros:**
✅ **Easy Setup**: Minimal configuration required  
✅ **Python Native**: Perfect integration with our FastAPI backend  
✅ **Local Storage**: No external dependencies for development  
✅ **Persistence**: Automatic data persistence to disk  
✅ **Similarity Search**: Built-in cosine similarity search  
✅ **Embedding Support**: Works seamlessly with HuggingFace embeddings

#### **Cons:**
❌ **Scalability**: Limited for very large datasets (>1M vectors)  
❌ **Performance**: Slower than specialized vector DBs like Pinecone  
❌ **Features**: Fewer advanced features compared to enterprise solutions

### Alternative Vector Databases Considered:

| Database | Pros | Cons | Use Case |
|----------|------|------|-----------|
| **FAISS** | Fast, Meta-backed | No persistence, complex setup | High-performance research |
| **Pinecone** | Cloud-native, scalable | Paid service, external dependency | Production at scale |
| **Weaviate** | GraphQL, rich features | Complex setup, resource heavy | Enterprise applications |
| **Qdrant** | High performance, Rust-based | Newer ecosystem | Production systems |

### Vector Storage Implementation:
```python
# Document Processing
Product Description → Text Chunks → Embeddings → ChromaDB Storage

# Retrieval Process
User Query → Query Embedding → Similarity Search → Top-K Documents → Context
```

### Embedding Model:
- **Model**: `all-MiniLM-L6-v2` (HuggingFace)
- **Dimensions**: 384
- **Speed**: Fast inference (~10ms per query)
- **Quality**: Good for general-purpose text similarity

---

## 🗄️ Enhanced Database Schema

### Database Design Philosophy

Our database follows a **realistic e-commerce model** where:
- Products exist independently of pricing
- Multiple retailers sell the same product at different prices
- Retailers have their own location, contact, and rating information

### Schema Overview:
```sql
-- Categories Table
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Products Table (NO PRICE HERE - Moved to retailers!)
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category_id INTEGER,
    brand TEXT,
    model TEXT,
    FOREIGN KEY(category_id) REFERENCES categories(id)
);

-- Retailers Table (Price at retailer level!)
CREATE TABLE retailers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    product_id INTEGER,
    price REAL NOT NULL,         -- ✅ Price here!
    stock INTEGER,
    location TEXT,               -- ✅ Store location
    contact TEXT,                -- ✅ Contact info
    rating REAL,                 -- ✅ Store rating
    FOREIGN KEY(product_id) REFERENCES products(id)
);
```

### Key Schema Benefits:

#### 🏷️ **Realistic Pricing Model:**
```sql
-- Same product, different prices at different retailers
Laptop:
  TechStore (NY): $1,199.99 ⭐⭐⭐⭐⭐
  GadgetHub (LA): $1,249.99 ⭐⭐⭐⭐
  ElectroMart (CHI): $1,179.99 ⭐⭐⭐⭐⭐
```

#### 📊 **Rich Retailer Data:**
- **Location**: Store city/state for local shopping
- **Contact**: Email for customer inquiries  
- **Rating**: 1-5 star rating system
- **Stock**: Real-time inventory levels

#### 💰 **Price Comparison Features:**
```sql
-- Find price ranges for any product
SELECT p.name, 
       MIN(r.price) as cheapest,
       MAX(r.price) as most_expensive,
       AVG(r.price) as average_price,
       COUNT(r.id) as retailer_count
FROM products p 
JOIN retailers r ON p.id = r.product_id 
GROUP BY p.id;
```

### Sample Data Structure:

#### **8 Products Across 3 Categories:**
- **Electronics**: Laptop, Smartphone, Tablet, Headphones (4 products)
- **Books**: Science Fiction Novel, Cookbook (2 products)  
- **Home Goods**: Coffee Maker, Desk Chair (2 products)

#### **34 Retailer Entries:**
- **4-5 retailers per product** for competitive pricing
- **Price ranges**: e.g., Smartphones $789.99 - $829.99
- **Geographic spread**: 20+ cities across US
- **Rating variety**: 4.0 - 4.8 stars average

### Enhanced Vector Store:

#### **Rich Document Content:**
```python
# Enhanced vector documents now include:
enhanced_content = f"""
Product: {name}
Brand: {brand}
Model: {model}
Category: {category_name}
Description: {description}
Price Range: ${min_price:.2f} - ${max_price:.2f}
Average Price: ${avg_price:.2f}

This {name} is a {category_name.lower()} product from {brand}. {description}
Available at multiple retailers with prices ranging from ${min_price:.2f} to ${max_price:.2f}.
"""
```

#### **Rich Metadata:**
```python
metadata = {
    "product_id": product_id,
    "name": name,
    "brand": brand,
    "model": model,
    "category": category_name,
    "min_price": min_price,
    "max_price": max_price,
    "avg_price": avg_price
}
```

---

## 🤖 AI Agents Architecture

### Agent-Based System Design

Instead of a monolithic AI system, we implemented **specialized AI agents** that excel in specific domains.

### Agent Hierarchy:
```
┌─────────────────────┐
│   Agent Manager     │  ← Routes queries to appropriate agents
│   (Orchestrator)    │
└─────────┬───────────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│Categories│ │Products │ │Retailers│
│ Agent   │ │ Agent   │ │ Agent   │
└─────────┘ └─────────┘ └─────────┘
```

### 1. **Categories Agent** 📁
**Specialization**: Product categories, browsing, navigation

**Keywords**: `categories`, `browse`, `explore`, `what do you have`

**Capabilities**:
- List all available categories
- Explain category contents
- Provide category-based recommendations
- Navigation assistance

**SQL Queries**:
```sql
-- Get all categories
SELECT name FROM categories;

-- Get categories with product counts
SELECT c.name, COUNT(p.id) as product_count 
FROM categories c 
LEFT JOIN products p ON c.id = p.category_id 
GROUP BY c.id, c.name;
```

### 2. **Products Agent** 🛍️
**Specialization**: Product search, price ranges, recommendations

**Keywords**: `laptop`, `smartphone`, `books`, `price`, `show me`

**Enhanced Capabilities**:
- **Price Range Display**: Shows min/max prices across retailers
- **Retailer Count**: "Available at 5 retailers" 
- **Smart Comparisons**: Cross-category product analysis
- **Brand & Model Info**: Enhanced product details

**New SQL Queries**:
```sql
-- Price ranges with retailer counts
SELECT p.name, c.name as category, 
       MIN(r.price) as min_price, 
       MAX(r.price) as max_price, 
       COUNT(r.id) as retailer_count
FROM products p 
JOIN categories c ON p.category_id = c.id 
JOIN retailers r ON p.id = r.product_id
WHERE p.name LIKE '%Laptop%' 
GROUP BY p.id, p.name, c.name;
```

**Response Format**:
```
🛍️ **Laptop**
📂 Category: Electronics
💰 Price Range: $1,179.99 - $1,299.99
🏪 Available at: 4 retailers
🖼️ Image: [product_image_url]
```

### 3. **Retailers Agent** 🏪
**Specialization**: Store info, pricing, location, stock, ratings

**Keywords**: `retailers`, `store`, `where to buy`, `stock`, `cheapest`, `best rated`

**Enhanced Capabilities**:
- **Individual Store Pricing**: Exact price per retailer
- **Location Information**: City/state for each store
- **Rating Display**: ⭐⭐⭐⭐⭐ visual ratings
- **Price Comparison**: Automatic savings calculation
- **Stock Status**: Real-time inventory levels

**New SQL Queries**:
```sql
-- Complete retailer information with pricing
SELECT r.name, p.name as product, r.price, r.stock, 
       r.location, r.rating
FROM retailers r 
JOIN products p ON r.product_id = p.id 
WHERE p.name LIKE '%Smartphone%'
ORDER BY r.price ASC;
```

**Enhanced Response Format**:
```
🏬 **Retailers selling Smartphone (5):**

📱 **MobileWorld**
🛍️ Product: Smartphone
💰 Price: $799.99
📊 In Stock: 100 units
📍 Location: San Francisco, CA
⭐ Rating: ⭐⭐⭐⭐⭐ (4.6/5.0)

💡 **Price Comparison:**
• Cheapest: $789.99
• Most Expensive: $829.99  
• Potential Savings: $40.00
```

**Capabilities**:
- Find retailers selling specific products
- Check stock levels and availability
- Provide store information
- Compare retailer options

**Stock Management**:
```python
def get_stock_status(stock):
    if stock > 50: return "🟢 In Stock"
    elif stock > 10: return "🟡 Limited Stock"  
    elif stock > 0: return "🟠 Low Stock"
    else: return "🔴 Out of Stock"
```

### Agent Communication Protocol:
```python
# Standard Agent Response Format
{
    "response": "Formatted response text",
    "source": "agent_name",
    "agent": "Agent Name",
    "data": "Raw database results",
    "routing_confidence": "high|medium|low"
}
```

### Why Agent-Based Architecture?

#### **Benefits:**
✅ **Specialization**: Each agent is expert in its domain  
✅ **Maintainability**: Easy to update/debug individual agents  
✅ **Scalability**: Can add new agents without affecting existing ones  
✅ **Performance**: Targeted processing reduces response time  
✅ **Quality**: Domain-specific prompts produce better responses

#### **Trade-offs:**
❌ **Complexity**: More components to manage  
❌ **Overhead**: Agent routing adds slight latency  
❌ **Memory**: Multiple agent instances use more RAM

---

## 🔄 System Flow

### Complete Request Flow:

```
1. User Input
   ↓
2. Frontend Validation
   ↓
3. API Request to Backend
   ↓
4. Agent Manager Routing
   ↓
5. Agent Selection (Categories/Products/Retailers)
   ↓
6. Database Query Execution
   ↓
7. AI Processing with Context
   ↓
8. Response Formatting
   ↓
9. Frontend Rendering
   ↓
10. User Sees Formatted Response
```

### Detailed Flow Examples:

#### **Example 1: "What products are available?"**
```
User Query → Agent Manager → Products Agent → SQL Database → 
Product List → AI Formatting → Beautiful Product Cards → Frontend Display
```

#### **Example 2: "Show me smartphones"**
```
User Query → Agent Manager → Products Agent → 
SQL Query with Price Aggregation (MIN/MAX/COUNT retailers) → Results → 
Price Range Calculation → Image Mapping → 
Product Cards with Price Ranges + Retailer Count
```

**Enhanced Output:**
```
🛍️ **Smartphone**
📂 Category: Electronics  
💰 Price Range: $789.99 - $829.99
🏪 Available at: 5 retailers
🖼️ Image: [smartphone_image]
```

#### **Example 3: "Who sells smartphones?"**
```
User Query → Agent Manager → Retailers Agent → 
SQL JOIN with Full Retailer Info → Price Sorting → 
Location Mapping → Rating Formatting → 
Retailer Cards with Complete Info + Price Comparison
```

**Enhanced Output:**
```
🏬 **Retailers selling Smartphone (5):**

📱 **GadgetHub**
💰 Price: $789.99 (CHEAPEST!)
📍 Location: Los Angeles, CA  
⭐ Rating: ⭐⭐⭐⭐ (4.2/5.0)
📊 In Stock: 60 units

💡 **Price Comparison:**
• Cheapest: $789.99
• Most Expensive: $829.99
• You Save: $40.00
```

### Fallback Mechanism:
```
Agent Routing Fails → Original RAG Chatbot → 
Vector Search OR Direct LLM → Simple Response
```

---

## 🛠️ Technical Stack

### Backend Technologies:
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Web Framework** | FastAPI | RESTful API, async support |
| **Database** | SQLite | Structured data storage |
| **Vector DB** | ChromaDB | Unstructured data, embeddings |
| **LLM** | NVIDIA Mixtral-8x22B | Natural language generation |
| **Embeddings** | HuggingFace MiniLM | Text vectorization |
| **ORM** | LangChain SQL | Database abstraction |
| **Logging** | Python Logging | System monitoring |

### Frontend Technologies:
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | React 18 | User interface |
| **Styling** | CSS3 + Flexbox | Responsive design |
| **State Management** | React Hooks | Component state |
| **HTTP Client** | Fetch API | Backend communication |
| **Formatting** | Custom Renderers | Rich text display |

### Development Tools:
- **Environment**: Python 3.13, Node.js 18+
- **Package Management**: pip, npm
- **Version Control**: Git
- **API Testing**: Built-in FastAPI docs
- **Logging**: Structured logging with levels

---

## ⚖️ Trade-offs and Design Decisions

### 1. **SQLite vs PostgreSQL**
**Chosen**: SQLite  
**Reason**: Simplicity for demo, zero configuration  
**Trade-off**: Limited concurrent users, no advanced features

### 2. **ChromaDB vs Pinecone**
**Chosen**: ChromaDB  
**Reason**: Local development, no API costs  
**Trade-off**: Less scalable, fewer features

### 3. **React vs Vue.js**
**Chosen**: React  
**Reason**: Larger ecosystem, better job market  
**Trade-off**: Steeper learning curve

### 4. **Multi-Agent vs Single AI**
**Chosen**: Multi-Agent  
**Reason**: Better specialization, maintainability  
**Trade-off**: Added complexity, more resources

### 5. **NVIDIA LLM vs OpenAI**
**Chosen**: NVIDIA  
**Reason**: Free tier, good performance  
**Trade-off**: Rate limiting, less known

### 6. **FastAPI vs Flask**
**Chosen**: FastAPI  
**Reason**: Async support, automatic docs, type hints  
**Trade-off**: Newer ecosystem, learning curve

### 7. **Price at Retailer Level vs Product Level**
**Chosen**: Retailer Level Pricing  
**Reason**: Realistic e-commerce model, price comparison features  
**Benefits**: 
- Multiple retailers per product
- Price competition analysis  
- Location-based shopping
- Rating-based decisions
**Trade-off**: More complex SQL queries, larger database size

### Performance Considerations:

| Aspect | Current Approach | Optimization Potential |
|--------|------------------|----------------------|
| **Response Time** | 500ms-2s | Caching, connection pooling |
| **Concurrent Users** | ~10 | Database upgrade, async processing |
| **Memory Usage** | ~250MB | Model quantization, lazy loading |
| **Storage** | ~100MB (enhanced data) | Data compression, cleanup jobs |
| **SQL Query Complexity** | JOIN operations | Query optimization, indexing |
| **Price Calculations** | Real-time aggregation | Pre-computed price ranges |

---

## 📡 API Documentation

### Core Endpoints:

#### **POST /api/chat**
Primary chat interface

**Request**:
```json
{
  "message": "What smartphones are available?"
}
```

**Enhanced Response**:
```json
{
  "response": "🔍 Found 1 product:\n\n🛍️ **Smartphone**\n📂 Category: Electronics\n💰 Price Range: $789.99 - $829.99\n🏪 Available at: 5 retailers\n🖼️ Image: https://example.com/smartphone.jpg\n\n💡 Ask \"Who sells Smartphone?\" to see specific retailers and their prices!",
  "source": "products_agent (via Products Agent)"
}
```

**Request**:
```json
{
  "message": "Who sells smartphones?"
}
```

**Enhanced Response**:
```json
{
  "response": "🏬 **Retailers selling Smartphone (5):**\n\n📱 **GadgetHub**\n🛍️ Product: Smartphone\n💰 Price: $789.99\n📊 In Stock: 60 units\n📍 Location: Los Angeles, CA\n⭐ Rating: ⭐⭐⭐⭐ (4.2/5.0)\n\n💡 **Price Comparison:**\n• Cheapest: $789.99\n• Most Expensive: $829.99\n• Potential Savings: $40.00",
  "source": "retailers_agent (via Retailers Agent)"
}
```

#### **GET /health**
System health check

**Response**:
```json
{
  "status": "healthy",
  "components": {
    "llm": true,
    "vector_store": true,
    "sql_database": true
  },
  "agents": {
    "overall_health": "healthy",
    "agents": {...}
  }
}
```

#### **GET /agents**
Agent information

**Response**:
```json
{
  "total_agents": 3,
  "agents": {
    "categories": {
      "name": "Categories",
      "specialization": "Product categories, browsing",
      "keywords": ["categories", "browse", "explore"],
      "capabilities": ["List categories", "Navigation"]
    }
  }
}
```

### Error Handling:
- **Rate Limiting**: 429 errors handled gracefully
- **Database Errors**: Fallback to alternative data sources
- **Agent Failures**: Automatic fallback to base chatbot
- **Network Issues**: Retry logic with exponential backoff

---

## 🚀 Deployment Guide

### Local Development Setup:

```bash
# Backend Setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Environment Variables
echo "NVIDIA_API_KEY=your_key_here" > .env
echo "LOG_LEVEL=INFO" >> .env

# Enhanced Database Setup (with retailer-level pricing)
python data_script.py
# Creates SQLite DB with 8 products, 3 categories, 34 retailer entries
# Also creates ChromaDB vector store with enhanced product descriptions

# Start Backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# Frontend Setup
cd frontend
npm install
npm start
```

### Production Deployment:

#### **Backend (Docker)**:
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### **Frontend (Nginx)**:
```dockerfile
FROM node:18 AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
```

### Environment Variables:
```bash
# Required
NVIDIA_API_KEY=nvapi-xxx
LOG_LEVEL=INFO

# Optional
DATABASE_URL=sqlite:///products.db
VECTOR_DB_PATH=./chroma_db
MAX_TOKENS=1024
TEMPERATURE=0.7
```

### Monitoring:
- **Logs**: Structured JSON logging
- **Health Checks**: `/health` endpoint
- **Metrics**: Response times, error rates
- **Alerts**: Failed agent initialization

---

## 🔮 Future Enhancements

### Short Term (1-2 months):
- [ ] Add user authentication  
- [ ] Implement conversation history
- [ ] Real-time stock level updates
- [ ] Geolocation-based retailer filtering
- [ ] Price drop alerts and notifications
- [ ] User wishlist and favorites
- [ ] Product comparison matrix
- [ ] Create admin dashboard for inventory management

### Medium Term (3-6 months):
- [ ] Multi-language support (Hindi, Spanish, etc.)
- [ ] Voice interface with speech recognition
- [ ] Mobile app with push notifications
- [ ] Integration with real e-commerce APIs (Amazon, eBay)
- [ ] Advanced price prediction using ML
- [ ] Retailer performance analytics
- [ ] Social features (reviews, ratings)
- [ ] AR/VR product visualization

### Long Term (6+ months):
- [ ] Multi-tenant architecture
- [ ] Advanced analytics
- [ ] Custom agent creation
- [ ] Enterprise features

---

## 📚 References and Resources

### Documentation:
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [React Documentation](https://react.dev/)

### Model Information:
- [NVIDIA AI Endpoints](https://build.nvidia.com/)
- [HuggingFace Embeddings](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)

### Architecture Patterns:
- [RAG Implementation Patterns](https://arxiv.org/abs/2005.11401)
- [Multi-Agent Systems](https://en.wikipedia.org/wiki/Multi-agent_system)

---

## 📊 Latest Updates & Enhancements

### 🗄️ **Database Schema Revolution** (Latest Update)
We've completely restructured our database to follow real-world e-commerce patterns:

#### **Before vs After:**
| Aspect | Old Schema | New Schema ✅ |
|--------|------------|--------------|
| **Pricing** | Product-level (unrealistic) | Retailer-level (realistic) |
| **Competition** | Single price per product | Multiple prices, price ranges |
| **Retailer Info** | Basic name + stock | Location, contact, ratings |
| **Shopping Experience** | Limited | Full comparison shopping |

#### **New Capabilities:**
- 🏷️ **Price Ranges**: "$789.99 - $829.99" instead of single price
- 🏪 **Retailer Competition**: 4-5 retailers per product
- 📍 **Location Aware**: Store locations across 20+ US cities  
- ⭐ **Rating System**: 1-5 star retailer ratings
- 💰 **Savings Calculator**: Automatic price comparison
- 📊 **Stock Levels**: Real-time inventory tracking

#### **Enhanced Data:**
- **8 Products** across 3 categories (vs 6 before)
- **34 Retailer Entries** (vs 7 before)
- **Rich Metadata**: Brand, model, contact info
- **Vector Store**: Enhanced descriptions with price ranges

#### **User Experience Improvements:**
```
Old: "Laptop - $1200"
New: "Laptop - $1,179.99 - $1,299.99 (Available at 4 retailers)"

Old: Basic retailer list
New: "🏬 TechStore (NY) - $1,199.99 ⭐⭐⭐⭐⭐ - In Stock: 50 units"
```

This update transforms our system from a simple product catalog into a **comprehensive shopping comparison platform**! 🛍️

---

## 👥 Contributing

### Development Guidelines:
1. Follow PEP 8 for Python code
2. Use TypeScript for new React components
3. Add comprehensive logging for new features
4. Include unit tests for business logic
5. Update documentation for API changes

### Code Structure:
```
backend/
├── agents/              # AI agent implementations
├── logger_service.py    # Centralized logging
├── main.py             # FastAPI application
├── data_script.py      # Database initialization
└── requirements.txt    # Python dependencies

frontend/
├── src/
│   ├── App.js          # Main React component
│   └── App.css         # Styling
└── package.json        # Node.js dependencies
```

---

*This document covers the complete system architecture of the Sample Multi Agent RAG LLM Chatbot. For specific implementation details, refer to the code comments and individual module documentation.*