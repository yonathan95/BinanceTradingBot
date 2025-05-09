import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { X, Send } from 'lucide-react';
import { useStore } from '../hooks/useStore';

interface AgentChatDrawerProps {
  agentId: string;
  onClose: () => void;
}

interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'agent';
  timestamp: Date;
}

const AgentChatDrawer = ({ agentId, onClose }: AgentChatDrawerProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const agent = useStore(state => 
    state.agents.find(a => a.id === agentId)
  );

  // Mock function to load chat history - would be replaced by actual API call
  useEffect(() => {
    // Simulate loading chat history from an API
    const mockMessages = [
      {
        id: '1',
        text: 'Hello! I am ready to help with your project.',
        sender: 'agent' as const,
        timestamp: new Date(Date.now() - 3600000), // 1 hour ago
      },
      {
        id: '2',
        text: 'Can you implement the login flow for the application?',
        sender: 'user' as const,
        timestamp: new Date(Date.now() - 3500000),
      },
      {
        id: '3',
        text: 'Sure, I can work on that. I\'ll create the authentication components and set up the routes.',
        sender: 'agent' as const,
        timestamp: new Date(Date.now() - 3400000),
      },
    ];
    
    setMessages(mockMessages);
  }, [agentId]);

  // Scroll to bottom when new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = () => {
    if (inputValue.trim() === '') return;
    
    // Add user message
    const newMessage: ChatMessage = {
      id: String(Date.now()),
      text: inputValue,
      sender: 'user',
      timestamp: new Date(),
    };
    
    setMessages([...messages, newMessage]);
    setInputValue('');
    
    // Simulate agent response
    setTimeout(() => {
      const agentResponse: ChatMessage = {
        id: String(Date.now() + 1),
        text: `I'm processing your request: "${inputValue}"`,
        sender: 'agent',
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, agentResponse]);
    }, 1000);
  };

  if (!agent) return null;

  return (
    <motion.div 
      className="w-[340px] h-full bg-white border-l border-gray-200 flex flex-col"
      initial={{ x: 340 }}
      animate={{ x: 0 }}
      exit={{ x: 340 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            agent.status === 'idle' ? 'bg-green-500' :
            agent.status === 'busy' ? 'bg-yellow-500' :
            'bg-red-500'
          }`} />
          <h3 className="font-semibold">{agent.name}</h3>
          <span className="text-xs text-gray-500">({agent.role})</span>
        </div>
        <button 
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700"
        >
          <X size={16} />
        </button>
      </div>
      
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div 
            key={message.id} 
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div 
              className={`max-w-[85%] p-3 rounded-lg ${
                message.sender === 'user' 
                  ? 'bg-primary text-primary-foreground' 
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="text-sm">{message.text}</p>
              <span className="text-xs opacity-70 mt-1 block">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input Area */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') handleSendMessage();
            }}
            placeholder="Send a message..."
            className="flex-1 p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          <button
            onClick={handleSendMessage}
            className="p-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </motion.div>
  );
};

export default AgentChatDrawer; 