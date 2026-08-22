import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useMemo } from 'react'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import {
  externalPartyApi,
  securityLevelApi,
  type DocumentPartnerInput,
  type SecurityLevelCreateInput,
  type SecurityLevelUpdateInput,
} from '../api/doc-catalog-api'
import { securityLevelLabel } from '../helpers/security-level-label'
import {
  FALLBACK_CONFIDENTIAL_LEVELS,
  FALLBACK_URGENCY_LEVELS,
  SECURITY_LEVEL_KIND_CONFIDENTIAL,
  type SecurityLevel,
  type SecurityLevelKind,
} from '../types/security-level'

/**
 * Ba danh mục phụ của phân hệ Văn thư.
 */

// ===== Mức mật / độ khẩn =====

/** Cả bảy dòng (còn dùng lẫn đã ngừng) — dùng cho màn danh mục CRUD. */
export function useSecurityLevels() {
  const query = useQuery({
    queryKey: queryKeys.document.securityLevels(),
    queryFn: () => securityLevelApi.list(),
  })

  const items = useMemo(() => {
    const rows = query.data?.items ?? []
    // Sắp theo thang rồi theo bậc — cùng thứ tự người xem quen từ bản khai cứng cũ.
    return [...rows].sort((a, b) => a.kind - b.kind || a.value - b.value)
  }, [query.data])

  return { ...query, items }
}

/** Các bậc ĐANG DÙNG của MỘT thang, xếp theo bậc tăng dần — dùng cho ô chọn. */
export function useSecurityLevelOptions(kind: SecurityLevelKind): SecurityLevel[] {
  const { items, isLoading } = useSecurityLevels()

  return useMemo(() => {
    const active = items.filter((item) => item.kind === kind && item.is_active)
    // Chưa nạp xong lần đầu (chưa có dòng nào): dùng bản dự phòng để ô chọn
    // không trống trơn trong lúc chờ API.
    if (isLoading && active.length === 0) {
      return kind === SECURITY_LEVEL_KIND_CONFIDENTIAL
        ? FALLBACK_CONFIDENTIAL_LEVELS
        : FALLBACK_URGENCY_LEVELS
    }
    return active
  }, [items, isLoading, kind])
}

export function useSecurityLevel(id?: number) {
  return useQuery({
    queryKey: queryKeys.document.securityLevel(id ?? 0),
    queryFn: () => securityLevelApi.getById(id as number),
    enabled: typeof id === 'number' && id > 0,
  })
}

/**
 * Tra NHÃN theo `(kind, value)` — dùng ở cột bảng / ô chỉ xem trên văn bản.
 * Số lạ (dữ liệu cũ, dòng đã bị xóa) thì trả về chính con số đó, giống hàm
 * thuần `secrecyLabel`/`urgencyLabel` bản cũ.
 */
export function useSecurityLevelLabel(): (kind: SecurityLevelKind, value: number) => string {
  const { items } = useSecurityLevels()

  //  Logic tra nằm ở hàm thuần `securityLevelLabel` (có test) — hook chỉ bơm
  //  dữ liệu vào. Viết lại phép tìm ở đây là hai bản logic sớm muộn lệch nhau,
  //  mà lệch chỗ này thì văn bản mức Mật hiện ra tên của một mức khác.
  return useCallback(
    (kind: SecurityLevelKind, value: number) => securityLevelLabel(items, kind, value),
    [items],
  )
}

export function useSaveSecurityLevel() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (
      input:
        | { id?: undefined; values: SecurityLevelCreateInput }
        | { id: number; values: SecurityLevelUpdateInput },
    ) =>
      input.id !== undefined
        ? securityLevelApi.update(input.id, input.values)
        : securityLevelApi.create(input.values),

    onSuccess: (_data, variables) => {
      toast.success(variables.id !== undefined ? 'Đã cập nhật bậc' : 'Đã thêm bậc')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    },
  })
}

export function useDeleteSecurityLevel() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => securityLevelApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa bậc')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    },
    // Không toast riêng khi lỗi: interceptor của httpClient đã tự hiện đúng câu
    // tiếng Việt backend trả về (vd "đang có văn bản dùng bậc này") — xem
    // `core/api/http-client.ts`.
  })
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
