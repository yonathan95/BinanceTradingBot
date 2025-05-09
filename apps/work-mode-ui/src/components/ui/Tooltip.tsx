import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactElement;
  side?: 'top' | 'right' | 'bottom' | 'left';
  delayMs?: number;
}

export const Tooltip = ({
  content,
  children,
  side = 'top',
  delayMs = 300,
}: TooltipProps) => {
  const [isVisible, setIsVisible] = useState(false);
  const [hoverTimeout, setHoverTimeout] = useState<number | null>(null);

  const handleMouseEnter = () => {
    const timeout = window.setTimeout(() => {
      setIsVisible(true);
    }, delayMs);
    setHoverTimeout(timeout);
  };

  const handleMouseLeave = () => {
    if (hoverTimeout) {
      window.clearTimeout(hoverTimeout);
      setHoverTimeout(null);
    }
    setIsVisible(false);
  };

  // Position the tooltip based on the side prop
  const getPosition = () => {
    switch (side) {
      case 'top':
        return { top: '-8px', left: '50%', transform: 'translate(-50%, -100%)' };
      case 'right':
        return { top: '50%', left: 'calc(100% + 8px)', transform: 'translateY(-50%)' };
      case 'bottom':
        return { bottom: '-8px', left: '50%', transform: 'translate(-50%, 100%)' };
      case 'left':
        return { top: '50%', right: 'calc(100% + 8px)', transform: 'translateY(-50%)' };
      default:
        return { top: '-8px', left: '50%', transform: 'translate(-50%, -100%)' };
    }
  };

  // Animation variants based on the side
  const variants = {
    hidden: {
      opacity: 0,
      y: side === 'top' ? 5 : side === 'bottom' ? -5 : 0,
      x: side === 'left' ? 5 : side === 'right' ? -5 : 0,
    },
    visible: {
      opacity: 1,
      y: 0,
      x: 0,
    },
  };

  return (
    <div
      className="relative inline-block"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}
      <AnimatePresence>
        {isVisible && (
          <motion.div
            className="absolute z-50 px-2 py-1 text-xs font-medium text-white bg-gray-900 rounded-md shadow-sm whitespace-nowrap"
            style={getPosition()}
            initial="hidden"
            animate="visible"
            exit="hidden"
            variants={variants}
            transition={{ duration: 0.15 }}
          >
            {content}
            {/* Arrow */}
            <div
              className={`absolute w-2 h-2 bg-gray-900 ${
                side === 'top' ? 'bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 rotate-45' :
                side === 'right' ? 'left-0 top-1/2 -translate-y-1/2 -translate-x-1/2 rotate-45' :
                side === 'bottom' ? 'top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 rotate-45' :
                'right-0 top-1/2 -translate-y-1/2 translate-x-1/2 rotate-45'
              }`}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}; 