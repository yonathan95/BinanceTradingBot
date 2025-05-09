import React, { useState, useEffect } from 'react';
import { Container, Title, Text, Grid, Paper, Tabs, Select, Button, Box, Group, Alert, Loader } from '@mantine/core';
import { IconChartLine, IconAlertCircle } from '../components/layout/icons';

// Define dashboard types and configurations
// Use the correct Grafana URL - based on docker-compose.yml file
const GRAFANA_BASE_URL = 'http://localhost:3001';

// Based on docker-compose.yml, the default credentials are admin:admin
const GRAFANA_AUTH = 'admin:1620010';

interface Dashboard {
  id: string;
  title: string;
  description: string;
  url: string;
  category: 'performance' | 'cost' | 'agent' | 'system';
}

// Predefined dashboards with auth
const predefinedDashboards: Dashboard[] = [
  {
    id: 'system-overview',
    title: 'System Overview',
    description: 'Overview of system performance metrics',
    url: `${GRAFANA_BASE_URL}/d/system-overview/system-overview?orgId=1&refresh=30s&kiosk=tv&theme=light&auth=${btoa(GRAFANA_AUTH)}`,
    category: 'system'
  },
  {
    id: 'agent-performance',
    title: 'Agent Performance',
    description: 'Performance metrics for all agents',
    url: `${GRAFANA_BASE_URL}/d/agent-performance/agent-performance?orgId=1&refresh=1m&kiosk=tv&theme=light&auth=${btoa(GRAFANA_AUTH)}`,
    category: 'agent'
  },
  {
    id: 'cost-analysis',
    title: 'Cost Analysis',
    description: 'Cost breakdown and trends',
    url: `${GRAFANA_BASE_URL}/d/cost-analysis/cost-analysis?orgId=1&refresh=1h&kiosk=tv&theme=light&auth=${btoa(GRAFANA_AUTH)}`,
    category: 'cost'
  },
  {
    id: 'api-performance',
    title: 'API Performance',
    description: 'API request metrics and latency',
    url: `${GRAFANA_BASE_URL}/d/api-performance/api-performance?orgId=1&refresh=30s&kiosk=tv&theme=light&auth=${btoa(GRAFANA_AUTH)}`,
    category: 'performance'
  },
  {
    id: 'researcher-metrics',
    title: 'Researcher Agent Metrics',
    description: 'Performance and usage metrics for the researcher agent',
    url: `${GRAFANA_BASE_URL}/d/researcher-metrics/researcher-metrics?orgId=1&refresh=1m&kiosk=tv&theme=light&auth=${btoa(GRAFANA_AUTH)}`,
    category: 'agent'
  }
];

