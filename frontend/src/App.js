import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  // Sample suggestions for better UX
  const suggestions = [
    "What products are available?",
    "Show me laptops",
    "Show me smartphones", 
    "What categories do you have?",
    "Show me electronics",
    "Show me books"
  ];

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Add welcome message on initial load
  useEffect(() => {
    const welcomeMessage = {
      text: "Hello! 👋 I'm your shopping assistant. I can help you find products, check prices, and explore our catalog. Try asking me about laptops, smartphones, or any other products!",
      sender: 'bot',
      timestamp: new Date(),
      source: 'welcome'
    };
    setMessages([welcomeMessage]);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { 
      text: input, 
      sender: 'user', 
      timestamp: new Date() 
    };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setIsLoading(true);
    setIsTyping(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Simulate typing delay for better UX
      setTimeout(() => {
        const botMessage = { 
          text: data.response, 
          sender: 'bot',
          timestamp: new Date(),
          source: data.source
        };
        setMessages((prevMessages) => [...prevMessages, botMessage]);
        setIsTyping(false);
      }, 1000);
      
    } catch (error) {
      console.error('Error:', error);
      setTimeout(() => {
        const errorMessage = { 
          text: 'Sorry, I encountered an error. Please try again or ask about our products directly.', 
          sender: 'bot',
          timestamp: new Date(),
          source: 'error'
        };
        setMessages((prevMessages) => [...prevMessages, errorMessage]);
        setIsTyping(false);
      }, 1000);
    } finally {
      setIsLoading(false);
    }

    setInput('');
  };

  const handleSuggestionClick = (suggestion) => {
    setInput(suggestion);
  };

  const formatTimestamp = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderMessageContent = (text) => {
    // Check if the message contains image URLs
    const imageUrlRegex = /(https?:\/\/[^\s]+\.(jpg|jpeg|png|gif|webp|bmp|svg))|🖼️ Image: (https?:\/\/[^\s]+)/gi;
    
    if (imageUrlRegex.test(text)) {
      // Split text and render with images
      const parts = text.split(/\n/);
      
      return (
        <div className="formatted-message">
          {parts.map((part, index) => {
            // Check if this line contains an image URL
            const imageMatch = part.match(/🖼️ Image: (https?:\/\/[^\s]+)/);
            
            if (imageMatch) {
              const imageUrl = imageMatch[1];
              return (
                <div key={index} className="image-container">
                  <img 
                    src={imageUrl} 
                    alt="Product" 
                    className="product-image"
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                    loading="lazy"
                  />
                </div>
              );
            }
            
            // Check for product name (bold text)
            if (part.includes('**') && part.includes('🛍️')) {
              const boldText = part.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
              return <div key={index} className="product-title" dangerouslySetInnerHTML={{ __html: boldText }} />;
            }
            
            // Check for other formatting
            if (part.includes('📂') || part.includes('💰')) {
              return <div key={index} className="product-detail">{part}</div>;
            }
            
            // Check for header
            if (part.includes('🔍') && part.includes('**')) {
              const boldText = part.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
              return <div key={index} className="results-header" dangerouslySetInnerHTML={{ __html: boldText }} />;
            }
            
            // Check for footer
            if (part.includes('💡') && part.includes('*')) {
              const italicText = part.replace(/\*(.*?)\*/g, '<em>$1</em>');
              return <div key={index} className="results-footer" dangerouslySetInnerHTML={{ __html: italicText }} />;
            }
            
            // Regular text
            return part.trim() ? <div key={index}>{part}</div> : <br key={index} />;
          })}
        </div>
      );
    }
    
    // Regular text without images
    return text;
  };

  const getSourceBadge = (source) => {
    const badges = {
      'sql': { label: 'Database', color: '#2196F3' },
      'sql_direct': { label: 'Database', color: '#2196F3' },
      'vector': { label: 'AI Search', color: '#FF9800' },
      'vector_direct': { label: 'AI Search', color: '#FF9800' },
      'simple': { label: 'Quick Reply', color: '#4CAF50' },
      'fallback': { label: 'Help', color: '#9E9E9E' },
      'rate_limit': { label: 'Rate Limited', color: '#F44336' },
      'error': { label: 'Error', color: '#F44336' },
      'welcome': { label: 'Welcome', color: '#9C27B0' }
    };
    
    const badge = badges[source] || { label: 'Unknown', color: '#9E9E9E' };
    
    return (
      <span 
        className="source-badge"
        style={{ backgroundColor: badge.color }}
      >
        {badge.label}
      </span>
    );
  };

  return (
    <div className="App">
      <header className="chat-header">
        <div className="header-content">
          <h1>🛍️ Shopping Assistant</h1>
          <p>AI-powered product search and recommendations</p>
        </div>
      </header>

      <div className="chat-container">
        <div className="chat-window">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.sender}`}>
              <div className="message-content">
                <div className="message-text">
                  {renderMessageContent(msg.text)}
                </div>
                <div className="message-meta">
                  <span className="timestamp">
                    {formatTimestamp(msg.timestamp)}
                  </span>
                  {msg.source && getSourceBadge(msg.source)}
                </div>
              </div>
            </div>
          ))}
          
          {isTyping && (
            <div className="message bot typing">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Suggestions */}
        {messages.length <= 1 && (
          <div className="suggestions">
            <p>Try asking about:</p>
            <div className="suggestion-chips">
              {suggestions.map((suggestion, index) => (
                <button 
                  key={index}
                  className="suggestion-chip"
                  onClick={() => handleSuggestionClick(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="chat-input">
        <div className="input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about products, prices, categories..."
            disabled={isLoading}
            maxLength={500}
          />
          <button 
            type="submit" 
            disabled={isLoading || !input.trim()}
            className={isLoading ? 'loading' : ''}
          >
            {isLoading ? '⏳' : '📤'}
          </button>
        </div>
        <div className="input-footer">
          <span className="char-count">{input.length}/500</span>
        </div>
      </form>
    </div>
  );
}

export default App;