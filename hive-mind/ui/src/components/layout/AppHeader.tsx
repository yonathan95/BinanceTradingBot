import { Avatar, Box, Button, Group, Menu, Text, UnstyledButton } from '@mantine/core';
import { IconBell, IconChevronDown, IconLogout, IconSettings, IconUser } from './icons';

export default function AppHeader() {
  return (
    <Box 
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '100%',
        padding: '0 1rem',
        backgroundColor: '#202939',
        borderBottom: '1px solid #364152'
      }}
    >
      <Group>
        <Box 
          style={{ 
            fontWeight: 700, 
            fontSize: '1.5rem', 
            color: '#F8FAFC',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <div
            style={{
              width: 28,
              height: 28,
              backgroundColor: '#1A3FE4',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: 'bold',
              fontSize: '0.9rem',
              borderRadius: '4px'
            }}
          >
            HM
          </div>
          Hive Mind
        </Box>
      </Group>

      <Group>
        <Button 
          variant="subtle" 
          leftSection={<IconBell size={18} />}
          style={{ 
            color: '#9AA5B4',
            borderRadius: '50%',
            width: '40px',
            height: '40px',
            padding: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <span className="sr-only">Notifications</span>
        </Button>

        <Menu
          shadow="md"
          width={200}
          position="bottom-end"
        >
          <Menu.Target>
            <UnstyledButton
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                borderRadius: '0.25rem',
                padding: '0.5rem',
                transition: 'background-color 0.2s ease',
                '&:hover': {
                  backgroundColor: '#364152'
                }
              }}
            >
              <Avatar
                src={null}
                alt="User"
                color="indigo"
                radius="xl"
                size="sm"
              >
                DA
              </Avatar>
              <Text size="sm" fw={500}>
                Demo Admin
              </Text>
              <IconChevronDown size={16} />
            </UnstyledButton>
          </Menu.Target>

          <Menu.Dropdown>
            <Menu.Item leftSection={<IconUser size={16} />}>Profile</Menu.Item>
            <Menu.Item leftSection={<IconSettings size={16} />}>Settings</Menu.Item>
            <Menu.Divider />
            <Menu.Item leftSection={<IconLogout size={16} />} color="red">Logout</Menu.Item>
          </Menu.Dropdown>
        </Menu>
      </Group>
    </Box>
  );
} 