import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchIngestedScenesForML,
  submitChangeDetection,
  fetchMLJob,
} from '../lib/api';
import {
  ChangeDetectionRequest,
  MLJobOut,
  IngestedSceneForML,
} from '../types';

/** Fetch scenes with completed Phase 5A processing for a location (change-detection inputs). */
export function useIngestedScenesForML(locationId?: string) {
  return useQuery<IngestedSceneForML[], Error>({
    queryKey: ['ml-ingested-scenes', locationId],
    queryFn: () => fetchIngestedScenesForML(locationId!),
    enabled: !!locationId,
    staleTime: 30_000,
  });
}

/** Submit a change-detection job. */
export function useSubmitChangeDetection() {
  const queryClient = useQueryClient();
  return useMutation<{ job_id: string; status: string }, Error, ChangeDetectionRequest>({
    mutationFn: submitChangeDetection,
    onSuccess: () => {
      // Invalidate job list so a refetch picks up the new job
      queryClient.invalidateQueries({ queryKey: ['ml-job'] });
    },
  });
}

/**
 * Poll a job's status.  Refetches every 3 seconds while running/pending.
 * Stops polling automatically when completed or failed.
 */
export function useMLJob(jobId?: string) {
  return useQuery<MLJobOut, Error>({
    queryKey: ['ml-job', jobId],
    queryFn: () => fetchMLJob(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (!status || status === 'completed' || status === 'failed') return false;
      return 3000; // poll every 3 s while pending/running
    },
    staleTime: 0,
  });
}
