import React, { useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Box, Divider, Stack, Text, Button, ActionIcon } from '@mantine/core';
import { 
  IconDashboard, 
  IconUsersGroup, 
  IconWorkspace, 
  IconMoneybag, 
  IconSettings,
  IconChartLine,
  IconChevronLeft,
  IconChevronRight,
  IconFolders,
  IconClipboardList,
  IconBrain,
  IconTag
} from './icons';

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  minimized?: boolean;
}

const NavItem = ({ to, icon, label, minimized }: NavItemProps) => (
  <NavLink
    to={to}
    className={({ isActive }) => `
      nav-item
      ${isActive ? 'nav-item-active' : ''}
    `}
    style={({ isActive }) => ({
      display: 'flex',
      alignItems: 'center',
      padding: minimized ? '0.75rem 0.5rem' : '0.75rem 1rem',
      borderRadius: '0.5rem',
      color: isActive ? '#F8FAFC' : '#9AA5B4',
      backgroundColor: isActive ? '#1A3FE4' : 'transparent',
      textDecoration: 'none',
      transition: 'all 0.2s ease',
      marginBottom: '0.25rem',
      fontWeight: isActive ? 500 : 400,
      justifyContent: minimized ? 'center' : 'flex-start',
    })}
    title={minimized ? label : undefined}
  >
    <Box mr={minimized ? 0 : "xs"} style={{ display: 'flex', alignItems: 'center' }}>
      {icon}
    </Box>
    {!minimized && <Text size="sm">{label}</Text>}
  </NavLink>
);

interface SectionTitleProps {
  title: string;
  minimized?: boolean;
}

const SectionTitle = ({ title, minimized }: SectionTitleProps) => (
  minimized ? null : (
    <Text size="xs" c="dimmed" fw={600} mb="xs" tt="uppercase" pl="md">
      {title}
    </Text>
  )
);

interface AppSidebarProps {
  onMinimizeChange?: (minimized: boolean) => void;
}

export default function AppSidebar({ onMinimizeChange }: AppSidebarProps) {
  const [minimized, setMinimized] = React.useState(false);
  const navigate = useNavigate();

  // Notify parent when minimized state changes
  useEffect(() => {
    if (onMinimizeChange) {
      onMinimizeChange(minimized);
    }
  }, [minimized, onMinimizeChange]);

  const handleToggleMinimize = () => {
    setMinimized(prev => !prev);
  };

  // Use existing icons for navigation items
  const navigationItems = [
    { label: 'Dashboard', icon: <IconDashboard size={20} />, link: '/' },
    { label: 'Workspaces', icon: <IconFolders size={20} />, link: '/workspaces' },
    { label: 'Teams', icon: <IconUsersGroup size={20} />, link: '/teams' },
    { label: 'Analytics', icon: <IconChartLine size={20} />, link: '/analytics' },
    { label: 'Cost Management', icon: <IconMoneybag size={20} />, link: '/cost-management' },
    { label: 'Settings', icon: <IconSettings size={20} />, link: '/settings' },
  ];

  return (
    <Box 
      style={{ 
        height: '100%', 
        padding: minimized ? '1rem 0.25rem' : '1rem', 
        backgroundColor: '#202939', 
        borderRight: '1px solid #364152',
        overflow: 'auto',
        width: minimized ? '60px' : '100%',
        transition: 'width 0.3s ease, padding 0.3s ease',
        position: 'relative',
      }}
    >
      <ActionIcon 
        variant="filled" 
        size="lg"
        color="blue"
        style={{
          position: 'absolute',
          right: minimized ? '50%' : '0.5rem',
          top: '0.5rem',
          zIndex: 100,
          transform: minimized ? 'translateX(50%)' : 'none',
          borderRadius: '50%',
          backgroundColor: '#1A3FE4',
          boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
          transition: 'all 0.3s ease',
        }}
        onClick={handleToggleMinimize}
        title={minimized ? "Expand sidebar" : "Collapse sidebar"}
      >
        {minimized ? <IconChevronRight size={16} /> : <IconChevronLeft size={16} />}
      </ActionIcon>
      
      <Stack mt={minimized ? "2.5rem" : "1.5rem"}>
        <SectionTitle title="Main" minimized={minimized} />
        {navigationItems.map((item, index) => (
          <NavItem key={index} to={item.link} icon={item.icon} label={item.label} minimized={minimized} />
        ))}

        <Divider my="md" color="#364152" />

        <SectionTitle title="Analytics" minimized={minimized} />
        <NavItem to="/analytics" icon={<IconChartLine size={20} />} label="Analytics" minimized={minimized} />
        <NavItem to="/cost-management" icon={<IconMoneybag size={20} />} label="Cost Management" minimized={minimized} />

        <Divider my="md" color="#364152" />

        <SectionTitle title="Other" minimized={minimized} />
        <NavItem to="/settings" icon={<IconSettings size={20} />} label="Settings" minimized={minimized} />
      </Stack>
    </Box>
  );
} 