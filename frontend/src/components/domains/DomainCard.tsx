import React from 'react';
import { EnvironmentalDomain } from '../../types';
import { useClimateStore } from '../../store/useClimateStore';
import { 
  Trees, 
  Waves, 
  Mountain, 
  Compass, 
  Anchor, 
  Building2, 
  ThermometerSun, 
  Wheat, 
  Sun,
  TrendingDown,
  TrendingUp,
  Activity
} from 'lucide-react';

const DOMAIN_ICONS: Record<string, React.ReactNode> = {
  Trees: <Trees className="w-5 h-5 text-emerald-500 dark:text-emerald-400" />,
  Waves: <Waves className="w-5 h-5 text-blue-500 dark:text-blue-400" />,
  Mountain: <Mountain className="w-5 h-5 text-indigo-500 dark:text-indigo-400" />,
  Compass: <Compass className="w-5 h-5 text-amber-500 dark:text-amber-400" />,
  Anchor: <Anchor className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />,
  Building2: <Building2 className="w-5 h-5 text-slate-600 dark:text-slate-300" />,
  ThermometerSun: <ThermometerSun className="w-5 h-5 text-rose-500 dark:text-rose-400" />,
  Wheat: <Wheat className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />,
  Sun: <Sun className="w-5 h-5 text-orange-500 dark:text-orange-400" />,
};

interface DomainCardProps {
  domain: EnvironmentalDomain;
  onSelect?: (domain: EnvironmentalDomain) => void;
}

export const DomainCard: React.FC<DomainCardProps> = ({ domain, onSelect }) => {
  const { activeDomainFilter, setActiveDomainFilter } = useClimateStore();
  const isSelected = activeDomainFilter === domain.id;

  const getStatusBadge = (status: EnvironmentalDomain['status']) => {
    switch (status) {
      case 'Critical Risk':
        return 'bg-rose-100 text-rose-700 border-rose-300 dark:bg-rose-500/20 dark:text-rose-400 dark:border-rose-500/30';
      case 'Vulnerable':
        return 'bg-amber-100 text-amber-700 border-amber-300 dark:bg-amber-500/20 dark:text-amber-400 dark:border-amber-500/30';
      case 'Stable':
        return 'bg-emerald-100 text-emerald-700 border-emerald-300 dark:bg-emerald-500/20 dark:text-emerald-400 dark:border-emerald-500/30';
      case 'Monitoring':
        return 'bg-cyan-100 text-cyan-700 border-cyan-300 dark:bg-cyan-500/20 dark:text-cyan-400 dark:border-cyan-500/30';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700';
    }
  };

  const handleCardClick = () => {
    if (isSelected) {
      setActiveDomainFilter('all');
    } else {
      setActiveDomainFilter(domain.id);
    }
    if (onSelect) onSelect(domain);
  };

  return (
    <div
      onClick={handleCardClick}
      className={`glass-panel p-5 cursor-pointer transition-all duration-300 relative group overflow-hidden ${
        isSelected
          ? 'border-cyan-500 dark:border-cyanGlow-500 shadow-md dark:shadow-glow-cyan bg-cyan-50/50 dark:bg-earth-850/90'
          : 'hover:border-slate-300 dark:hover:border-slate-700 hover:bg-slate-50/80 dark:hover:bg-earth-850/50'
      }`}
    >
      {/* Glow highlight line */}
      <div
        className={`absolute top-0 left-0 right-0 h-0.5 transition-all duration-300 ${
          isSelected ? 'bg-cyan-500 dark:bg-cyanGlow-500' : 'bg-transparent group-hover:bg-slate-300 dark:group-hover:bg-slate-700'
        }`}
      />

      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-earth-950 border border-slate-200 dark:border-slate-800 shadow-inner group-hover:border-slate-300 dark:group-hover:border-slate-700 transition-colors">
            {DOMAIN_ICONS[domain.iconName] || <Activity className="w-5 h-5 text-cyan-600 dark:text-cyanGlow-400" />}
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 group-hover:text-cyan-600 dark:group-hover:text-cyanGlow-400 transition-colors">
              {domain.name}
            </h4>
            <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">{domain.category}</span>
          </div>
        </div>

        <span
          className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getStatusBadge(
            domain.status
          )}`}
        >
          {domain.status}
        </span>
      </div>

      <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 mb-4 leading-relaxed">
        {domain.description}
      </p>

      <div className="pt-3 border-t border-slate-200 dark:border-slate-800/80 flex items-center justify-between">
        <div>
          <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-wider">{domain.keyIndicator}</div>
          <div className="text-sm font-bold text-slate-800 dark:text-slate-100 font-mono flex items-center gap-1.5 mt-0.5">
            <span>{domain.indicatorValue}</span>
            <span className={`text-[11px] font-normal flex items-center ${
              domain.changeRate.startsWith('-') ? 'text-amber-600 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400'
            }`}>
              {domain.changeRate.startsWith('-') ? <TrendingDown className="w-3 h-3" /> : <TrendingUp className="w-3 h-3" />}
              {domain.changeRate}
            </span>
          </div>
        </div>

        <div className="text-right">
          <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase tracking-wider">Regions</div>
          <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 font-mono">
            {domain.affectedRegionsCount} Zones
          </div>
        </div>
      </div>
    </div>
  );
};
