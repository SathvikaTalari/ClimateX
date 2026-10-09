'use client';

import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { useClimateStore } from '../../store/useClimateStore';
import { LOCATIONS } from '../../data/mockData';
import { useLocations } from '../../hooks';
import { Layers, Maximize2, Minimize2, MapPin, Eye } from 'lucide-react';
import { ClimateLocation } from '../../types';

export interface ActiveFootprint {
  bbox?: [number, number, number, number];
  footprint_geojson?: any;
  scene_id?: string;
  thumbnail_url?: string;
  satellite?: string;
  sensor?: string;
  cloud_cover?: number;
}

interface MapLibreMapProps {
  height?: string;
  className?: string;
  showControls?: boolean;
  interactive?: boolean;
  onLocationSelect?: (location: ClimateLocation) => void;
  activeFootprint?: ActiveFootprint | null;
}

export const MapLibreMap: React.FC<MapLibreMapProps> = ({
  height = '650px',
  className = '',
  showControls = true,
  interactive = true,
  onLocationSelect,
  activeFootprint,
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<{ [key: string]: maplibregl.Marker }>({});
  const popupRef = useRef<maplibregl.Popup | null>(null);

  const { selectedLocation, setSelectedLocation, theme } = useClimateStore();
  const { data: apiLocations } = useLocations();
  const locationsList = apiLocations && apiLocations.length > 0 ? apiLocations : LOCATIONS;

  const [activeLayer, setActiveLayer] = useState<'base' | 'satellite'>('base');
  const [isFullScreen, setIsFullScreen] = useState(false);

  // Map Tile Style URLs (Free Carto / OpenStreetMap without API keys)
  const mapStyles = {
    dark: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
    light: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
    satellite: {
      version: 8,
      sources: {
        'imagery': {
          type: 'raster',
          tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
          tileSize: 256,
          attribution: 'Esri World Imagery',
        },
      },
      layers: [
        {
          id: 'imagery-layer',
          type: 'raster',
          source: 'imagery',
          minzoom: 0,
          maxzoom: 18,
        },
      ],
    },
  };

  const currentBaseStyle = theme === 'dark' ? mapStyles.dark : mapStyles.light;

  const createMarkerElement = (loc: ClimateLocation, isSelected: boolean) => {
    const el = document.createElement('div');
    el.className = 'custom-map-marker group relative cursor-pointer';

    el.innerHTML = `
      <div class="relative">
        <div class="w-8 h-8 rounded-full ${
          isSelected 
            ? 'bg-cyan-500 ring-4 ring-cyan-500/40 shadow-glow-cyan' 
            : 'bg-white dark:bg-earth-900 border-2 border-slate-300 dark:border-slate-700 shadow-md'
        } flex items-center justify-center text-slate-100 transition-all duration-300 hover:scale-125">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="${
            isSelected ? '#0b0f19' : '#0284c7'
          }" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
            <circle cx="12" cy="10" r="3"/>
          </svg>
        </div>
        <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-white/95 dark:bg-earth-950/90 text-[10px] text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-800 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap shadow-lg z-20">
          ${loc.name}
        </div>
      </div>
    `;
    return el;
  };

  const addMarkers = (map: maplibregl.Map, locations: ClimateLocation[]) => {
    Object.values(markersRef.current).forEach((m) => m.remove());
    markersRef.current = {};

    locations.forEach((loc) => {
      const isSelected = selectedLocation.id === loc.id;
      const el = createMarkerElement(loc, isSelected);

      el.addEventListener('click', () => {
        setSelectedLocation(loc);
        if (onLocationSelect) onLocationSelect(loc);
      });

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([loc.coordinates[1], loc.coordinates[0]])
        .addTo(map);

      markersRef.current[loc.id] = marker;
    });
  };

  const updateFootprintLayer = (map: maplibregl.Map, footprint: ActiveFootprint | null | undefined) => {
    // Remove existing footprint layers/sources if present
    if (map.getLayer('scene-raster-layer')) map.removeLayer('scene-raster-layer');
    if (map.getSource('scene-raster-source')) map.removeSource('scene-raster-source');
    if (map.getLayer('scene-footprint-fill')) map.removeLayer('scene-footprint-fill');
    if (map.getLayer('scene-footprint-line')) map.removeLayer('scene-footprint-line');
    if (map.getSource('scene-footprint')) map.removeSource('scene-footprint');

    if (!footprint) {
      if (popupRef.current) {
        popupRef.current.remove();
        popupRef.current = null;
      }
      return;
    }

    // 1. If real satellite scene thumbnail URL and bounding box exist, drape the image directly onto the map!
    if (footprint.thumbnail_url && footprint.bbox) {
      const [minLon, minLat, maxLon, maxLat] = footprint.bbox;
      try {
        map.addSource('scene-raster-source', {
          type: 'image',
          url: footprint.thumbnail_url,
          coordinates: [
            [minLon, maxLat], // top-left
            [maxLon, maxLat], // top-right
            [maxLon, minLat], // bottom-right
            [minLon, minLat], // bottom-left
          ],
        });

        map.addLayer({
          id: 'scene-raster-layer',
          type: 'raster',
          source: 'scene-raster-source',
          paint: {
            'raster-opacity': 0.85,
            'raster-fade-duration': 300,
          },
        });
      } catch (e) {
        console.warn('Could not overlay satellite raster thumbnail:', e);
      }
    }

    let geojson = footprint.footprint_geojson;
    if (!geojson && footprint.bbox) {
      const [minLon, minLat, maxLon, maxLat] = footprint.bbox;
      geojson = {
        type: 'Polygon',
        coordinates: [
          [
            [minLon, minLat],
            [maxLon, minLat],
            [maxLon, maxLat],
            [minLon, maxLat],
            [minLon, minLat],
          ],
        ],
      };
    }

    if (!geojson) return;

    const sceneId = footprint.scene_id || 'Satellite Scene';

    const featureGeoJSON: any = {
      type: 'Feature',
      geometry: geojson,
      properties: { scene_id: sceneId },
    };

    map.addSource('scene-footprint', {
      type: 'geojson',
      data: featureGeoJSON,
    });

    map.addLayer({
      id: 'scene-footprint-fill',
      type: 'fill',
      source: 'scene-footprint',
      paint: {
        'fill-color': '#06b6d4',
        'fill-opacity': footprint.thumbnail_url ? 0.1 : 0.25,
      },
    });

    map.addLayer({
      id: 'scene-footprint-line',
      type: 'line',
      source: 'scene-footprint',
      paint: {
        'line-color': '#0891b2',
        'line-width': 2,
        'line-dasharray': [2, 2],
      },
    });

    // Fit map to footprint bounding box if available and display on-map popup badge
    if (footprint.bbox) {
      const [minLon, minLat, maxLon, maxLat] = footprint.bbox;
      const centerLon = (minLon + maxLon) / 2;
      const centerLat = (minLat + maxLat) / 2;

      // Extract MGRS Tile Code if present in scene_id (e.g. T43SGS or T43SFS)
      const tileMatch = sceneId.match(/_T([0-9A-Z]{5})_/);
      const tileCode = tileMatch ? `Tile ${tileMatch[1]}` : 'Grid Frame';

      const satStr = footprint.satellite || 'Sentinel-2';
      const sensorStr = footprint.sensor ? ` (${footprint.sensor})` : '';
      const cloudStr =
        footprint.cloud_cover !== undefined && footprint.cloud_cover !== null
          ? ` | Cloud: ${footprint.cloud_cover.toFixed(1)}%`
          : '';

      const popupHtml = `
        <div style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 11px; padding: 8px 12px; background: #090d16; color: #f8fafc; border-radius: 10px; border: 1px solid #06b6d4; box-shadow: 0 4px 20px rgba(6, 182, 212, 0.25);">
          <div style="font-weight: bold; color: #22d3ee; margin-bottom: 3px; font-size: 12px; display: flex; align-items: center; gap: 4px;">
            <span>🛰️</span> <span>MGRS ${tileCode}</span>
          </div>
          <div style="color: #94a3b8; font-size: 10px; margin-bottom: 4px; word-break: break-all;" title="${sceneId}">
            ${sceneId.length > 28 ? sceneId.slice(0, 28) + '...' : sceneId}
          </div>
          <div style="color: #34d399; font-size: 10px;">
            Longitudes: ${minLon.toFixed(3)}° to ${maxLon.toFixed(3)}° E
          </div>
          <div style="color: #34d399; font-size: 10px;">
            Latitudes: ${minLat.toFixed(3)}° to ${maxLat.toFixed(3)}° N
          </div>
          <div style="color: #fbbf24; font-size: 10px; margin-top: 3px;">
            Sensor: ${satStr}${sensorStr}${cloudStr}
          </div>
        </div>
      `;

      if (popupRef.current) {
        popupRef.current.remove();
      }

      popupRef.current = new maplibregl.Popup({
        closeButton: false,
        closeOnClick: false,
        offset: 10,
        className: 'footprint-popup',
      })
        .setLngLat([centerLon, centerLat])
        .setHTML(popupHtml)
        .addTo(map);

      map.fitBounds(
        [
          [minLon, minLat],
          [maxLon, maxLat],
        ],
        { padding: 60, maxZoom: 10 }
      );
    }
  };

  useEffect(() => {
    if (!mapContainer.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: currentBaseStyle,
      center: [selectedLocation.coordinates[1], selectedLocation.coordinates[0]],
      zoom: selectedLocation.zoom,
      attributionControl: false,
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'bottom-right');
    mapRef.current = map;

    map.on('load', () => {
      addMarkers(map, locationsList);
      updateFootprintLayer(map, activeFootprint);
      map.resize();
    });

    const resizeObserver = new ResizeObserver(() => {
      if (mapRef.current) {
        mapRef.current.resize();
      }
    });

    resizeObserver.observe(mapContainer.current);

    return () => {
      resizeObserver.disconnect();
      map.remove();
    };
  }, []);

  useEffect(() => {
    if (mapRef.current) {
      addMarkers(mapRef.current, locationsList);
    }
  }, [locationsList]);

  useEffect(() => {
    if (!mapRef.current) return;
    if (activeLayer === 'base') {
      mapRef.current.setStyle(currentBaseStyle);
      mapRef.current.once('style.load', () => {
        if (mapRef.current) {
          addMarkers(mapRef.current, locationsList);
          updateFootprintLayer(mapRef.current, activeFootprint);
        }
      });
    }
  }, [theme]);

  useEffect(() => {
    if (!mapRef.current) return;
    mapRef.current.flyTo({
      center: [selectedLocation.coordinates[1], selectedLocation.coordinates[0]],
      zoom: Math.max(selectedLocation.zoom, 4),
      speed: 1.2,
      curve: 1.4,
    });
    addMarkers(mapRef.current, locationsList);
  }, [selectedLocation]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const renderFootprint = () => {
      if (activeFootprint) {
        if (activeLayer !== 'satellite') {
          setActiveLayer('satellite');
          map.setStyle(mapStyles.satellite as any);
          map.once('style.load', () => {
            addMarkers(map, locationsList);
            updateFootprintLayer(map, activeFootprint);
          });
          return;
        }
      }
      updateFootprintLayer(map, activeFootprint);
      if (activeFootprint && mapContainer.current) {
        mapContainer.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    };

    if (map.isStyleLoaded()) {
      renderFootprint();
    } else {
      map.once('style.load', renderFootprint);
    }
  }, [activeFootprint]);

  const handleLayerChange = (styleKey: 'base' | 'satellite') => {
    setActiveLayer(styleKey);
    if (!mapRef.current) return;

    if (styleKey === 'satellite') {
      mapRef.current.setStyle(mapStyles.satellite as any);
    } else {
      mapRef.current.setStyle(currentBaseStyle);
    }
    mapRef.current.once('style.load', () => {
      if (mapRef.current) {
        addMarkers(mapRef.current, locationsList);
        updateFootprintLayer(mapRef.current, activeFootprint);
      }
    });
  };

  return (
    <div
      className={`relative w-full rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-800 shadow-xl dark:shadow-2xl glass-panel ${className} ${
        isFullScreen ? 'fixed inset-4 z-50 h-[calc(100vh-2rem)]' : ''
      }`}
      style={{ height: isFullScreen ? 'calc(100vh - 2rem)' : height }}
    >
      <div ref={mapContainer} className="w-full h-full min-h-[400px]" />

      <div className="absolute top-4 left-4 z-10 glass-panel px-4 py-2.5 border border-slate-200 dark:border-slate-700/80 max-w-sm flex items-center justify-between gap-3 shadow-lg dark:shadow-xl backdrop-blur-md">
        <div className="flex items-center gap-2.5">
          <div className="w-3 h-3 rounded-full bg-cyan-500 dark:bg-cyanGlow-500 animate-ping" />
          <div>
            <div className="text-xs font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
              <span>{selectedLocation.name}</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-100 dark:bg-cyanGlow-500/20 text-cyan-700 dark:text-cyanGlow-400 border border-cyan-200 dark:border-cyanGlow-500/30">
                {selectedLocation.dominantDomain}
              </span>
            </div>
            <div className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
              Lat: {selectedLocation.coordinates[0]}° N | Lng: {selectedLocation.coordinates[1]}° W
            </div>
          </div>
        </div>
      </div>

      {showControls && (
        <div className="absolute top-4 right-4 z-10 flex flex-col gap-2">
          <div className="glass-panel p-1 border border-slate-200 dark:border-slate-700/80 flex items-center gap-1 shadow-lg">
            <button
              onClick={() => handleLayerChange('base')}
              className={`px-2.5 py-1 text-[11px] font-medium rounded-lg transition-colors flex items-center gap-1 ${
                activeLayer === 'base'
                  ? 'bg-cyan-100 dark:bg-cyanGlow-500/20 text-cyan-700 dark:text-cyanGlow-400 border border-cyan-300 dark:border-cyanGlow-500/40'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <Eye className="w-3 h-3" />
              <span>{theme === 'dark' ? 'Dark Terrain' : 'Light Terrain'}</span>
            </button>
            <button
              onClick={() => handleLayerChange('satellite')}
              className={`px-2.5 py-1 text-[11px] font-medium rounded-lg transition-colors flex items-center gap-1 ${
                activeLayer === 'satellite'
                  ? 'bg-cyan-100 dark:bg-cyanGlow-500/20 text-cyan-700 dark:text-cyanGlow-400 border border-cyan-300 dark:border-cyanGlow-500/40'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <Layers className="w-3 h-3" /> Satellite RGB
            </button>
          </div>

          <button
            onClick={() => setIsFullScreen(!isFullScreen)}
            className="self-end p-2 glass-panel border border-slate-200 dark:border-slate-700/80 text-slate-700 dark:text-slate-300 hover:text-cyan-600 dark:hover:text-cyanGlow-400 rounded-lg transition-colors shadow-lg"
            title="Toggle Fullscreen Map"
          >
            {isFullScreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>
      )}

      <div className="absolute bottom-4 left-4 z-10 glass-panel px-3 py-2 border border-slate-200 dark:border-slate-800 text-[10px] text-slate-600 dark:text-slate-400 flex items-center gap-4 shadow-lg backdrop-blur-md">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-cyan-500 dark:bg-cyanGlow-400" />
          <span>Active Sensor Node</span>
        </div>
        {activeFootprint && (
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 border border-cyan-500 bg-cyan-500/30" />
            <span className="font-semibold text-cyan-600 dark:text-cyanGlow-400">Scene Footprint Swath</span>
          </div>
        )}
      </div>
    </div>
  );
};
