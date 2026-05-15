import { useState, useEffect, useRef } from 'react';
import { sendChatMessage, getSuggestedQuestions } from '../api/chat';
import './Chat.css';

export default function Chat() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestedQuestions, setSuggestedQuestions] = useState([]);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  // Load suggested questions on mount
  useEffect(() => {
    loadSuggestedQuestions();
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadSuggestedQuestions = async () => {
    try {
      const data = await getSuggestedQuestions();
      setSuggestedQuestions(data.questions.slice(0, 5)); // Show first 5
    } catch (err) {
      console.error('Failed to load suggestions:', err);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (messageText = null) => {
    const text = messageText || inputValue.trim();
    if (!text || isLoading) return;

    // Add user message
    const userMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      // Send to API
      const response = await sendChatMessage(text, true);

      // Add assistant response
      const assistantMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: response.timestamp,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Chat error:', err);
      setError('Failed to get response. Please check if the backend is running and LLM API is configured.');
      
      // Add error message
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please make sure the backend server is running and the LLM API is properly configured.',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSuggestedQuestion = (question) => {
    handleSendMessage(question);
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  };

  const formatMessage = (content) => {
    // Split by lines and process each line
    const lines = content.split('\n');
    
    return lines.map((line, index) => {
      // Empty line - add spacing
      if (line.trim() === '') {
        return <br key={index} />;
      }
      
      // Numbered list item (e.g., "1. Item" or "14. Item")
      if (/^\d+\.\s/.test(line)) {
        return (
          <div key={index} className="chat-list-item">
            {formatInlineStyles(line)}
          </div>
        );
      }
      
      // Checkmark items (✅ or ✓)
      if (line.trim().startsWith('✅') || line.trim().startsWith('✓')) {
        return (
          <div key={index} className="chat-checkmark-item">
            {formatInlineStyles(line)}
          </div>
        );
      }
      
      // Headers or emphasized lines (starting with ###, ##, or #)
      if (line.trim().startsWith('#')) {
        const level = line.match(/^#+/)[0].length;
        const text = line.replace(/^#+\s*/, '');
        return (
          <div key={index} className={`chat-header-${level}`}>
            {formatInlineStyles(text)}
          </div>
        );
      }
      
      // Horizontal rule
      if (line.trim() === '---' || line.trim() === '***') {
        return <hr key={index} className="chat-divider" />;
      }
      
      // Regular line
      return (
        <div key={index} className="chat-line">
          {formatInlineStyles(line)}
        </div>
      );
    });
  };

  const formatInlineStyles = (text) => {
    // Convert **bold** to <strong>
    const parts = [];
    let currentIndex = 0;
    const boldRegex = /\*\*(.+?)\*\*/g;
    let match;
    
    while ((match = boldRegex.exec(text)) !== null) {
      // Add text before bold
      if (match.index > currentIndex) {
        parts.push(text.substring(currentIndex, match.index));
      }
      // Add bold text
      parts.push(<strong key={match.index}>{match[1]}</strong>);
      currentIndex = match.index + match[0].length;
    }
    
    // Add remaining text
    if (currentIndex < text.length) {
      parts.push(text.substring(currentIndex));
    }
    
    return parts.length > 0 ? parts : text;
  };

  return (
    <div className="chat-widget">
      {/* Chat Button */}
      {!isOpen && (
        <button 
          className="chat-button"
          onClick={() => setIsOpen(true)}
          aria-label="Open chat"
        >
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" 
            />
          </svg>
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="chat-window">
          {/* Header */}
          <div className="chat-header">
            <div className="chat-header-info">
              <div className="chat-avatar">🤖</div>
              <div className="chat-header-text">
                <h3>8NAP AI</h3>
                <p>Supply Chain Assistant</p>
              </div>
            </div>
            <button 
              className="chat-close-btn"
              onClick={() => setIsOpen(false)}
              aria-label="Close chat"
            >
              <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div className="chat-messages">
            {messages.length === 0 ? (
              <div className="chat-welcome">
                <div className="chat-welcome-icon">👋</div>
                <h4>Hi! I'm 8NAP AI</h4>
                <p>Your AI assistant for supply chain operations. Ask me anything about shipments, orders, inventory, or exceptions.</p>
                
                {suggestedQuestions.length > 0 && (
                  <div className="suggested-questions">
                    {suggestedQuestions.map((question, index) => (
                      <button
                        key={index}
                        className="suggested-question-btn"
                        onClick={() => handleSuggestedQuestion(question)}
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <>
                {messages.map((message, index) => (
                  <div key={index} className={`chat-message ${message.role}`}>
                    <div className="chat-message-avatar">
                      {message.role === 'assistant' ? '🤖' : '👤'}
                    </div>
                    <div>
                      <div className="chat-message-content">
                        {message.role === 'assistant' 
                          ? formatMessage(message.content)
                          : message.content
                        }
                      </div>
                      <div className="chat-message-time">
                        {formatTime(message.timestamp)}
                      </div>
                    </div>
                  </div>
                ))}
                
                {isLoading && (
                  <div className="chat-message assistant">
                    <div className="chat-message-avatar">🤖</div>
                    <div className="typing-indicator">
                      <div className="typing-dots">
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Show suggested questions after conversation starts */}
                {!isLoading && messages.length > 0 && suggestedQuestions.length > 0 && (
                  <div className="suggested-questions-inline">
                    <p className="suggestions-label">You can also ask:</p>
                    <div className="suggested-questions">
                      {suggestedQuestions.slice(0, 3).map((question, index) => (
                        <button
                          key={index}
                          className="suggested-question-btn"
                          onClick={() => handleSuggestedQuestion(question)}
                        >
                          {question}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Error Message */}
          {error && (
            <div className="chat-error">
              {error}
            </div>
          )}

          {/* Input */}
          <div className="chat-input-container">
            <div className="chat-input-wrapper">
              <textarea
                className="chat-input"
                placeholder="Ask me about your operations..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                rows={1}
                disabled={isLoading}
              />
              <button
                className="chat-send-btn"
                onClick={() => handleSendMessage()}
                disabled={!inputValue.trim() || isLoading}
                aria-label="Send message"
              >
                <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" 
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
