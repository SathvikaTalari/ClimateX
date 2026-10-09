import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  searchSatelliteScenes,
  ingestSatelliteScene,
  fetchIngestionStatus,
  fetchSceneFootprint,
  fetchScenesByLocation,
} from '../lib/api';
import { SceneSearchParams, SceneIngestionRequest, EOScene } from '../types';

/**
 * Mutation for searching live satellite scenes across EO providers.
 */
export function useEOSearchMutation() {
  return useMutation<EOScene[], Error, SceneSearchParams>({
    mutationFn: (params: SceneSearchParams) => searchSatelliteScenes(params),
  });
}

/**
 * Mutation for starting controlled scene ingestion.
 */
export function useIngestSceneMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (req: SceneIngestionRequest) => ingestSatelliteScene(req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['satellite-scenes'] });
    },
  });
}

/**
 * Hook for polling ingestion status of a specific scene.
 */
export function useIngestionStatus(sceneIdentifier: string | number, enabled: boolean = true) {
  return useQuery({
    queryKey: ['ingestion-status', sceneIdentifier],
    queryFn: () => fetchIngestionStatus(sceneIdentifier),
    enabled: enabled && !!sceneIdentifier,
    refetchInterval: (query) => {
      const status = query.state.data?.ingestion_status;
      if (status === 'pending' || status === 'processing') {
        return 3000; // Poll every 3 seconds while processing
      }
      return false; // Stop polling when completed or failed
    },
  });
}

/**
 * Hook to fetch scenes for a location coordinate or ID.
 */
export function useScenesByLocation(locationId?: string, lat?: number, lon?: number) {
  return useQuery({
    queryKey: ['satellite-scenes-location', locationId, lat, lon],
    queryFn: () => fetchScenesByLocation(locationId, lat, lon),
    enabled: !!(locationId || (lat !== undefined && lon !== undefined)),
  });
}

/**
 * Hook to fetch GeoJSON footprint for a scene.
 */
export function useSceneFootprint(sceneIdentifier?: string | number) {
  return useQuery({
    queryKey: ['scene-footprint', sceneIdentifier],
    queryFn: () => fetchSceneFootprint(sceneIdentifier!),
    enabled: !!sceneIdentifier,
  });
}
