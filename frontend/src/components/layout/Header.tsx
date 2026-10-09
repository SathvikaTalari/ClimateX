'use client';

import React from 'react';
import { LocationSearch } from '../map/LocationSearch';
import { RoleSwitcher } from '../roles/RoleSwitcher';
import { Globe, Menu, Satellite, ShieldCheck, Bell, Sun, Moon } from 'lucide-react';
import { useClimateStore } from '../../store/useClimateStore';

export const Header: React.FC = () => {
  const { toggleSidebar, isSidebarOpen, activeRole, theme, toggleTheme } = useClimateStore();

  return (
    <header className="sticky top-0 z-40 bg-white/80 dark:bg-earth-950/80 backdrop-blur-xl border-b border-slate-200 dark:border-slate-800/80 px-4 lg:px-6 py-3 transition-colors duration-300">
      <div className="flex items-center justify-between gap-4">
        {/* Left Side: Mobile Menu Toggle + Brand Logo */}
        <div className="flex items-center gap-3">
          <button
            onClick={toggleSidebar}
            className="p-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200/60 dark:hover:bg-slate-800/60 rounded-xl transition-colors"
            title="Toggle Navigation Menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyanGlow-600 via-emeraldGlow-500 to-cyanGlow-400 p-0.5 shadow-glow-cyan">
              <div className="w-full h-full bg-white dark:bg-earth-950 rounded-[10px] flex items-center justify-center transition-colors">
                <Globe className="w-5 h-5 text-cyan-600 dark:text-cyanGlow-400 animate-pulse" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-base font-extrabold tracking-tight text-slate-900 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-r dark:from-slate-100 dark:via-cyanGlow-400 dark:to-emeraldGlow-400">
                  ClimateX
                </span>
                <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-cyan-100 text-cyan-700 dark:bg-cyanGlow-500/20 dark:text-cyanGlow-400 border border-cyan-300 dark:border-cyanGlow-500/30 uppercase">
                  v2.4
                </span>
              </div>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 font-medium hidden sm:block">
                AI Earth Intelligence Platform
              </p>
            </div>
          </div>
        </div>

        {/* Center: Global Location Search */}
        <div className="flex-1 max-w-md hidden md:block">
          <LocationSearch />
        </div>

        {/* Right Side: Role Switcher, Theme Toggle & System Telemetry Status */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Role Switcher */}
          <div className="hidden xl:block">
            <RoleSwitcher />
          </div>

          {/* Satellite Data Status Pill */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-earth-900 border border-slate-200 dark:border-slate-800 text-[11px] transition-colors">
            <Satellite className="w-3.5 h-3.5 text-cyan-600 dark:text-cyanGlow-400" />
            <span className="text-slate-700 dark:text-slate-300 font-medium">Sentinel-2 Ingest</span>
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          </div>

          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            className="p-2 text-slate-600 dark:text-slate-300 hover:text-cyan-600 dark:hover:text-cyanGlow-400 hover:bg-slate-200/70 dark:hover:bg-slate-800/80 rounded-xl transition-all border border-slate-200 dark:border-slate-800 shadow-sm"
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-amber-400 animate-in spin-in-180 duration-300" />
            ) : (
              <Moon className="w-4 h-4 text-slate-700 animate-in spin-in-180 duration-300" />
            )}
          </button>

          {/* Quick Notifications */}
          <button className="p-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200/60 dark:hover:bg-slate-800/60 rounded-xl transition-colors relative">
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-cyan-500 dark:bg-cyanGlow-400" />
          </button>
        </div>
      </div>

      {/* Mobile Location Search & Role Switcher Bar */}
      <div className="mt-3 flex flex-col gap-2 md:hidden">
        <LocationSearch />
        <div className="overflow-x-auto pt-1">
          <RoleSwitcher />
        </div>
      </div>
    </header>
  );
};
