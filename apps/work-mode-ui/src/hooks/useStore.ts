import { create } from 'zustand';

export interface Agent {
  id: string;
  name: string;
  status: 'idle' | 'busy' | 'error';
  role: string;
  currentTask?: string;
  avatarUrl?: string;
}

export interface TimelineEvent {
  agentId: string;
  commitSha: string;
  timestamp: string;
  message: string;
  diffSize: number;
}

export interface Task {
  id: string;
  title: string;
  status: 'STARTED' | 'COMPLETE' | 'ERROR';
  agentId: string;
  createdAt: string;
  updatedAt: string;
}

interface StoreState {
  agents: Agent[];
  timelines: Record<string, TimelineEvent[]>;
  tasks: Task[];
  selectedCommit: string | null;
  focusMode: boolean;
  activeAgent: string | null;
  tokenBurnForecasts: Record<string, { perHourUsd: number; trend: 'up' | 'down' | 'stable' }>;
  
  // Actions
  setAgents: (agents: Agent[]) => void;
  addTimelineEvent: (event: TimelineEvent) => void;
  setSelectedCommit: (commitSha: string | null) => void;
  setTaskStatus: (payload: { taskId: string; status: Task['status'] }) => void;
  toggleFocusMode: () => void;
  setActiveAgent: (agentId: string | null) => void;
  setTokenForecast: (agentId: string, forecast: { perHourUsd: number; trend: 'up' | 'down' | 'stable' }) => void;
}

export const useStore = create<StoreState>((set) => ({
  agents: [],
  timelines: {},
  tasks: [],
  selectedCommit: null,
  focusMode: false,
  activeAgent: null,
  tokenBurnForecasts: {},
  
  setAgents: (agents) => set({ agents }),
  
  addTimelineEvent: (event) => set((state) => {
    const agentTimeline = state.timelines[event.agentId] || [];
    
    // Check if event already exists to avoid duplicates
    const eventExists = agentTimeline.some(
      (e) => e.commitSha === event.commitSha
    );
    
    if (eventExists) return state;
    
    return {
      timelines: {
        ...state.timelines,
        [event.agentId]: [event, ...agentTimeline].sort(
          (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        ),
      },
    };
  }),
  
  setSelectedCommit: (commitSha) => set({ selectedCommit: commitSha }),
  
  setTaskStatus: (payload) => set((state) => {
    const updatedTasks = state.tasks.map((task) => {
      if (task.id === payload.taskId) {
        return { ...task, status: payload.status, updatedAt: new Date().toISOString() };
      }
      return task;
    });
    
    return { tasks: updatedTasks };
  }),
  
  toggleFocusMode: () => set((state) => ({ focusMode: !state.focusMode })),
  
  setActiveAgent: (agentId) => set({ activeAgent: agentId }),
  
  setTokenForecast: (agentId, forecast) => set((state) => ({
    tokenBurnForecasts: {
      ...state.tokenBurnForecasts,
      [agentId]: forecast,
    },
  })),
})); 