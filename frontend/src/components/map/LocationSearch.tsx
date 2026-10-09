import React, { useState, useRef, useEffect } from 'react';
import { Search, MapPin, ChevronRight, Compass } from 'lucide-react';
import { useClimateStore } from '../../store/useClimateStore';
import { LOCATIONS } from '../../data/mockData';
import { useLocations } from '../../hooks';
import { ClimateLocation } from '../../types';

interface LocationSearchProps {
  onSelectLocation?: (location: ClimateLocation) => void;
  className?: string;
}

export const LocationSearch: React.FC<LocationSearchProps> = ({
  onSelectLocation,
  className = '',
}) => {
  const { searchQuery, setSearchQuery, selectedLocation, setSelectedLocation } = useClimateStore();
  const { data: apiLocations } = useLocations();
  const locationsList = apiLocations && apiLocations.length > 0 ? apiLocations : LOCATIONS;

  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const filteredLocations = locationsList.filter(
    (loc) =>
      loc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      loc.region.toLowerCase().includes(searchQuery.toLowerCase()) ||
      loc.country.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (loc.dominantDomain || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (loc: ClimateLocation) => {
    setSelectedLocation(loc);
    setSearchQuery(loc.name);
    setIsOpen(false);
    if (onSelectLocation) {
      onSelectLocation(loc);
    }
  };

  return (
    <div ref={dropdownRef} className={`relative z-30 ${className}`}>
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-cyan-600 dark:text-cyanGlow-400 pointer-events-none" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder="Search location, region, landform, or biome..."
          className="w-full bg-white dark:bg-earth-950/90 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 pl-10 pr-10 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700/80 focus:border-cyan-500 dark:focus:border-cyanGlow-500 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 dark:focus:ring-cyanGlow-500/50 shadow-sm dark:shadow-inner backdrop-blur-md transition-all"
        />
        {selectedLocation && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          </div>
        )}
      </div>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 glass-panel border border-slate-200 dark:border-slate-700/80 max-h-72 overflow-y-auto z-50 shadow-2xl p-1.5 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="px-3 py-1.5 text-[10px] font-semibold text-slate-500 dark:text-slate-400 tracking-wider uppercase border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
            <span>Global Observation Locations ({filteredLocations.length})</span>
            <Compass className="w-3 h-3 text-cyan-600 dark:text-cyanGlow-400" />
          </div>
          {filteredLocations.length > 0 ? (
            filteredLocations.map((loc) => {
              const isSelected = selectedLocation.id === loc.id;
              return (
                <button
                  key={loc.id}
                  onClick={() => handleSelect(loc)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg text-xs flex items-center justify-between transition-colors my-0.5 ${
                    isSelected
                      ? 'bg-cyan-50 dark:bg-cyanGlow-500/10 text-cyan-700 dark:text-cyanGlow-400 border border-cyan-200 dark:border-cyanGlow-500/30 font-medium'
                      : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/80 hover:text-slate-900 dark:hover:text-slate-100'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <MapPin className={`w-4 h-4 shrink-0 ${isSelected ? 'text-cyan-600 dark:text-cyanGlow-400' : 'text-slate-400'}`} />
                    <div>
                      <div className="font-medium text-slate-800 dark:text-slate-100">{loc.name}</div>
                      <div className="text-[11px] text-slate-500 dark:text-slate-400">
                        {loc.region} • {loc.country}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 dark:bg-earth-950 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800 capitalize">
                      {loc.dominantDomain}
                    </span>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
                  </div>
                </button>
              );
            })
          ) : (
            <div className="p-4 text-center text-xs text-slate-500 dark:text-slate-400">
              No matching locations found for "{searchQuery}"
            </div>
          )}
        </div>
      )}
    </div>
  );
};
