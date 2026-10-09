'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useClimateStore } from '../../store/useClimateStore';
import {
  LayoutDashboard,
  Compass,
  Layers,
  AlertTriangle,
  TrendingUp,
  Sliders,
  CheckSquare,
  ShieldCheck,
  Settings,
  MapPin,
  Sparkles,
  ExternalLink,
} from 'lucide-react';

interface NavItem {
  name: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { name: 'Dashboard', href: '/', icon: <LayoutDashboard className="w-4 h-4" /> },
  { name: 'Explore Map', href: '/explore', icon: <Compass className="w-4 h-4" /> },
  { name: 'Environmental Domains', href: '/domains', icon: <Layers className="w-4 h-4" />, badge: '9' },
  { name: 'Location Intelligence', href: '/location', icon: <MapPin className="w-4 h-4 text-cyan-600 dark:text-cyanGlow-400" /> },
  { name: 'Climate Risk', href: '/climate-risk', icon: <AlertTriangle className="w-4 h-4" /> },
  { name: 'Future Prediction', href: '/prediction', icon: <TrendingUp className="w-4 h-4" /> },
  { name: 'What-if Simulation', href: '/simulation', icon: <Sliders className="w-4 h-4" /> },
  { name: 'Recommended Actions', href: '/actions', icon: <CheckSquare className="w-4 h-4" /> },
  { name: 'Impact Verification', href: '/verification', icon: <ShieldCheck className="w-4 h-4" /> },
  { name: 'Settings', href: '/settings', icon: <Settings className="w-4 h-4" /> },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { isSidebarOpen, selectedLocation, activeRole } = useClimateStore();

  if (!isSidebarOpen) return null;

  return (
    <aside className="w-64 shrink-0 bg-white/90 dark:bg-earth-950/90 border-r border-slate-200 dark:border-slate-800/80 min-h-[calc(100vh-61px)] p-4 flex flex-col justify-between backdrop-blur-md transition-colors duration-300 z-30">
      <div className="space-y-6">
        {/* Navigation Items */}
        <div className="space-y-1">
          <div className="px-3 py-1.5 text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider font-mono">
            Navigation Menu
          </div>

          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all group ${
                  isActive
                    ? 'bg-cyan-50 dark:bg-gradient-to-r dark:from-cyanGlow-600/20 dark:to-earth-850 text-cyan-700 dark:text-cyanGlow-400 border border-cyan-200 dark:border-cyanGlow-500/30 shadow-sm dark:shadow-glow-cyan'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className={isActive ? 'text-cyan-600 dark:text-cyanGlow-400' : 'text-slate-500 dark:text-slate-400 group-hover:text-slate-800 dark:group-hover:text-slate-200'}>
                    {item.icon}
                  </span>
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-100 dark:bg-earth-900 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </div>

        {/* Selected Location Quick Context Card */}
        <div className="glass-panel p-3.5 border border-slate-200 dark:border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Active Focus Site
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 dark:bg-cyanGlow-400 animate-ping" />
          </div>
          <div>
            <div className="text-xs font-bold text-slate-800 dark:text-slate-100 truncate">{selectedLocation.name}</div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400 font-mono mt-0.5">{selectedLocation.landform}</div>
          </div>
          <Link
            href="/location"
            className="w-full mt-2 inline-flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg text-[11px] font-medium bg-cyan-50 dark:bg-cyanGlow-500/10 hover:bg-cyan-100 dark:hover:bg-cyanGlow-500/20 text-cyan-700 dark:text-cyanGlow-400 border border-cyan-200 dark:border-cyanGlow-500/30 transition-colors"
          >
            <span>Location Intelligence</span>
            <ExternalLink className="w-3 h-3" />
          </Link>
        </div>
      </div>

      {/* Footer Role Identifier Pill */}
      <div className="pt-4 border-t border-slate-200 dark:border-slate-800/80">
        <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
          <span>Persona View</span>
          <span className="font-semibold text-cyan-600 dark:text-cyanGlow-400">{activeRole}</span>
        </div>
      </div>
    </aside>
  );
};
