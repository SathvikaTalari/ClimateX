import { useQuery } from '@tanstack/react-query';
import { fetchLocations, fetchLocation, LocationsFilter } from '../lib/api';
import { ClimateLocation } from '../types';

export function useLocations(filter?: LocationsFilter) {
  return useQuery<ClimateLocation[]>({
    queryKey: ['locations', filter],
    queryFn: () => fetchLocations(filter),
  });
}

export function useLocation(id: string) {
  return useQuery<ClimateLocation | undefined>({
    queryKey: ['location', id],
    queryFn: () => fetchLocation(id),
    enabled: !!id,
  });
}
