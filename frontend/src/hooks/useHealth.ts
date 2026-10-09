import { useQuery } from '@tanstack/react-query';
import { fetchHealth, HealthResponse } from '../lib/api';

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 30000, // check health every 30s
  });
}
