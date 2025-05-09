import { useStore } from '../hooks/useStore';
import { Clock, Focus, ChevronUp, ChevronDown, AlertCircle, Zap } from 'lucide-react';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const GlobalStatusBar = () => {
  const { agents, focusMode, toggleFocusMode, tokenBurnForecasts } = useStore(state => ({
    agents: state.agents,
    focusMode: state.focusMode,
    toggleFocusMode: state.toggleFocusMode,
    tokenBurnForecasts: state.tokenBurnForecasts
  }));
  
  const [expandedStats, setExpandedStats] = useState(false);
  
  // Calculate total token burn rate
  const totalTokenBurn = Object.values(tokenBurnForecasts).reduce(
    (total, forecast) => total + forecast.perHourUsd, 
    0
  );
  
  // Determine system status based on agent statuses
  const busyAgentsCount = agents.filter(agent => agent.status === 'busy').length;
  const errorAgentsCount = agents.filter(agent => agent.status === 'error').length;
  
  let systemStatus = 'Idle';
  let statusColor = 'text-green-500';
  
  if (errorAgentsCount > 0) {
    systemStatus = `System Error (${errorAgentsCount} agent${errorAgentsCount > 1 ? 's' : ''})`;
    statusColor = 'text-red-500';
  } else if (busyAgentsCount > 0) {
    systemStatus = `Active (${busyAgentsCount} agent${busyAgentsCount > 1 ? 's' : ''} working)`;
    statusColor = 'text-yellow-500';
  }
  
  return (
    <div className="bg-gray-100 border-t border-gray-200 relative">
      {/* Expanded Stats Section */}
      <AnimatePresence>
        {expandedStats && (
          <motion.div 
            className="bg-gray-100 border-t border-gray-200 p-2 grid grid-cols-3 gap-4 text-sm"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {/* Agent Status */}
            <div className="p-2">
              <h3 className="font-semibold mb-1">Agent Status</h3>
              <ul className="space-y-1">
                {agents.map(agent => (
                  <li key={agent.id} className="flex items-center justify-between">
                    <span>{agent.name}</span>
                    <span className={
                      agent.status === 'idle' ? 'text-green-500' :
                      agent.status === 'busy' ? 'text-yellow-500' :
                      'text-red-500'
                    }>
                      {agent.status.charAt(0).toUpperCase() + agent.status.slice(1)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
            
            {/* Token Usage */}
            <div className="p-2">
              <h3 className="font-semibold mb-1">Token Usage</h3>
              <ul className="space-y-1">
                {Object.entries(tokenBurnForecasts).map(([agentId, forecast]) => {
                  const agent = agents.find(a => a.id === agentId);
                  return agent ? (
                    <li key={agentId} className="flex items-center justify-between">
                      <span>{agent.name}</span>
                      <span className="flex items-center">
                        ${forecast.perHourUsd.toFixed(2)}/hr
                        {forecast.trend === 'up' && <ChevronUp className="h-3 w-3 text-red-500 ml-1" />}
                        {forecast.trend === 'down' && <ChevronDown className="h-3 w-3 text-green-500 ml-1" />}
                      </span>
                    </li>
                  ) : null;
                })}
              </ul>
            </div>
            
            {/* System Info */}
            <div className="p-2">
              <h3 className="font-semibold mb-1">System Info</h3>
              <p className="text-gray-700">Agent count: {agents.length}</p>
              <p className="text-gray-700">Active agents: {busyAgentsCount}</p>
              <p className="text-gray-700">
                Session started: {new Date().toLocaleTimeString()}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Main Status Bar */}
      <div className="h-10 px-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {/* System Status */}
          <div className="flex items-center">
            <div className={`w-2 h-2 rounded-full ${
              statusColor.replace('text-', 'bg-')
            } mr-2`} />
            <span className={`text-sm ${statusColor}`}>{systemStatus}</span>
          </div>
          
          {/* Current Time */}
          <div className="flex items-center text-gray-600 text-sm">
            <Clock className="h-3 w-3 mr-1" />
            <span>{new Date().toLocaleTimeString()}</span>
          </div>
          
          {/* Token Burn Rate */}
          <div className="flex items-center text-gray-600 text-sm">
            <Zap className="h-3 w-3 mr-1" />
            <span>${totalTokenBurn.toFixed(2)}/hr</span>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          {/* Focus Mode Toggle */}
          <button 
            className={`flex items-center text-sm ${
              focusMode ? 'text-primary font-medium' : 'text-gray-600'
            }`}
            onClick={toggleFocusMode}
          >
            <Focus className="h-3 w-3 mr-1" />
            <span>Focus Mode</span>
          </button>
          
          {/* Stats Expander Toggle */}
          <button 
            className="flex items-center text-gray-600 text-sm"
            onClick={() => setExpandedStats(!expandedStats)}
          >
            <span>Stats</span>
            {expandedStats ? (
              <ChevronDown className="h-3 w-3 ml-1" />
            ) : (
              <ChevronUp className="h-3 w-3 ml-1" />
            )}
          </button>
          
          {/* Alert Count */}
          {errorAgentsCount > 0 && (
            <div className="flex items-center text-red-500 text-sm">
              <AlertCircle className="h-3 w-3 mr-1" />
              <span>{errorAgentsCount} Alert{errorAgentsCount > 1 ? 's' : ''}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GlobalStatusBar; 