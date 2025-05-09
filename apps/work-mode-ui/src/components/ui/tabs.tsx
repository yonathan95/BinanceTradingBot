import React from 'react';
import { motion } from 'framer-motion';

interface TabsProps {
  defaultValue: string;
  children: React.ReactNode;
}

interface TabsListProps {
  children: React.ReactNode;
  className?: string;
}

interface TabsTriggerProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

interface TabsContentProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

const TabsContext = React.createContext<{
  value: string;
  onChange: (value: string) => void;
}>({
  value: '',
  onChange: () => {},
});

export const Tabs: React.FC<TabsProps> = ({ defaultValue, children }) => {
  const [value, setValue] = React.useState(defaultValue);

  return (
    <TabsContext.Provider value={{ value, onChange: setValue }}>
      {children}
    </TabsContext.Provider>
  );
};

export const TabsList: React.FC<TabsListProps> = ({ children, className = '' }) => {
  return (
    <div className={`flex space-x-2 border-b border-gray-200 ${className}`}>
      {children}
    </div>
  );
};

export const TabsTrigger: React.FC<TabsTriggerProps> = ({ value, children, className = '' }) => {
  const { value: activeValue, onChange } = React.useContext(TabsContext);
  const isActive = activeValue === value;

  return (
    <button
      className={`px-4 py-2 text-sm font-medium relative ${
        isActive 
          ? 'text-primary' 
          : 'text-gray-500 hover:text-gray-900'
      } ${className}`}
      onClick={() => onChange(value)}
    >
      {children}
      {isActive && (
        <motion.div 
          className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary"
          layoutId="activeTab"
        />
      )}
    </button>
  );
};

export const TabsContent: React.FC<TabsContentProps> = ({ value, children, className = '' }) => {
  const { value: activeValue } = React.useContext(TabsContext);
  const isActive = activeValue === value;

  if (!isActive) return null;

  return (
    <motion.div 
      className={className}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      transition={{ duration: 0.2 }}
    >
      {children}
    </motion.div>
  );
}; 