import { useQuery } from '@tanstack/react-query'

import { apiGet } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { queryKeys } from '@/shared/constants/query-keys'
import type {
  ApplicableDossiersResult,
  DocKind,
} from '../types/dossier-applicability'

/**
 * Hồ sơ phải kèm theo một chứng từ — nguồn của thẻ «Hồ sơ cần kèm».
 *
 * ⚠️ **Tự tắt khi thiếu `dossier.read`.** Thẻ này mọc ra ở màn của phân hệ KHÁC
 * (Thu mua, Khảo sát), nơi phần lớn người dùng không có khóa của phân hệ Hồ sơ.
 * Không có nhánh tắt thì cứ mở một đơn mua hàng là ăn một toast 403 — đúng lỗi
 * đã phải vá ở tab «Công nợ & Đánh giá» của màn Nhà cung cấp (CR-106).
 *
 * ⚠️ `docId` chưa có (trang THÊM MỚI, hoặc `useParams` trả `undefined`) thì cũng
 * không gọi: chứng từ chưa tồn tại thì không có dòng hàng nào để mà khớp.
 */
export function useApplicableDossiers(docKind: DocKind, docId: number | undefined) {
  const { can } = usePermission()
  const allowed = can('dossier', 'read')

  return useQuery({
    queryKey: queryKeys.dossier.applicable(docKind, docId ?? 0),
    queryFn: () =>
      apiGet<ApplicableDossiersResult>(
        `/api/dossiers/applicable?doc_kind=${docKind}&doc_id=${docId}`,
      ),
    enabled: allowed && Boolean(docId),
  })
}
