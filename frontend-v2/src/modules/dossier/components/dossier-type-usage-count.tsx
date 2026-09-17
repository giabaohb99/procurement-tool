import { usePermission } from '@/core/authorization/use-permission'
import { Skeleton } from '@/shared/ui/skeleton'
import { useDossierTypeStats } from '../hooks/use-dossier-type-stats'

/**
 * Ô «Hồ sơ đang dùng» của bảng danh mục Loại hồ sơ.
 *
 * ⚠️ **Hook gọi trong TỪNG Ô, và đó không phải N+1.** TanStack Query gom theo
 * khóa: mọi ô dùng chung `['dossier','dossier-types','stats']` nên cả bảng chỉ
 * bắn **một** lượt mạng, còn lại đọc từ bộ nhớ đệm. Cách này giữ được khai báo
 * CRUD ở dạng hằng tĩnh — đổi nó thành hàm dựng (như bên `dossier-crud.tsx`)
 * chỉ để chuyền xuống một con số thì phải sửa cả hai trang gọi tới.
 *
 * ⚠️ **Thiếu quyền `dossier.read` thì TẮT HẲN cột, không hiện `0`.** Backend
 * không ném 403 ở endpoint này — `apply_scope` chặn hết và trả rỗng — nên vẽ
 * `0` là nói với người dùng rằng chưa hồ sơ nào dùng loại này, trong khi sự
 * thật là họ không được phép đếm. Đúng bài học duoc-CR-322.
 *
 * ⚠️ Con số này **lọc theo phạm vi dữ liệu** của người đang xem, nên nó có thể
 * NHỎ HƠN con số trong câu chặn xóa (chốt toàn vẹn đếm toàn công ty). Hai luật
 * ngược nhau là cố ý; câu chặn đã nói rõ «trên toàn công ty» để hai số lệch
 * nhau không bị đọc thành lỗi.
 */
export function DossierTypeUsageCount({ typeId }: { typeId: number }) {
  const { can } = usePermission()
  const canCount = can('dossier', 'read')
  const { data, isLoading } = useDossierTypeStats(canCount)

  if (!canCount) return <span className="text-muted-foreground">—</span>
  if (isLoading) return <Skeleton className="h-4 w-8" />

  const total = data?.get(typeId) ?? 0
  return total > 0 ? (
    <span className="font-medium">{total}</span>
  ) : (
    <span className="text-muted-foreground">0</span>
  )
}
