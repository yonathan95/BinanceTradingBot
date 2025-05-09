import { Outlet } from 'react-router-dom';
import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useStore } from '../hooks/useStore';
import AgentRail from './AgentRail';
import AgentChatDrawer from './AgentChatDrawer';
import GlobalStatusBar from './GlobalStatusBar';

const Layout = () => {
  const { focusMode, activeAgent } = useStore(state => ({
    focusMode: state.focusMode,
    activeAgent: state.activeAgent
  }));

  // Focus mode auto-exit after 5 min of inactivity
  useEffect(() => {
    if (!focusMode) return;
    
    let inactivityTimer: number;
    const resetTimer = () => {
      if (inactivityTimer) window.clearTimeout(inactivityTimer);
      inactivityTimer = window.setTimeout(() => {
        useStore.getState().toggleFocusMode();
      }, 5 * 60 * 1000); // 5 minutes
    };
    
    // Reset timer on any user activity
    const handleActivity = () => resetTimer();
    
    window.addEventListener('mousemove', handleActivity);
    window.addEventListener('keypress', handleActivity);
    
    // Start the initial timer
    resetTimer();
    
    return () => {
      if (inactivityTimer) window.clearTimeout(inactivityTimer);
      window.removeEventListener('mousemove', handleActivity);
      window.removeEventListener('keypress', handleActivity);
    };
  }, [focusMode]);

  return (
    <div className="h-screen flex flex-col">
      <div className="flex flex-1 overflow-hidden">
        {/* Left Rail - 60px fixed width */}
        <AgentRail />
        
        {/* Main Canvas */}
        <motion.main 
          className="flex-1 overflow-auto bg-background relative"
          animate={focusMode ? { 
            scale: 1.03,
            opacity: 1
          } : { 
            scale: 1,
            opacity: 1
          }}
          transition={{ duration: 0.3 }}
        >
          <Outlet />
        </motion.main>
        
        {/* Right Drawer - 340px when open */}
        <AnimatePresence>
          {activeAgent && (
            <AgentChatDrawer 
              agentId={activeAgent} 
              onClose={() => useStore.getState().setActiveAgent(null)}
            />
          )}
        </AnimatePresence>
      </div>
      
      {/* Global Status Bar - 40px height */}
      <GlobalStatusBar />
      
      {/* Focus Mode Overlay */}
      {focusMode && (
        <motion.div
          className="fixed inset-0 bg-black pointer-events-none"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.25 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          style={{ zIndex: 10 }}
        />
      )}
    </div>
  );
};

export default Layout; 