# 🛍️ Sample Multi Agent RAG LLM Chatbot

A comprehensive **sample-multi-agent-rag-llm-chatbot** that combines **Retrieval-Augmented Generation (RAG)** with specialized AI agents to provide intelligent product search, category browsing, and retailer comparison.

![React](https://img.shields.io/badge/React-18-blue?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![LangChain](https://img.shields.io/badge/LangChain-0.2-purple)
![NVIDIA](https://img.shields.io/badge/NVIDIA%20LLM-Mixtral--8x22B-green?logo=nvidia)

## 🌟 Features

### 🤖 **Multi-Agent AI System**
- **Categories Agent** 📁 - Product categories and navigation
- **Products Agent** 🛍️ - Product search with price ranges
- **Retailers Agent** 🏪 - Store comparison with locations & ratings

### 🏷️ **Realistic E-commerce Model**
- **Price Competition** - Multiple retailers per product with different prices
- **Location-Aware** - Store locations across 20+ US cities
- **Rating System** - 1-5 star retailer ratings
- **Price Comparison** - Automatic savings calculation

### 📊 **Advanced RAG Implementation**
- **Dual Data Sources** - SQLite (structured) + ChromaDB (vector)
- **Smart Routing** - Query-based agent selection
- **Enhanced Context** - Rich product descriptions with pricing

### 🎨 **Modern Frontend**
- **Real-time Chat** - WebSocket-like experience
- **Rich Formatting** - Product cards with images, prices, ratings
- **Responsive Design** - Works on desktop and mobile
- **Price Display** - Beautiful price ranges and comparisons

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+
- NVIDIA API Key ([Get it here](https://build.nvidia.com/))

### ⚡ One-Click Start (Recommended)

**Linux/macOS:**
```bash
# Start both backend and frontend
./start.sh

# Stop services
./stop.sh
```

**Windows:**
```batch
# Start both backend and frontend
start.bat

# Stop services
stop.bat
```

### 🔧 Development Mode

**Start individual services:**

```bash
# Backend only (Linux/macOS)
./dev-backend.sh

# Frontend only (Linux/macOS)  
./dev-frontend.sh
```

### 📖 Manual Setup

<details>
<summary>Click to expand manual setup instructions</summary>

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "NVIDIA_API_KEY=your_nvidia_api_key_here" > .env

# Initialize database and vector store
python data_script.py

# Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

</details>

### 🌐 Access the Application

- **Frontend (React App):** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** Disabled for security

### 📋 Available Scripts

| Script | Description |
|--------|-------------|
| `./start.sh` | Start both services (Linux/macOS) |
| `start.bat` | Start both services (Windows) |
| `./stop.sh` | Stop all services (Linux/macOS) |
| `stop.bat` | Stop all services (Windows) |
| `./dev-backend.sh` | Backend development mode |
| `./dev-frontend.sh` | Frontend development mode |

## 📊 Database Schema

### **Enhanced E-commerce Model**
```sql
-- Products (no pricing here!)
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category_id INTEGER,
    brand TEXT,
    model TEXT
);

-- Retailers (pricing at retailer level!)
CREATE TABLE retailers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    product_id INTEGER,
    price REAL NOT NULL,      -- 💰 Price here!
    stock INTEGER,
    location TEXT,            -- 📍 Store location
    contact TEXT,             -- 📧 Contact info
    rating REAL              -- ⭐ Store rating
);
```

## 🎯 Usage Examples

### Simple Product Browsing
```
User: "What products are available?"
AI: 🛍️ Available Products:

**Electronics:**
• Laptop
• Smartphone
• Tablet
• Headphones

**Books:**
• Science Fiction Novel
• Cookbook

**Home Goods:**
• Coffee Maker
• Desk Chair
```

### Product Search with Pricing
```
User: "Show me smartphones"
AI: 🛍️ **Smartphone**
📂 Category: Electronics
💰 Price Range: $789.99 - $829.99
🏪 Available at: 5 retailers
🖼️ Image: [smartphone_image]
```

### Retailer Comparison
```
User: "Who sells smartphones?"
AI: 🏬 **Retailers selling Smartphone (5):**

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

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework
- **SQLite** - Lightweight database for structured data
- **ChromaDB** - Vector database for semantic search
- **LangChain** - LLM framework and agent orchestration
- **NVIDIA LLM** - Mixtral-8x22B for natural language generation
- **HuggingFace** - Embeddings (all-MiniLM-L6-v2)

### Frontend
- **React 18** - User interface framework
- **CSS3 + Flexbox** - Responsive styling
- **Fetch API** - Backend communication

## 📡 API Endpoints

### Core Endpoints
- `POST /api/chat` - Main chat interface
- `GET /health` - System health check
- `GET /agents` - Available AI agents info
- `GET /agents/health` - Detailed agent status

### Example API Request
```json
{
  "message": "What smartphones are available?"
}
```

### Example API Response
```json
{
  "response": "🛍️ **Smartphone**\n📂 Category: Electronics\n💰 Price Range: $789.99 - $829.99\n🏪 Available at: 5 retailers\n🖼️ Image: https://example.com/smartphone.jpg",
  "source": "products_agent (via Products Agent)"
}
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
NVIDIA_API_KEY=nvapi-your-key-here
LOG_LEVEL=INFO

# Optional
DATABASE_URL=sqlite:///products.db
VECTOR_DB_PATH=./chroma_db
MAX_TOKENS=1024
TEMPERATURE=0.7
```

## 📊 Sample Data

The system comes pre-loaded with:
- **8 Products** across 3 categories
- **34 Retailer Entries** with competitive pricing
- **20+ Store Locations** across the US
- **Rich Product Descriptions** for vector search

## 🔮 Future Enhancements

### Short Term (1-2 months)
- [ ] User authentication and profiles
- [ ] Real-time stock level updates
- [ ] Geolocation-based retailer filtering
- [ ] Price drop alerts and notifications
- [ ] User wishlist and favorites

### Medium Term (3-6 months)
- [ ] Multi-language support (Hindi, Spanish)
- [ ] Voice interface with speech recognition
- [ ] Mobile app with push notifications
- [ ] Integration with real e-commerce APIs
- [ ] Advanced price prediction using ML

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Add comprehensive logging for new features
- Include unit tests for business logic
- Update documentation for API changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📚 Documentation

For detailed system architecture and technical documentation, see [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md).

## 🙏 Acknowledgments

- **NVIDIA** for providing free LLM API access
- **LangChain** for the excellent RAG framework
- **ChromaDB** for vector database capabilities
- **HuggingFace** for embedding models
- **FastAPI** for the amazing web framework

---

**Built with ❤️ using modern AI technologies**

*Transform your shopping experience with intelligent product discovery and comparison!* 🛍️✨