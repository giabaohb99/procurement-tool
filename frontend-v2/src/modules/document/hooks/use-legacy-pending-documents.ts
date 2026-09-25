import { useQuery } from '@tanstack/react-query'

import { usePermission } from '@/core/authorization/use-permission'
import { queryKeys } from '@/shared/constants/query-keys'
import { legacyPendingApprovalApi } from '../api/legacy-pending-approval-api'

/**
 * Văn bản chờ DUYỆT MỘT BƯỚC mà tôi duyệt được (25/09/2026).
 *
 * Nguồn thứ ba của «Chờ tôi duyệt», bên cạnh việc của bộ máy duyệt: văn bản
 * không khớp luồng nào thì không sinh việc, trước đây người duyệt không thấy nó
 * ở màn này. Thiếu `document.approve` thì TẮT hẳn — đường API đòi quyền đó, cứ
 * gọi là ăn 403 ở mọi màn của phân hệ (huy hiệu menu dựng ở khắp nơi).
 */
export function useLegacyPendingDocuments() {
  const { can } = usePermission()
  const enabled = can('document', 'approve')
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.document.legacyPending,
    queryFn: legacyPendingApprovalApi.list,
    enabled,
  })
  return { items: enabled ? (data ?? []) : [], isLoading: enabled && isLoading }
}

/**
 * Lượt TÔI đã duyệt / trả lại theo đường một bước — nhóm «Đã duyệt» của màn
 * «Chờ tôi duyệt». Thiếu thì duyệt xong văn bản biến mất khỏi màn, như chưa ký
 * gì (25/09/2026). Cùng chốt quyền với danh sách chờ.
 */
export function useLegacyDecisions(days: number) {
  const { can } = usePermission()
  const enabled = can('document', 'approve')
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.document.legacyDecisions(days),
    queryFn: () => legacyPendingApprovalApi.decisions(days),
    enabled,
  })
  return { items: enabled ? (data ?? []) : [], isLoading: enabled && isLoading }
}
