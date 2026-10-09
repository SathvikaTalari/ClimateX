import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  processScene,
  fetchProcessingStatus,
  fetchLocationSpatialFeatures,
  fetchProcessedImageHistogram,
  getCompositeUrl,
  getSpatialFeaturesExportUrl,
} from '../lib/api';
import {
  ProcessingRequest,
  ProcessedImageOut,
  SpatialFeatureOut,
  HistogramData,
  CompositeMode,
} from '../types';

/** Trigger index processing (NDVI / NDWI / NDBI / LST) for a scene. */
export function useProcessSceneMutation() {
  const queryClient = useQueryClient();
  return useMutation<ProcessedImageOut, Error, { sceneIdentifier: string | number; req: ProcessingRequest }>({
    mutationFn: ({ sceneIdentifier, req }) => processScene(sceneIdentifier, req),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['processing-status'] });
      queryClient.invalidateQueries({ queryKey: ['spatial-features'] });
      if (data.id) {
        queryClient.invalidateQueries({ queryKey: ['histogram', data.id] });
      }
    },
  });
}

/** Poll processing status for a scene. */
export function useProcessingStatus(sceneIdentifier?: string | number) {
  return useQuery<ProcessedImageOut[], Error>({
    queryKey: ['processing-status', sceneIdentifier],
    queryFn: () => fetchProcessingStatus(sceneIdentifier!),
    enabled: !!sceneIdentifier,
  });
}

/** Fetch all zonal statistics for a location (optionally filtered by index). */
export function useLocationSpatialFeatures(locationId?: string, indexName?: string) {
  return useQuery<SpatialFeatureOut[], Error>({
    queryKey: ['spatial-features', locationId, indexName],
    queryFn: () => fetchLocationSpatialFeatures(locationId!, indexName),
    enabled: !!locationId,
    refetchOnWindowFocus: true,
  });
}

/** Fetch 32-bin pixel value histogram for a processed image. */
export function useProcessedImageHistogram(imageId?: number, nBins: number = 32) {
  return useQuery<HistogramData, Error>({
    queryKey: ['histogram', imageId, nBins],
    queryFn: () => fetchProcessedImageHistogram(imageId!, nBins),
    enabled: !!imageId,
    staleTime: 60_000,
  });
}

/** Returns a composite image URL (no fetching — used as <img src> directly). */
export function useCompositeUrl(
  sceneIdentifier?: string | number,
  mode: CompositeMode = 'RGB',
  locationId?: string
): string | null {
  if (!sceneIdentifier) return null;
  return getCompositeUrl(sceneIdentifier, mode, locationId);
}

/** Returns download URLs for GeoJSON or CSV export. */
export function useSpatialFeatureExportUrls(locationId?: string, indexName?: string) {
  if (!locationId) return { geojsonUrl: null, csvUrl: null };
  return {
    geojsonUrl: getSpatialFeaturesExportUrl(locationId, 'geojson', indexName),
    csvUrl:     getSpatialFeaturesExportUrl(locationId, 'csv',     indexName),
  };
}
