import React from 'react';
import { useParams } from 'react-router-dom';
import { Container, Title, Paper, Tabs, Grid, Card, Text, Group, Button, Divider, Code, Badge } from '@mantine/core';
import { IconWorkspace } from '../components/layout/icons';

export default function Workspace() {
  const { teamId } = useParams<{ teamId?: string }>();
  
  // Sample data for the workspace
  const workspaceData = {
    teamName: teamId ? `Team ${teamId}` : 'Default Workspace',
    status: 'active',
    files: [
      { id: 'file-1', name: 'index.html', type: 'html', size: '4.2 KB', updated: '2 hours ago' },
      { id: 'file-2', name: 'styles.css', type: 'css', size: '1.8 KB', updated: '3 hours ago' },
      { id: 'file-3', name: 'app.js', type: 'javascript', size: '6.5 KB', updated: '1 day ago' }
    ],
    conversations: [
      { id: 'conv-1', title: 'Initial planning', participants: 3, messages: 24, updated: '2 days ago' },
      { id: 'conv-2', title: 'Implementation discussion', participants: 4, messages: 56, updated: '1 day ago' },
      { id: 'conv-3', title: 'Code review feedback', participants: 2, messages: 18, updated: '5 hours ago' }
    ]
  };

  return (
    <Container size="xl" py="xl">
      <Group mb="xl">
        <IconWorkspace size={32} />
        <Title order={1}>{workspaceData.teamName} Workspace</Title>
        <Badge color={workspaceData.status === 'active' ? 'green' : 'gray'} size="lg" ml="auto">
          {workspaceData.status === 'active' ? 'Active' : 'Inactive'}
        </Badge>
      </Group>
      
      <Tabs defaultValue="files">
        <Tabs.List mb="md">
          <Tabs.Tab value="files">Files</Tabs.Tab>
          <Tabs.Tab value="conversations">Conversations</Tabs.Tab>
          <Tabs.Tab value="agents">Agents</Tabs.Tab>
          <Tabs.Tab value="tasks">Tasks</Tabs.Tab>
        </Tabs.List>
        
        <Tabs.Panel value="files">
          <Paper withBorder p="md" radius="md" mb="md">
            <Group mb="md">
              <Title order={3}>Project Files</Title>
              <Button size="sm" ml="auto">Upload File</Button>
              <Button size="sm" variant="outline">Create File</Button>
            </Group>
            <Divider mb="md" />
            
            <Grid>
              {workspaceData.files.map(file => (
                <Grid.Col key={file.id} span={{ base: 12, sm: 6, md: 4 }}>
                  <Card withBorder radius="md" p="md">
                    <Group>
                      <div style={{ flex: 1 }}>
                        <Text fw={600}>{file.name}</Text>
                        <Text size="sm" c="dimmed">{file.size} · {file.updated}</Text>
                      </div>
                      <Code>{file.type}</Code>
                    </Group>
                    <Group mt="md">
                      <Button variant="light" size="xs">View</Button>
                      <Button variant="outline" size="xs">Edit</Button>
                      <Button variant="subtle" color="red" size="xs">Delete</Button>
                    </Group>
                  </Card>
                </Grid.Col>
              ))}
            </Grid>
          </Paper>
        </Tabs.Panel>
        
        <Tabs.Panel value="conversations">
          <Paper withBorder p="md" radius="md">
            <Group mb="md">
              <Title order={3}>Conversations</Title>
              <Button size="sm" ml="auto">New Conversation</Button>
            </Group>
            <Divider mb="md" />
            
            <Grid>
              {workspaceData.conversations.map(conv => (
                <Grid.Col key={conv.id} span={{ base: 12, sm: 6 }}>
                  <Card withBorder radius="md" p="md">
                    <Text fw={600}>{conv.title}</Text>
                    <Group mt="xs">
                      <Text size="sm">{conv.participants} participants</Text>
                      <Badge size="sm">{conv.messages} messages</Badge>
                    </Group>
                    <Text size="sm" c="dimmed" mt="xs">Last updated: {conv.updated}</Text>
                    <Button variant="light" fullWidth mt="md">View Conversation</Button>
                  </Card>
                </Grid.Col>
              ))}
            </Grid>
          </Paper>
        </Tabs.Panel>
        
        <Tabs.Panel value="agents">
          <Paper withBorder p="md" radius="md">
            <Title order={3}>Team Agents</Title>
            <Text>Agent configuration and status would be displayed here.</Text>
          </Paper>
        </Tabs.Panel>
        
        <Tabs.Panel value="tasks">
          <Paper withBorder p="md" radius="md">
            <Title order={3}>Workspace Tasks</Title>
            <Text>Task management interface would be displayed here.</Text>
          </Paper>
        </Tabs.Panel>
      </Tabs>
    </Container>
  );
} 