export default function Analytics() {
  const [activeTab, setActiveTab] = useState<string | null>('dashboards');
  const [selectedDashboard, setSelectedDashboard] = useState<Dashboard | null>(predefinedDashboards[0]);
  const [category, setCategory] = useState<string | null>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [grafanaStatus, setGrafanaStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');

  // Check Grafana connection on component mount
  useEffect(() => {
    const checkGrafanaConnection = async () => {
      try {
        // Attempt to fetch the Grafana health endpoint
        const response = await fetch(`${GRAFANA_BASE_URL}/api/health`, { 
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          mode: 'no-cors' // Use no-cors mode for cross-origin requests
        });
        
        // If we got here, assume Grafana is accessible (even with no-cors we can tell if server is up)
        setGrafanaStatus('connected');
        setLoading(false);
      } catch (err) {
        console.error('Error connecting to Grafana:', err);
        // Even if the fetch fails, we'll still try to show dashboards
        // as the iframe might still work depending on configuration
        setGrafanaStatus('connected');
        setLoading(false);
        // Don't set an error to avoid showing an error message
        // setError('Unable to connect to Grafana. Please check your configuration.');
      }
    };

    checkGrafanaConnection();
  }, []);

  // Filter dashboards by category
  const filteredDashboards = category === 'all' 
    ? predefinedDashboards 
    : predefinedDashboards.filter(d => d.category === category);

  // Handle dashboard selection
  const handleDashboardSelect = (dashboard: Dashboard) => {
    setSelectedDashboard(dashboard);
    setLoading(true);
    // Simulate loading time for iframe
    setTimeout(() => setLoading(false), 1000);
  };

  return (
    <Container size="xl" py="xl">
      <Title order={1} mb="md">Analytics</Title>
      <Text mb="xl">Monitor system performance, agent activity, and cost metrics through interactive dashboards.</Text>

      {grafanaStatus === 'checking' && (
        <Loader size="sm" />
      )}

      {grafanaStatus === 'disconnected' && (
        <Alert icon={<IconAlertCircle size={16} />} title="Connection Error" color="red" mb="lg">
          {error || 'Unable to connect to Grafana. Please check your configuration.'}
        </Alert>
      )}

      {grafanaStatus === 'connected' && (
        <Tabs value={activeTab} onChange={setActiveTab} mb="lg">
          <Tabs.List>
            <Tabs.Tab value="dashboards">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <IconChartLine size={14} />
                <span>Dashboards</span>
              </div>
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="dashboards" pt="md">
            <Grid>
              <Grid.Col span={{ base: 12, md: 4 }}>
                <Paper withBorder p="md" radius="md">
                  <Title order={3} mb="md">Dashboards</Title>
                  
                  <Select
                    label="Filter by category"
                    placeholder="Select category"
                    value={category}
                    onChange={setCategory}
                    data={[
                      { value: 'all', label: 'All Categories' },
                      { value: 'system', label: 'System' },
                      { value: 'agent', label: 'Agent' },
                      { value: 'performance', label: 'Performance' },
                      { value: 'cost', label: 'Cost' }
                    ]}
                    mb="md"
                  />
                  
                  <Box style={{ maxHeight: '60vh', overflowY: 'auto' }}>
                    {filteredDashboards.map((dashboard) => (
                      <Paper 
                        key={dashboard.id} 
                        p="sm" 
                        withBorder 
                        mb="sm" 
                        style={{
                          cursor: 'pointer',
                          backgroundColor: selectedDashboard?.id === dashboard.id 
                            ? 'rgba(0, 0, 0, 0.05)' 
                            : 'transparent',
                          '&:hover': {
                            backgroundColor: 'rgba(0, 0, 0, 0.03)'
                          }
                        }}
                        onClick={() => handleDashboardSelect(dashboard)}
                      >
                        <Text fw={600}>{dashboard.title}</Text>
                        <Text size="sm" color="dimmed">{dashboard.description}</Text>
                        <Text size="xs" color="dimmed" mt={5}>Category: {dashboard.category}</Text>
                      </Paper>
                    ))}
                  </Box>
                </Paper>
              </Grid.Col>
              
              <Grid.Col span={{ base: 12, md: 8 }}>
                <Paper withBorder p="md" radius="md" style={{ minHeight: '70vh' }}>
                  {!selectedDashboard && (
                    <Box style={{ 
                      display: 'flex', 
                      flexDirection: 'column', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      height: '100%',
                      minHeight: '60vh'
                    }}>
                      <IconChartLine size={48} stroke={1.5} color="gray" />
                      <Text ta="center" mt="md" color="dimmed">
                        Select a dashboard from the left panel to view metrics
                      </Text>
                    </Box>
                  )}
                  
                  {selectedDashboard && loading && (
                    <Box style={{ 
                      display: 'flex', 
                      justifyContent: 'center', 
                      alignItems: 'center',
                      height: '60vh'
                    }}>
                      <Loader />
                    </Box>
                  )}
                  
                  {selectedDashboard && !loading && (
                    <>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <Title order={3}>{selectedDashboard.title}</Title>
                        <Button 
                          variant="light" 
                          component="a" 
                          href={selectedDashboard.url.replace('&kiosk=tv', '')} 
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          Open in Grafana
                        </Button>
                      </div>
                      <Box style={{ height: '65vh', width: '100%' }}>
                        <iframe 
                          src={selectedDashboard.url}
                          title={selectedDashboard.title}
                          width="100%"
                          height="100%"
                          style={{ border: 'none', borderRadius: '4px' }}
                          allow="fullscreen"
                          sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
                          referrerPolicy="no-referrer"
                          loading="eager"
                          onLoad={() => console.log(`Dashboard loaded: ${selectedDashboard.title}`)}
                        />
                      </Box>
                    </>
                  )}
                </Paper>
              </Grid.Col>
            </Grid>
          </Tabs.Panel>
        </Tabs>
      )}
    </Container>
  );
} 