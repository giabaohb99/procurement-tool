import { ChevronRight, TriangleAlert } from 'lucide-react'

import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Badge } from '@/shared/ui/badge'
import { employeeInitials, type Employee } from '../types/employee'

/** Mã tình trạng BÌNH THƯỜNG của một nhân sự đang làm việc. */
const STATUS_NORMAL = 'official'

/**
 * Một hồ sơ nhân sự ở chế độ MÀN HẸP — xem `DataTableProps.mobileCard`.
 *
 * Bảng khai **12 cột**, bề rộng tự nhiên ~2100px: trên máy 390px chỉ thấy *Ảnh*,
 * *Mã NV* và một mẩu *Họ tên*, tức phòng ban · chức vụ · tình trạng đều nằm sau
 * một lượt cuộn ngang.
 *
 * ⚠️ **Gương mặt đứng đầu thẻ, không phải mã.** Bảng để *Ảnh* thành một cột
 * riêng vì lưới cần vậy; trên thẻ thì ảnh là thứ mắt bắt được trước và là cách
 * người ta thật sự nhận ra đồng nghiệp. Mã NV tụt xuống dòng phụ, chỗ của nó
 * cùng với chức vụ.
 *
 * ⚠️ **Mỗi dòng chữ đúng MỘT hàng, dài thì «…»** (luật chung của thẻ danh mục,
 * khách chốt 10/09/2026) — thẻ cao thấp so le nhau thì mắt phải dò lại mép trên
 * của từng thẻ thay vì lướt một cột đều.
 *
 * ⚠️ **Thẻ chỉ nói cái BẤT THƯỜNG.** Huy hiệu tình trạng tắt khi *Chính thức*
 * (gần hết hồ sơ đều vậy, in ra là mấy chục huy hiệu giống hệt nhau); thứ cần
 * nhặt ra là người đã nghỉ. Cùng lý do, dòng cảnh báo *Chưa gán quản lý trực
 * tiếp* chỉ hiện khi ô đó trống.
 *
 * ⚠️ Cảnh báo K5 **phải theo sang thẻ, đừng bỏ vì cho gọn**: ô «quản lý trực
 * tiếp» là thứ bộ máy duyệt đọc để tìm người ký; bỏ trống thì đơn từ lặng lẽ
 * chạy về trưởng bộ phận và không ai biết là đã đi sai đường. Ở khổ rộng nó là
 * một cột đỏ, ở khổ hẹp phải là một dòng đỏ — không thể là khoảng trắng.
 */
export function EmployeeCard({ employee }: { employee: Employee }) {
  const workplace = [employee.department_name, employee.company_name].filter(Boolean).join(' · ')

  return (
    <div className="flex items-start gap-3">
      <Avatar className="size-9 shrink-0">
        <AvatarImage src={employee.avatar} alt={employee.full_name} />
        <AvatarFallback className="text-xs">
          {employeeInitials(employee.full_name)}
        </AvatarFallback>
      </Avatar>

      <div className="min-w-0 flex-1 space-y-1">
        <span className="flex min-w-0 items-center gap-2">
          <span className="truncate font-medium text-foreground">{employee.full_name}</span>
          {employee.status !== STATUS_NORMAL && employee.status_label && (
            <Badge variant="outline" className="shrink-0">
              {employee.status_label}
            </Badge>
          )}
        </span>

        <span className="block truncate text-xs text-muted-foreground">
          {employee.code}
          {employee.position ? ` · ${employee.position}` : ''}
        </span>

        {workplace && (
          <span className="block truncate text-xs text-muted-foreground">{workplace}</span>
        )}

        {!employee.direct_manager_name && (
          <span className="flex items-center gap-1 text-xs text-destructive">
            <TriangleAlert className="size-3.5 shrink-0" />
            Chưa gán quản lý trực tiếp
          </span>
        )}
      </div>

      {/*  Mũi tên nói THẺ NÀY BẤM ĐƯỢC: màn cảm ứng không có con trỏ đổi hình khi
           rê qua, nên phải nói bằng hình. */}
      <ChevronRight className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
    </div>
  )
}
