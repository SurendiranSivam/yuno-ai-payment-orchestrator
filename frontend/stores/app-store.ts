import { create } from "zustand";
import type { WorkflowEvent, DashboardStats } from "@/lib/api";

interface AppState {
  // Realtime events buffer (latest 100)
  liveEvents: WorkflowEvent[];
  addLiveEvent: (event: WorkflowEvent) => void;

  // Dashboard stats
  stats: DashboardStats | null;
  setStats: (stats: DashboardStats) => void;

  // Active workflow notification
  activeWorkflowId: string | null;
  setActiveWorkflowId: (id: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  liveEvents: [],
  addLiveEvent: (event) =>
    set((state) => ({
      liveEvents: [event, ...state.liveEvents].slice(0, 100),
    })),

  stats: null,
  setStats: (stats) => set({ stats }),

  activeWorkflowId: null,
  setActiveWorkflowId: (id) => set({ activeWorkflowId: id }),
}));
