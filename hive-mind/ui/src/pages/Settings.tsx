import React from 'react';
import { Container, Title, Paper, Tabs, TextInput, Switch, Button, Group, Select, Text, NumberInput, Divider } from '@mantine/core';
import { IconSettings } from '../components/layout/icons';

export default function Settings() {
  return (
    <Container size="xl" py="xl">
      <Group mb="xl">
        <IconSettings size={32} />
        <Title order={1}>Settings</Title>
      </Group>
      
      <Tabs defaultValue="general">
        <Tabs.List mb="md">
          <Tabs.Tab value="general">General</Tabs.Tab>
          <Tabs.Tab value="appearance">Appearance</Tabs.Tab>
          <Tabs.Tab value="api">API Integration</Tabs.Tab>
          <Tabs.Tab value="advanced">Advanced</Tabs.Tab>
        </Tabs.List>
        
        <Tabs.Panel value="general">
          <Paper withBorder p="xl" radius="md">
            <Title order={3} mb="lg">General Settings</Title>
            
            <TextInput
              label="Organization Name"
              placeholder="Your organization name"
              defaultValue="Hive Mind Organization"
              mb="md"
            />
            
            <TextInput
              label="Administrator Email"
              placeholder="admin@example.com"
              defaultValue="admin@hivemind.ai"
              mb="md"
            />
            
            <Select
              label="Default Timezone"
              placeholder="Select timezone"
              defaultValue="utc"
              data={[
                { value: 'utc', label: 'UTC (Coordinated Universal Time)' },
                { value: 'est', label: 'EST (Eastern Standard Time)' },
                { value: 'pst', label: 'PST (Pacific Standard Time)' },
                { value: 'gmt', label: 'GMT (Greenwich Mean Time)' }
              ]}
              mb="md"
            />
            
            <Group mt="xl">
              <Button color="indigo">Save Changes</Button>
              <Button variant="subtle">Cancel</Button>
            </Group>
          </Paper>
        </Tabs.Panel>
        
        <Tabs.Panel value="appearance">
          <Paper withBorder p="xl" radius="md">
            <Title order={3} mb="lg">Appearance Settings</Title>
            
            <Group mb="md">
              <Switch
                label="Dark Mode"
                defaultChecked
              />
            </Group>
            
            <Select
              label="Theme Accent Color"
              placeholder="Select accent color"
              defaultValue="indigo"
              data={[
                { value: 'indigo', label: 'Indigo' },
                { value: 'blue', label: 'Blue' },
                { value: 'teal', label: 'Teal' },
                { value: 'purple', label: 'Purple' }
              ]}
              mb="md"
            />
            
            <NumberInput
              label="Interface Density"
              description="Adjust the spacing between UI elements"
              defaultValue={1}
              min={0.8}
              max={1.5}
              step={0.1}
              mb="md"
            />
            
            <Group mt="xl">
              <Button color="indigo">Save Changes</Button>
              <Button variant="subtle">Reset to Defaults</Button>
            </Group>
          </Paper>
        </Tabs.Panel>
        
        <Tabs.Panel value="api">
          <Paper withBorder p="xl" radius="md">
            <Title order={3} mb="lg">API Integration</Title>
            
            <TextInput
              label="API Key"
              placeholder="Your API key"
              defaultValue="sk-••••••••••••••••••••••••••••••••••••"
              mb="md"
            />
            
            <Select
              label="API Version"
              placeholder="Select API version"
              defaultValue="v1"
              data={[
                { value: 'v1', label: 'v1 (Stable)' },
                { value: 'v2', label: 'v2 (Beta)' }
              ]}
              mb="md"
            />
            
            <Group mb="md">
              <Switch
                label="Enable API Access"
                defaultChecked
              />
            </Group>
            
            <Divider my="lg" />
            
            <Title order={4} mb="md">Rate Limits</Title>
            <NumberInput
              label="Requests per minute"
              defaultValue={60}
              min={1}
              max={500}
              mb="md"
            />
            
            <Group mt="xl">
              <Button color="indigo">Save API Settings</Button>
              <Button variant="outline" color="indigo">Regenerate API Key</Button>
            </Group>
          </Paper>
        </Tabs.Panel>
        
        <Tabs.Panel value="advanced">
          <Paper withBorder p="xl" radius="md">
            <Title order={3} mb="lg">Advanced Settings</Title>
            
            <Title order={4} mb="md">Performance</Title>
            <Group mb="md">
              <Switch
                label="Enable Performance Mode"
                description="Optimizes the application for better performance on slower devices"
              />
            </Group>
            
            <Title order={4} mt="lg" mb="md">Data Management</Title>
            <Group mb="md">
              <Switch
                label="Enable Automatic Backups"
                defaultChecked
                description="Creates daily backups of workspace data"
              />
            </Group>
            
            <Divider my="lg" />
            
            <Title order={4} mb="md" c="red">Danger Zone</Title>
            <Text size="sm" c="dimmed" mb="md">
              The following actions are irreversible. Please proceed with caution.
            </Text>
            
            <Group>
              <Button variant="outline" color="red">Clear All Data</Button>
              <Button variant="filled" color="red">Reset Application</Button>
            </Group>
          </Paper>
        </Tabs.Panel>
      </Tabs>
    </Container>
  );
} 