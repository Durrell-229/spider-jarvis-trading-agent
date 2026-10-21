import { create } from 'zustand';
import type { EventLog, JEVDecision, PaperStats, SpiderState, SystemStatus, TokenNode } from '../types';

interface AppState {
  status: SystemStatus | null;
  nodes: TokenNode[];
  events: EventLog[];
  jev: JEVDecision | null;
  paperStats: PaperStats | null;
  spiderState: SpiderState;
  spiderColor: string;
  spiderMessage: string;
  connected: boolean;
  setStatus: (s: SystemStatus) => void;
  setNodes: (n: TokenNode[]) => void;
  addEvent: (e: EventLog) => void;
  setJev: (j: JEVDecision) => void;
  setPaperStats: (p: PaperStats) => void;
  setSpider: (state: SpiderState, message: string, color: string) => void;
  setConnected: (c: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  status: null,
  nodes: [],
  events: [],
  jev: null,
  paperStats: null,
  spiderState: 'IDLE',
  spiderColor: '#3b82f6',
  spiderMessage: 'En attente',
  connected: false,
  setStatus: (status) => set({ status, spiderState: status.spider_state }),
  setNodes: (nodes) => set({ nodes }),
  addEvent: (e) =>
    set((s) => ({ events: [e, ...s.events].slice(0, 200) })),
  setJev: (jev) => set({ jev }),
  setPaperStats: (paperStats) => set({ paperStats }),
  setSpider: (spiderState, spiderMessage, spiderColor) =>
    set({ spiderState, spiderMessage, spiderColor }),
  setConnected: (connected) => set({ connected }),
}));
