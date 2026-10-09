import { useQuery } from '@tanstack/react-query';
import { fetchSatelliteScenes, SatelliteScenesFilter, SatelliteSceneItem } from '../lib/api';

export function useSatelliteScenes(filter?: SatelliteScenesFilter) {
  return useQuery<SatelliteSceneItem[]>({
    queryKey: ['satellite-scenes', filter],
    queryFn: () => fetchSatelliteScenes(filter),
  });
}
