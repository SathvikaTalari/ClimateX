'use client';

import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { useClimateStore } from '../../store/useClimateStore';

const projectionData = [
  { year: '2024', historical: 1.2, ssp126: 1.2, ssp245: 1.2, ssp585: 1.2 },
  { year: '2026', historical: 1.3, ssp126: 1.3, ssp245: 1.3, ssp585: 1.35 },
  { year: '2030', ssp126: 1.4, ssp245: 1.55, ssp585: 1.7 },
  { year: '2035', ssp126: 1.45, ssp245: 1.75, ssp585: 2.1 },
  { year: '2040', ssp126: 1.5, ssp245: 1.95, ssp585: 2.5 },
  { year: '2050', ssp126: 1.52, ssp245: 2.3, ssp585: 3.2 },
  { year: '2060', ssp126: 1.55, ssp245: 2.6, ssp585: 4.1 },
];

export const PredictionTimelineChart: React.FC = () => {
  const { theme } = useClimateStore();
  const isDark = theme === 'dark';

  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={projectionData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorSSP1" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorSSP2" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4}/>
              <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorSSP5" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4}/>
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#1f2b48' : '#e2e8f0'} />
          <XAxis
            dataKey="year"
            stroke={isDark ? '#94a3b8' : '#475569'}
            tick={{ fill: isDark ? '#94a3b8' : '#475569', fontSize: 11 }}
          />
          <YAxis 
            stroke={isDark ? '#94a3b8' : '#475569'} 
            tick={{ fill: isDark ? '#94a3b8' : '#475569', fontSize: 11 }} 
            unit="°C"
            domain={[0, 5]} 
          />
          <Tooltip
            contentStyle={{
              backgroundColor: isDark ? '#0b0f19' : '#ffffff',
              borderColor: isDark ? '#1e293b' : '#e2e8f0',
              borderRadius: '8px',
              color: isDark ? '#f8fafc' : '#0f172a',
              fontSize: '12px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
          />
          <Legend
            wrapperStyle={{
              fontSize: '11px',
              paddingTop: '10px',
              color: isDark ? '#94a3b8' : '#475569',
            }}
          />
          <Area
            type="monotone"
            dataKey="ssp126"
            name="SSP1-2.6 (1.5°C Goal)"
            stroke="#10b981"
            fillOpacity={1}
            fill="url(#colorSSP1)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="ssp245"
            name="SSP2-4.5 (Middle of Road)"
            stroke="#f59e0b"
            fillOpacity={1}
            fill="url(#colorSSP2)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="ssp585"
            name="SSP5-8.5 (High Emissions)"
            stroke="#ef4444"
            fillOpacity={1}
            fill="url(#colorSSP5)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
