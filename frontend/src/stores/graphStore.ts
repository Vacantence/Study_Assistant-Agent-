import { create } from 'zustand';
import type { GraphNode, GraphEdge } from '../types';
import { graphApi } from '../api/graph';

interface GraphState {
  nodes: GraphNode[];
  edges: GraphEdge[];
  loading: boolean;
  fetchGraph: () => Promise<void>;
  clearGraph: () => Promise<void>;
}

export const useGraphStore = create<GraphState>((set) => ({
  nodes: [],
  edges: [],
  loading: false,

  fetchGraph: async () => {
    set({ loading: true });
    const g = await graphApi.getGraph();
    set({ nodes: g.nodes, edges: g.edges, loading: false });
  },

  clearGraph: async () => {
    await graphApi.clearGraph();
    set({ nodes: [], edges: [] });
  },
}));
