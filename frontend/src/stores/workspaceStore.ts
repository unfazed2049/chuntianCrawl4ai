import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface WorkspaceState {
  currentWorkspace: string;
  setWorkspace: (workspace: string) => void;
}

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({
      currentWorkspace: 'default',
      setWorkspace: (workspace) => set({ currentWorkspace: workspace }),
    }),
    {
      name: 'workspace-storage',
    }
  )
);
