import React from 'react';
import { Container, Grid, Paper, Title, Text, Group, ThemeIcon, List, Button } from '@mantine/core';
import { IconDashboard } from '../components/layout/icons';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const navigate = useNavigate();

  return (
    <Container size="xl" py="xl">
      <Title order={1} mb="lg">Dashboard</Title>
      
      <Grid gutter="md">
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Paper withBorder p="xl" radius="md" mb="md">
            <Title order={2} mb="md">Welcome to Hive Mind</Title>
            <Text>
              Hive Mind is a platform for orchestrating teams of AI agents to work together on complex tasks.
              This dashboard gives you an overview of your agent teams, workspaces, and system performance.
            </Text>
            
            <Title order={3} mt="xl" mb="md">Getting Started</Title>
            <List spacing="sm">
              <List.Item>Create a new team of agents using the Teams page</List.Item>
              <List.Item>Configure agent roles and capabilities</List.Item>
              <List.Item>Set up a workspace with the necessary tools and environments</List.Item>
              <List.Item>Monitor cost and performance in the Cost Management section</List.Item>
            </List>
            
            <Button 
              mt="xl" 
              color="indigo"
              onClick={() => navigate('/create-team')}
            >
              Create Your First Team
            </Button>
          </Paper>
        </Grid.Col>
        
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Paper withBorder p="xl" radius="md" mb="md">
            <Title order={3} mb="lg">System Status</Title>
            <Group>
              <ThemeIcon color="green" size="lg" radius="xl">
                <IconDashboard size={20} />
              </ThemeIcon>
              <div>
                <Text>All Systems Operational</Text>
                <Text size="xs" c="dimmed">Last updated: 5 minutes ago</Text>
              </div>
            </Group>
          </Paper>
          
          <Paper withBorder p="xl" radius="md">
            <Title order={3} mb="lg">Recent Activity</Title>
            <Text c="dimmed" size="sm">No recent activity to display.</Text>
          </Paper>
        </Grid.Col>
      </Grid>
    </Container>
  );
} 