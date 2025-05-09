import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useStore } from '../hooks/useStore';
import { Tooltip } from './ui/Tooltip';

const AgentRail = () => {
  const navigate = useNavigate();
  const { agents, activeAgent, setActiveAgent } = useStore(state => ({
    agents: state.agents,
    activeAgent: state.activeAgent,
    setActiveAgent: state.setActiveAgent,
  }));

  return (
    <div className="w-[60px] bg-gray-100 border-r border-gray-200 flex flex-col items-center py-4 overflow-y-auto">
      {agents.map((agent) => (
        <Tooltip 
          key={agent.id} 
          content={`${agent.name} (${agent.role})${agent.currentTask ? ` - Working on: ${agent.currentTask}` : ''}`}
          side="right"
        >
          <motion.div
            className="relative mb-4 cursor-pointer"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => {
              // Navigate to agent detail page
              navigate(`/agent/${agent.id}`);
              // Open chat drawer if not already open
              if (activeAgent !== agent.id) {
                setActiveAgent(agent.id);
              }
            }}
          >
            {/* Agent Avatar */}
            <div className="w-10 h-10 rounded-full bg-gray-300 flex items-center justify-center overflow-hidden">
              {agent.avatarUrl ? (
                <img 
                  src={agent.avatarUrl} 
                  alt={agent.name} 
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="text-lg font-bold text-gray-700">
                  {agent.name.charAt(0)}
                </div>
              )}
            </div>
            
            {/* Status Ring */}
            <motion.div
              className={`absolute -inset-1 rounded-full border-2 pointer-events-none ${
                agent.status === 'idle' ? 'border-green-500' :
                agent.status === 'busy' ? 'border-yellow-500' :
                'border-red-500'
              }`}
              animate={agent.status === 'idle' ? {
                scale: [1, 1.1, 1],
                opacity: [1, 0.8, 1]
              } : {
                scale: 1,
                opacity: 1
              }}
              transition={agent.status === 'idle' ? {
                duration: 2,
                repeat: Infinity,
                repeatType: 'loop'
              } : {}}
            />
            
            {/* Current Agent Indicator */}
            {activeAgent === agent.id && (
              <div className="absolute -right-1 top-1/2 transform -translate-y-1/2 w-1 h-6 bg-primary rounded-full" />
            )}
          </motion.div>
        </Tooltip>
      ))}
    </div>
  );
};

export default AgentRail; 