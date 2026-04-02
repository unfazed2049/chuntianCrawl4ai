import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface WorkspaceState {
  currentWorkspace: string;
  setWorkspace: (workspace: string) => void;
}

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({
      currentWorkspace: 'hpp',
      setWorkspace: (workspace) => set({ currentWorkspace: workspace || 'hpp' }),
    }),
    {
      name: 'workspace-storage',
      merge: (persistedState, currentState) => {
        const persistedWorkspace = (persistedState as Partial<WorkspaceState> | undefined)?.currentWorkspace;

        return {
          ...currentState,
          ...(persistedState as Partial<WorkspaceState> | undefined),
          currentWorkspace: persistedWorkspace && persistedWorkspace !== 'default'
            ? persistedWorkspace
            : currentState.currentWorkspace,
        };
      },
    }
  )
);
