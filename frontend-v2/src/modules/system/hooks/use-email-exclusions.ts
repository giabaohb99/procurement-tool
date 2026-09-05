import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { emailExclusionApi } from '../api/email-exclusion-api'
import type { ExclusionScope } from '../types/email-exclusion'

export function useEmailExclusions() {
  return useQuery({
    queryKey: queryKeys.system.emailExclusions(),
    queryFn: () => emailExclusionApi.list(),
  })
}

export function useAddEmailExclusion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { scope: ExclusionScope; ref_id: number; label: string; event: string }) =>
      emailExclusionApi.add(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.system.emailExclusions() }),
  })
}

export function useRemoveEmailExclusion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => emailExclusionApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.system.emailExclusions() }),
  })
}
