import { useQuery } from '@tanstack/react-query';
import { fetchObservations, ObservationsFilter, ObservationItem } from '../lib/api';

export function useObservations(filter?: ObservationsFilter) {
  return useQuery<ObservationItem[]>({
    queryKey: ['observations', filter],
    queryFn: () => fetchObservations(filter),
  });
}
