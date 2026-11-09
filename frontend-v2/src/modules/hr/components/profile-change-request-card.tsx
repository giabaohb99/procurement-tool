import { ChevronRight } from 'lucide-react'

import { formatDateTime } from '@/shared/utils/format-date'
import type { EmployeeChangeRequest } from '../types/employee-change-request'
import { countChangedFields, listChangedGroups } from '../utils/employee-change-request-review'
import { EmployeeChangeRequestStatusBadge } from './employee-change-request-status-badge'

/**
 * Một đề nghị sửa hồ sơ ở khổ điện thoại (màn "Duyệt sửa hồ sơ") — xem `DataTableProps.mobileCard`.
 *
 * ⚠️ **Tên người lên đầu, mã NV tụt xuống dòng phụ.** Người duyệt nhận ra đề nghị bằng tên đồng
 * nghiệp; mã chỉ để phân biệt hai người trùng tên, nên đứng ngay dưới (màu sky như mọi thẻ khác).
 *
 * ⚠️ **Ruột thẻ toàn `<span>`.** Bảng có `onRowClick` nên `DataTableMobileCards` bọc cả thẻ trong
 * một `<button>` — `<button>` chỉ nhận nội dung chữ, và trong thẻ KHÔNG có nút nào khác (lồng nút
 * vào nút là HTML sai, hai vùng chạm đè nhau). Duyệt / từ chối làm ở màn chi tiết như khổ rộng.
 *
 * Huy hiệu trạng thái LUÔN hiện, không tắt khi "Chờ duyệt": bộ lọc trạng thái đổi được sang
 * "Tất cả", lúc đó trạng thái là thứ phân loại danh sách — đúng như cột Trạng thái của bảng.
 */
export function ProfileChangeRequestCard({ request }: { request: EmployeeChangeRequest }) {
  const groups = listChangedGroups(request)
  const fieldCount = countChangedFields(request)

  return (
    <span className="flex items-start gap-2">
      <span className="min-w-0 flex-1 space-y-1">
        <span className="flex items-start justify-between gap-2">
          <span className="min-w-0 truncate font-medium text-foreground">
            {request.employee_name || `#${request.employee_id}`}
          </span>
          <span className="shrink-0">
            <EmployeeChangeRequestStatusBadge status={request.status} />
          </span>
        </span>

        <span className="block truncate font-mono text-xs text-sky-600 dark:text-sky-400">
          {request.employee_code}
        </span>

        {groups.length > 0 && (
          <span className="block text-sm break-words text-muted-foreground">
            {groups.join(', ')}
          </span>
        )}

        {/*  Dấu `·` nằm CÙNG span với vế sau — tách riêng thì lúc xuống dòng nó mồ côi ở cuối dòng trên. */}
        <span className="flex flex-wrap gap-x-1 text-xs text-muted-foreground tabular-nums">
          <span>{fieldCount} trường</span>
          <span>
            <span aria-hidden="true">· </span>
            Gửi {formatDateTime(request.created_at)}
          </span>
        </span>
      </span>

      {/*  Mũi tên nói THẺ NÀY BẤM ĐƯỢC: màn cảm ứng không có con trỏ đổi hình khi rê qua. */}
      <ChevronRight className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
    </span>
  )
}
