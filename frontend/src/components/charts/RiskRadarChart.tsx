'use client';

import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import { useClimateStore } from '../../store/useClimateStore';

const sampleRiskData = [
  { subject: 'Heat Stress', A: 85, fullMark: 100 },
  { subject: 'Drought Deficit', A: 68, fullMark: 100 },
  { subject: 'Wildfire Hazard', A: 92, fullMark: 100 },
  { subject: 'Flood Vulnerability', A: 45, fullMark: 100 },
  { subject: 'Coastal Erosion', A: 78, fullMark: 100 },
  { subject: 'Biodiversity Loss', A: 88, fullMark: 100 },
];

export const RiskRadarChart: React.FC = () => {
  const { theme } = useClimateStore();
  const isDark = theme === 'dark';

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={sampleRiskData}>
          <PolarGrid stroke={isDark ? '#1f2b48' : '#cbd5e1'} />
          <PolarAngleAxis
            dataKey="subject"
            stroke={isDark ? '#94a3b8' : '#475569'}
            tick={{ fill: isDark ? '#94a3b8' : '#475569', fontSize: 11 }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            stroke={isDark ? '#334155' : '#94a3b8'}
          />
          <Radar
            name="Climate Risk Index"
            dataKey="A"
            stroke={isDark ? '#00f2fe' : '#0284c7'}
            fill={isDark ? '#00f2fe' : '#0284c7'}
            fillOpacity={isDark ? 0.3 : 0.25}
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
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};
