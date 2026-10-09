import { create } from 'zustand';
import { UserRole, ClimateLocation, EnvironmentalDomainId } from '../types';
import { LOCATIONS } from '../data/mockData';

export type AppTheme = 'dark' | 'light';

interface ClimateState {
  activeRole: UserRole;
  selectedLocation: ClimateLocation;
  activeDomainFilter: EnvironmentalDomainId | 'all';
  searchQuery: string;
  isSidebarOpen: boolean;
  theme: AppTheme;
  
  // Actions
  setActiveRole: (role: UserRole) => void;
  setSelectedLocation: (location: ClimateLocation) => void;
  setSelectedLocationById: (id: string, locationsList?: ClimateLocation[]) => void;
  setActiveDomainFilter: (domainId: EnvironmentalDomainId | 'all') => void;
  setSearchQuery: (query: string) => void;
  toggleSidebar: () => void;
  setIsSidebarOpen: (isOpen: boolean) => void;
  setTheme: (theme: AppTheme) => void;
  toggleTheme: () => void;
  initTheme: () => void;
}

export const useClimateStore = create<ClimateState>((set, get) => ({
  activeRole: 'Government',
  selectedLocation: LOCATIONS[0],
  activeDomainFilter: 'all',
  searchQuery: '',
  isSidebarOpen: true,
  theme: 'dark',

  setActiveRole: (role) => set({ activeRole: role }),
  setSelectedLocation: (location) => set({ selectedLocation: location }),
  setSelectedLocationById: (id, locationsList?) => set((state) => {
    const list = locationsList || LOCATIONS;
    const loc = list.find((l) => l.id === id);
    return loc ? { selectedLocation: loc } : state;
  }),
  setActiveDomainFilter: (domainId) => set({ activeDomainFilter: domainId }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  setIsSidebarOpen: (isOpen) => set({ isSidebarOpen: isOpen }),

  setTheme: (theme: AppTheme) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('climatex-theme', theme);
      if (theme === 'dark') {
        document.documentElement.classList.add('dark');
        document.documentElement.classList.remove('light');
      } else {
        document.documentElement.classList.remove('dark');
        document.documentElement.classList.add('light');
      }
    }
    set({ theme });
  },

  toggleTheme: () => {
    const newTheme = get().theme === 'dark' ? 'light' : 'dark';
    get().setTheme(newTheme);
  },

  initTheme: () => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('climatex-theme') as AppTheme | null;
      const initialTheme = stored || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'dark');
      get().setTheme(initialTheme);
    }
  },
}));
