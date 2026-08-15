import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo } from 'react'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { externalPartyApi, type DocumentPartnerInput } from '../api/doc-catalog-api'
import {
  CONFIDENTIAL_LEVELS,
  URGENCY_LEVELS,
  type SecurityLevel,
  type SecurityLevelKind,
} from '../types/security-level'

/**
 * Hai danh mục phụ của phân hệ Văn thư.
 *
 * **Mức mật / độ khẩn không gọi API** — đó là thang cố định khai trong mã
 * (`types/security-level.ts`), lý do ghi ở đầu tệp đó.
 */

// ===== Mức mật / độ khẩn =====

export function useSecurityLevels(): SecurityLevel[] {
  return useMemo(() => [...CONFIDENTIAL_LEVELS, ...URGENCY_LEVELS], [])
}

/** Các mức của MỘT thang, xếp theo thứ bậc tăng dần. */
export function useSecurityLevelOptions(kind: SecurityLevelKind): SecurityLevel[] {
  return useMemo(
    () => (kind === 'confidential' ? CONFIDENTIAL_LEVELS : URGENCY_LEVELS),
    [kind],
  )
}

// ===== Đơn vị gửi nhận bên ngoài =====

export function useDocumentPartners() {
  const query = useQuery({
    queryKey: queryKeys.document.externalParties(),
    queryFn: () => externalPartyApi.list(),
  })

  const items = useMemo(() => query.data?.items ?? [], [query.data])
  return { ...query, items }
}

export function useActiveDocumentPartners() {
  const { items } = useDocumentPartners()
  return useMemo(() => items.filter((item) => item.is_active), [items])
}

export function useDocumentPartner(id?: number) {
  return useQuery({
    queryKey: queryKeys.document.externalParty(id ?? 0),
    queryFn: () => externalPartyApi.getById(id as number),
    enabled: typeof id === 'number' && id > 0,
  })
}

export function useSaveDocumentPartner() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, values }: { id?: number; values: DocumentPartnerInput }) =>
      id ? externalPartyApi.update(id, values) : externalPartyApi.create(values),

    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã cập nhật đơn vị' : 'Đã thêm đơn vị')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    },
  })
}

export function useDeleteDocumentPartner() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => externalPartyApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa đơn vị')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    },
  })
}
