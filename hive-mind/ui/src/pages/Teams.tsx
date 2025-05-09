import React from 'react';
import { Container, Title, Grid, Paper, Button, Group, Text, ThemeIcon, Card, Avatar } from '@mantine/core';
import { IconUsersGroup } from '../components/layout/icons';
import { useNavigate } from 'react-router-dom';

// Sample team data
const sampleTeams = [
  { 
    id: 'team-1', 
    name: 'Frontend Development', 
    description: 'Specializes in UI/UX implementation',
    members: 4,
    created: '2023-09-15',
    status: 'active'
  },
  { 
    id: 'team-2', 
    name: 'Backend API', 
    description: 'Builds and maintains API services',
    members: 3,
    created: '2023-10-02',
    status: 'active'
  },
  { 
    id: 'team-3', 
    name: 'Data Analysis', 
    description: 'Processes and analyzes large datasets',
    members: 5,
    created: '2023-11-20',
    status: 'inactive'
  }
];

export default function Teams() {
  const navigate = useNavigate();

  return (
    <Container size="xl" py="xl">
      <Group justify="space-between" mb="xl">
        <Title order={1}>Teams</Title>
        <Button 
          leftSection={<IconUsersGroup size={18} />} 
          color="indigo"
          onClick={() => navigate('/create-team')}
        >
          Create New Team
        </Button>
      </Group>
      
      <Grid>
        {sampleTeams.map((team) => (
          <Grid.Col key={team.id} span={{ base: 12, sm: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
              <Card.Section p="md" bg="indigo.9">
                <Group>
                  <Avatar color="blue" radius="xl" size="lg">
                    {team.name.substring(0, 2).toUpperCase()}
                  </Avatar>
                  <div>
                    <Text fw={700} c="white">{team.name}</Text>
                    <Text size="xs" c="gray.3">Created: {team.created}</Text>
                  </div>
                </Group>
              </Card.Section>
              
              <Text mt="md" mb="xs" size="sm">
                {team.description}
              </Text>
              
              <Group mt="md" mb="xs">
                <div>
                  <Text size="xs" tt="uppercase" fw={700} c="dimmed">Members</Text>
                  <Text>{team.members} agents</Text>
                </div>
                <div>
                  <Text size="xs" tt="uppercase" fw={700} c="dimmed">Status</Text>
                  <Group gap="xs">
                    <ThemeIcon color={team.status === 'active' ? 'green' : 'gray'} variant="light" size="xs" radius="xl" />
                    <Text>{team.status === 'active' ? 'Active' : 'Inactive'}</Text>
                  </Group>
                </div>
              </Group>
              
              <Group mt="xl" justify="space-between">
                <Button variant="outline" size="xs">View Details</Button>
                <Button variant="light" size="xs">Manage Team</Button>
              </Group>
            </Card>
          </Grid.Col>
        ))}
      </Grid>
      
      {sampleTeams.length === 0 && (
        <Paper p="xl" withBorder radius="md" ta="center">
          <IconUsersGroup size={48} stroke={1} color="var(--mantine-color-gray-4)" />
          <Title order={3} mt="md">No Teams Yet</Title>
          <Text c="dimmed" size="sm" maw={500} mx="auto" mt="sm">
            Create your first team to start organizing AI agents into specialized groups for different tasks.
          </Text>
          <Button 
            mt="xl" 
            color="indigo"
            onClick={() => navigate('/create-team')}
          >
            Create Your First Team
          </Button>
        </Paper>
      )}
    </Container>
  );
} 