import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface CostData {
  date: string;
  amount: number;
  model: string;
}

interface TaskData {
  id: string;
  name: string;
  status: 'completed' | 'in_progress' | 'pending' | 'failed';
  created_at: string;
  completed_at: string | null;
  assigned_to: string[];
  priority: 'high' | 'medium' | 'low';
}

interface ResourceUsage {
  agent: string;
  tokens: number;
  requests: number;
  cost: number;
}

interface ProjectMetricsProps {
  projectId: string;
  timeRange: 'day' | 'week' | 'month' | 'all';
}

const ProjectMetrics: React.FC<ProjectMetricsProps> = ({ projectId, timeRange }) => {
  const [costData, setCostData] = useState<CostData[]>([]);
  const [tasks, setTasks] = useState<TaskData[]>([]);
  const [resourceUsage, setResourceUsage] = useState<ResourceUsage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeMetric, setActiveMetric] = useState<'cost' | 'tasks' | 'resources'>('cost');

  useEffect(() => {
    const fetchMetricsData = async () => {
      try {
        setIsLoading(true);
        const [costResponse, tasksResponse, resourcesResponse] = await Promise.all([
          axios.get(`/api/projects/${projectId}/metrics/cost?timeRange=${timeRange}`),
          axios.get(`/api/projects/${projectId}/metrics/tasks?timeRange=${timeRange}`),
          axios.get(`/api/projects/${projectId}/metrics/resources?timeRange=${timeRange}`)
        ]);
        
        setCostData(costResponse.data);
        setTasks(tasksResponse.data);
        setResourceUsage(resourcesResponse.data);
        setError('');
      } catch (err) {
        setError('Failed to load metrics data');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMetricsData();
  }, [projectId, timeRange]);

  // Prepare cost chart data
  const costChartData = {
    labels: costData.map(item => {
      const date = new Date(item.date);
      return date.toLocaleDateString();
    }),
    datasets: [
      {
        label: 'Daily Cost',
        data: costData.map(item => item.amount),
        fill: false,
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        borderColor: 'rgba(75, 192, 192, 1)',
        tension: 0.4,
      },
    ],
  };

  // Prepare task status chart data
  const taskStatusCounts = {
    completed: tasks.filter(task => task.status === 'completed').length,
    in_progress: tasks.filter(task => task.status === 'in_progress').length,
    pending: tasks.filter(task => task.status === 'pending').length,
    failed: tasks.filter(task => task.status === 'failed').length,
  };

  const taskStatusChartData = {
    labels: ['Completed', 'In Progress', 'Pending', 'Failed'],
    datasets: [
      {
        data: [
          taskStatusCounts.completed,
          taskStatusCounts.in_progress,
          taskStatusCounts.pending,
          taskStatusCounts.failed,
        ],
        backgroundColor: [
          'rgba(75, 192, 192, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(255, 99, 132, 0.6)',
        ],
        borderColor: [
          'rgba(75, 192, 192, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(255, 99, 132, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  // Prepare resource usage chart data
  const resourceChartData = {
    labels: resourceUsage.map(item => item.agent),
    datasets: [
      {
        label: 'Resource Usage (Cost)',
        data: resourceUsage.map(item => item.cost),
        backgroundColor: 'rgba(153, 102, 255, 0.6)',
        borderColor: 'rgba(153, 102, 255, 1)',
        borderWidth: 1,
      },
    ],
  };

  // Calculate project completion percentage
  const completionPercentage = tasks.length > 0
    ? Math.round((taskStatusCounts.completed / tasks.length) * 100)
    : 0;

  // Calculate total cost
  const totalCost = costData.reduce((sum, item) => sum + item.amount, 0);

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading project metrics...</p>
      </div>
    );
  }

  return (
    <div className="project-metrics">
      <div className="metrics-header">
        <h3>Project Metrics</h3>
        <div className="metrics-tabs">
          <button 
            className={`tab ${activeMetric === 'cost' ? 'active' : ''}`}
            onClick={() => setActiveMetric('cost')}
          >
            Cost
          </button>
          <button 
            className={`tab ${activeMetric === 'tasks' ? 'active' : ''}`}
            onClick={() => setActiveMetric('tasks')}
          >
            Tasks
          </button>
          <button 
            className={`tab ${activeMetric === 'resources' ? 'active' : ''}`}
            onClick={() => setActiveMetric('resources')}
          >
            Resources
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="metrics-summary">
        <div className="metric-card">
          <div className="metric-title">Completion</div>
          <div className="metric-value">
            <div className="completion-bar">
              <div 
                className="completion-progress"
                style={{ width: `${completionPercentage}%` }}
              ></div>
            </div>
            <span>{completionPercentage}%</span>
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-title">Total Cost</div>
          <div className="metric-value">${totalCost.toFixed(2)}</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-title">Active Tasks</div>
          <div className="metric-value">{taskStatusCounts.in_progress}</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-title">Completed Tasks</div>
          <div className="metric-value">{taskStatusCounts.completed}</div>
        </div>
      </div>

      <div className="metrics-content">
        {activeMetric === 'cost' && (
          <div className="cost-metrics">
            <div className="chart-container">
              <h4>Cost Over Time</h4>
              {costData.length > 0 ? (
                <Line 
                  data={costChartData}
                  options={{
                    responsive: true,
                    scales: {
                      y: {
                        beginAtZero: true,
                        title: {
                          display: true,
                          text: 'Cost ($)'
                        }
                      },
                      x: {
                        title: {
                          display: true,
                          text: 'Date'
                        }
                      }
                    }
                  }}
                />
              ) : (
                <p className="empty-message">No cost data available</p>
              )}
            </div>
            
            <div className="cost-breakdown">
              <h4>Cost Breakdown</h4>
              <table className="metrics-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Model</th>
                    <th>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {costData.length > 0 ? (
                    costData.map((item, index) => (
                      <tr key={index}>
                        <td>{new Date(item.date).toLocaleDateString()}</td>
                        <td>{item.model}</td>
                        <td>${item.amount.toFixed(2)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={3} className="empty-message">No cost data available</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeMetric === 'tasks' && (
          <div className="task-metrics">
            <div className="chart-container">
              <h4>Task Status</h4>
              {tasks.length > 0 ? (
                <Doughnut 
                  data={taskStatusChartData}
                  options={{
                    responsive: true,
                    plugins: {
                      legend: {
                        position: 'right',
                      }
                    }
                  }}
                />
              ) : (
                <p className="empty-message">No task data available</p>
              )}
            </div>
            
            <div className="task-list">
              <h4>Recent Tasks</h4>
              <table className="metrics-table">
                <thead>
                  <tr>
                    <th>Task</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Created</th>
                    <th>Assigned To</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.length > 0 ? (
                    tasks.slice(0, 5).map((task) => (
                      <tr key={task.id} className={`task-row ${task.status}`}>
                        <td>{task.name}</td>
                        <td>
                          <span className={`status-badge ${task.status}`}>
                            {task.status.replace('_', ' ')}
                          </span>
                        </td>
                        <td>{task.priority}</td>
                        <td>{new Date(task.created_at).toLocaleDateString()}</td>
                        <td>{task.assigned_to.join(', ')}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="empty-message">No tasks available</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeMetric === 'resources' && (
          <div className="resource-metrics">
            <div className="chart-container">
              <h4>Resource Usage by Agent</h4>
              {resourceUsage.length > 0 ? (
                <Bar 
                  data={resourceChartData}
                  options={{
                    responsive: true,
                    scales: {
                      y: {
                        beginAtZero: true,
                        title: {
                          display: true,
                          text: 'Cost ($)'
                        }
                      }
                    }
                  }}
                />
              ) : (
                <p className="empty-message">No resource usage data available</p>
              )}
            </div>
            
            <div className="resource-breakdown">
              <h4>Resource Breakdown</h4>
              <table className="metrics-table">
                <thead>
                  <tr>
                    <th>Agent</th>
                    <th>Tokens</th>
                    <th>Requests</th>
                    <th>Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {resourceUsage.length > 0 ? (
                    resourceUsage.map((resource, index) => (
                      <tr key={index}>
                        <td>{resource.agent}</td>
                        <td>{resource.tokens.toLocaleString()}</td>
                        <td>{resource.requests}</td>
                        <td>${resource.cost.toFixed(2)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="empty-message">No resource data available</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectMetrics; 