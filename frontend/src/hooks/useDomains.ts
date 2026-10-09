import { useQuery } from '@tanstack/react-query';
import { fetchDomains, fetchDomain } from '../lib/api';
import { EnvironmentalDomain } from '../types';

export function useDomains() {
  return useQuery<EnvironmentalDomain[]>({
    queryKey: ['domains'],
    queryFn: fetchDomains,
  });
}

export function useDomain(id: string) {
  return useQuery<EnvironmentalDomain | undefined>({
    queryKey: ['domain', id],
    queryFn: () => fetchDomain(id),
    enabled: !!id,
  });
}
