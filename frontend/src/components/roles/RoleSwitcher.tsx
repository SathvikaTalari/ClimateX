import React from 'react';
import { useClimateStore } from '../../store/useClimateStore';
import { UserRole } from '../../types';
import { ROLE_INFO } from '../../data/mockData';
import { UserCheck, Shield, Building, HeartHandshake, Microchip, Lock } from 'lucide-react';

const ROLE_ICONS: Record<UserRole, React.ReactNode> = {
  Citizen: <UserCheck className="w-3.5 h-3.5" />,
  Government: <Shield className="w-3.5 h-3.5" />,
  Municipality: <Building className="w-3.5 h-3.5" />,
  NGO: <HeartHandshake className="w-3.5 h-3.5" />,
  Researcher: <Microchip className="w-3.5 h-3.5" />,
  Administrator: <Lock className="w-3.5 h-3.5" />,
};

const ROLES: UserRole[] = [
  'Citizen',
  'Government',
  'Municipality',
  'NGO',
  'Researcher',
  'Administrator',
];

export const RoleSwitcher: React.FC = () => {
  const { activeRole, setActiveRole } = useClimateStore();

  return (
    <div className="flex items-center gap-1 bg-slate-100/90 dark:bg-earth-950/80 p-1 rounded-xl border border-slate-200 dark:border-slate-800/80 overflow-x-auto max-w-full transition-colors">
      {ROLES.map((role) => {
        const isActive = activeRole === role;
        return (
          <button
            key={role}
            onClick={() => setActiveRole(role)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 whitespace-nowrap ${
              isActive
                ? 'bg-cyan-500 text-white dark:bg-gradient-to-r dark:from-cyanGlow-600/30 dark:to-earth-800 dark:text-cyanGlow-400 border border-cyan-500 dark:border-cyanGlow-500/40 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-200/60 dark:hover:bg-slate-800/50'
            }`}
          >
            <span className={isActive ? 'text-white dark:text-cyanGlow-400' : 'text-slate-500 dark:text-slate-400'}>
              {ROLE_ICONS[role]}
            </span>
            <span>{role}</span>
          </button>
        );
      })}
    </div>
  );
};
