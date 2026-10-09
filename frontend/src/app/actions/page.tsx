'use client';

import React, { useState } from 'react';
import { useClimateStore } from '../../store/useClimateStore';
import { RECOMMENDED_ACTIONS } from '../../data/mockData';
import { RoleContextBanner } from '../../components/roles/RoleContextBanner';
import { CheckSquare, Filter, Clock, DollarSign } from 'lucide-react';
import { UserRole } from '../../types';

export default function RecommendedActionsPage() {
  const { activeRole } = useClimateStore();
  const [selectedRoleFilter, setSelectedRoleFilter] = useState<UserRole | 'all'>('all');

  const filteredActions = RECOMMENDED_ACTIONS.filter((act) => {
    if (selectedRoleFilter === 'all') return true;
    return act.targetRoles.includes(selectedRoleFilter);
  });

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      <RoleContextBanner />

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <CheckSquare className="w-6 h-6 text-emerald-600 dark:text-emeraldGlow-400" />
            <span>Recommended Climate Action Interventions</span>
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Tailored mitigation, adaptation, and resilience action blueprints indexed by stakeholder persona.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-white dark:bg-earth-900 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
          <Filter className="w-3.5 h-3.5 text-cyan-600 dark:text-cyanGlow-400" />
          <span className="text-xs text-slate-700 dark:text-slate-300 font-medium">Filter Persona:</span>
          <select
            value={selectedRoleFilter}
            onChange={(e) => setSelectedRoleFilter(e.target.value as any)}
            className="bg-transparent text-xs text-slate-900 dark:text-slate-100 font-semibold focus:outline-none"
          >
            <option value="all" className="bg-white dark:bg-earth-950">All Personas</option>
            <option value="Citizen" className="bg-white dark:bg-earth-950">Citizen</option>
            <option value="Government" className="bg-white dark:bg-earth-950">Government</option>
            <option value="Municipality" className="bg-white dark:bg-earth-950">Municipality</option>
            <option value="NGO" className="bg-white dark:bg-earth-950">NGO</option>
            <option value="Researcher" className="bg-white dark:bg-earth-950">Researcher</option>
            <option value="Administrator" className="bg-white dark:bg-earth-950">Administrator</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredActions.map((act) => {
          const isTargetingActiveRole = act.targetRoles.includes(activeRole);
          return (
            <div
              key={act.id}
              className={`glass-panel p-5 border space-y-3 relative overflow-hidden transition-all ${
                isTargetingActiveRole
                  ? 'border-cyan-400 dark:border-cyanGlow-500/50 shadow-md dark:shadow-glow-cyan bg-cyan-50/40 dark:bg-earth-850/80'
                  : 'border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-earth-900/60'
              }`}
            >
              {isTargetingActiveRole && (
                <div className="absolute top-0 right-0 px-3 py-0.5 bg-cyan-500 text-white dark:bg-cyanGlow-500 dark:text-earth-950 font-bold text-[10px] uppercase tracking-wider rounded-bl-lg">
                  Matches Active Persona ({activeRole})
                </div>
              )}

              <div className="flex items-start justify-between pr-16">
                <div>
                  <span className="text-[10px] font-semibold text-cyan-600 dark:text-cyanGlow-400 uppercase tracking-wider">
                    {act.category}
                  </span>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 mt-0.5">{act.title}</h3>
                </div>
              </div>

              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">{act.description}</p>

              <div className="flex flex-wrap gap-1.5 pt-2">
                {act.targetRoles.map((role) => (
                  <span
                    key={role}
                    className={`px-2 py-0.5 rounded text-[10px] font-medium border ${
                      role === activeRole
                        ? 'bg-cyan-100 dark:bg-cyanGlow-500/20 text-cyan-700 dark:text-cyanGlow-400 border-cyan-300 dark:border-cyanGlow-500/40'
                        : 'bg-slate-100 dark:bg-earth-950 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-800'
                    }`}
                  >
                    {role}
                  </span>
                ))}
              </div>

              <div className="pt-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                <div className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" />
                  <span>{act.timeframe}</span>
                </div>
                <div className="flex items-center gap-1">
                  <DollarSign className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                  <span>{act.estimatedCost}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
