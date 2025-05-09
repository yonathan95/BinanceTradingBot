import React from 'react';
import { Title, Paper, Text, Container, Grid, Card, RingProgress, Group, ThemeIcon } from '@mantine/core';
import { IconMoneybag } from '../components/layout/icons';

export default function CostManagement() {
  // Example data
  const costData = {
    totalCost: 432.18,
    previousPeriod: 387.45,
    usage: {
      compute: 210.34,
      storage: 98.75,
      network: 54.28,
      api: 68.81
    }
  };

  const percentChange = ((costData.totalCost - costData.previousPeriod) / costData.previousPeriod) * 100;
  const isIncrease = percentChange > 0;

  return (
    <Container size="xl" py="xl">
      <Title order={1} mb="lg">Cost Management</Title>
      
      <Grid>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Paper withBorder p="xl" radius="md">
            <Group>
              <IconMoneybag size={28} color={isIncrease ? '#ef4444' : '#10b981'} />
              <Title order={3}>Cost Overview</Title>
            </Group>
            <Text size="xl" fw={700} mt="md">${costData.totalCost.toFixed(2)}</Text>
            <Group mt="md">
              <Text c={isIncrease ? 'red' : 'teal'}>
                <span style={{ display: 'inline-flex', alignItems: 'center' }}>
                  {isIncrease ? '+' : '-'}
                  {Math.abs(percentChange).toFixed(1)}%
                </span>
              </Text>
              <Text c="dimmed" size="sm">compared to previous period</Text>
            </Group>
          </Paper>
        </Grid.Col>
        
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Paper withBorder p="xl" radius="md">
            <Title order={3}>Resource Distribution</Title>
            <Group mt="md" grow>
              <RingProgress
                size={140}
                thickness={14}
                roundCaps
                sections={[
                  { value: (costData.usage.compute / costData.totalCost) * 100, color: 'blue' },
                  { value: (costData.usage.storage / costData.totalCost) * 100, color: 'cyan' },
                  { value: (costData.usage.network / costData.totalCost) * 100, color: 'indigo' },
                  { value: (costData.usage.api / costData.totalCost) * 100, color: 'violet' },
                ]}
              />
              <div>
                <Text size="xs" tt="uppercase" fw={700} c="dimmed">Distribution</Text>
                <Text size="xs" c="dimmed" mt={5}>
                  <Text span c="blue" fw={500}>Compute:</Text> ${costData.usage.compute.toFixed(2)}
                </Text>
                <Text size="xs" c="dimmed" mt={5}>
                  <Text span c="cyan" fw={500}>Storage:</Text> ${costData.usage.storage.toFixed(2)}
                </Text>
                <Text size="xs" c="dimmed" mt={5}>
                  <Text span c="indigo" fw={500}>Network:</Text> ${costData.usage.network.toFixed(2)}
                </Text>
                <Text size="xs" c="dimmed" mt={5}>
                  <Text span c="violet" fw={500}>API:</Text> ${costData.usage.api.toFixed(2)}
                </Text>
              </div>
            </Group>
          </Paper>
        </Grid.Col>
      </Grid>
      
      <Grid mt="lg">
        <Grid.Col span={12}>
          <Paper withBorder p="xl" radius="md">
            <Title order={3} mb="lg">Cost Breakdown</Title>
            <Text>
              This section would contain detailed cost breakdown tables and charts.
              For the demo version, this is a placeholder for future implementation.
            </Text>
          </Paper>
        </Grid.Col>
      </Grid>
    </Container>
  );
} 