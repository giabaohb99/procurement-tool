import { Users } from 'lucide-react'
import { useMemo } from 'react'
import { useLocation } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { fromHere } from '@/shared/hooks/use-back-target'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { useConcurrentMembers } from '../hooks/use-concurrent-members'
import type { ConcurrentMember } from '../types/concurrent-member'
import { CONCURRENT_KIND_DEPARTMENT } from '../types/employee-concurrent'
import { formatConcurrentPeriod, formatPrimaryPlace } from '../utils/concurrent-member-display'
import { ConcurrentMemberName } from './concurrent-member-name'

interface DepartmentConcurrentMembersTableProps {
  departmentId: number
}

/**
 * Người KIÊM NHIỆM ở phòng này (duoc-CR-755) — bảng thứ hai ngay dưới `DepartmentMembersTable`. Chỉ dòng loại
 * **Phòng ban** (`kind=1`, duoc-CR-756): dòng loại Công ty không gắn phòng, hiện ở trang chi tiết công ty.
 *
 * Tách bảng chứ không trộn vào bảng thành viên: bảng thành viên phân trang ở máy chủ (luật §8
 * `chung-dat-ten-va-quy-uoc.md`), nhét thêm người kiêm nhiệm vào cùng trang là xếp lại một trang và nói dối về
 * thứ tự. Bảng này nạp đủ (trần 200 ở backend), backend đã xếp theo họ tên.
 *
 * Mỗi hàng chỉ là bản TÓM TẮT (không điện thoại, email, ngày sinh). Tên chỉ là liên kết khi `can_open` — dòng tắt
 * công tắc "Tính vào phạm vi quyền" thì người xem thấy tên nhưng không mở được hồ sơ.
 *
 * Ẩn cả khối khi không có ai (đa số phòng không có người kiêm nhiệm — một khung rỗng chỉ thêm nhiễu); lỗi tải
 * thì vẫn hiện khung để người dùng thấy là có chuyện, không lặng lẽ biến mất.
 */
export function DepartmentConcurrentMembersTable({ departmentId }: DepartmentConcurrentMembersTableProps) {
  const location = useLocation()
  const { can } = usePermission()
  //  Backend gác `employee.read`; thiếu quyền thì không gọi (403 trên GET không bật toast, bảng chỉ lặng lẽ rỗng).
  const canRead = can('employee', 'read')
  const { data, isLoading, isError } = useConcurrentMembers(
    { department_id: departmentId, kind: CONCURRENT_KIND_DEPARTMENT },
    { enabled: canRead },
  )

  const columns = useMemo<DataTableColumn<ConcurrentMember>[]>(
    () => [
      { key: 'code', header: 'Mã NV', width: 130, cell: (m) => m.code },
      {
        key: 'full_name',
        header: 'Họ tên',
        width: 300,
        hideable: false,
        cell: (m) => <ConcurrentMemberName member={m} backState={fromHere(location)} />,
      },
      { key: 'position_label', header: 'Chức vụ kiêm nhiệm', width: 200, wrap: true, cell: (m) => m.position_label || '—' },
      //  Dòng loại Phòng ban luôn ở công ty chính của người đó; phòng DÙNG CHUNG phục vụ nhiều công ty nên vẫn ghi rõ.
      { key: 'company_name', header: 'Công ty', width: 220, wrap: true, cell: (m) => m.company_name || '—' },
      { key: 'period', header: 'Hiệu lực', width: 200, cell: (m) => formatConcurrentPeriod(m.from_date, m.to_date) },
      {
        key: 'primary_place',
        header: 'Thuộc phòng chính',
        width: 280,
        wrap: true,
        cell: (m) => formatPrimaryPlace(m) || '—',
      },
    ],
    [location],
  )

  if (!canRead) return null
  if (!isLoading && !isError && (data?.items.length ?? 0) === 0) return null

  return (
    <Card className="max-md:gap-4 max-md:py-4">
      <CardHeader className="max-md:px-4">
        <CardTitle className="flex items-center gap-2 text-base">
          <Users className="size-4 text-muted-foreground" />
          Kiêm nhiệm tại phòng này ({data?.total ?? 0})
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          Người thuộc phòng khác đang kiêm nhiệm ở đây. Quân số và báo cáo vẫn tính ở phòng chính của họ.
          {data?.truncated ? ' Danh sách quá dài nên chỉ hiện 200 người đầu.' : ''}
        </p>
      </CardHeader>

      <CardContent className="max-md:px-4">
        <DataTable
          columns={columns}
          rows={data?.items}
          getRowId={(member) => member.id}
          //  Id DÒNG kiêm nhiệm không có nghĩa với người đọc (không phải mã nhân sự) — bỏ cột ID tự thêm.
          idColumn={false}
          isLoading={isLoading}
          isError={isError}
          errorMessage="Không tải được danh sách kiêm nhiệm."
          emptyMessage="Chưa có ai kiêm nhiệm ở phòng này."
          storageKey="hr.department-concurrent-members"
          mobileCard={(member: ConcurrentMember) => (
            <div className="min-w-0 space-y-0.5">
              <ConcurrentMemberName member={member} backState={fromHere(location)} />
              <span className="block truncate text-xs text-muted-foreground">
                {[member.code, member.position_label].filter(Boolean).join(' · ')}
              </span>
              <span className="block text-xs text-muted-foreground">
                {formatConcurrentPeriod(member.from_date, member.to_date)}
              </span>
              {formatPrimaryPlace(member) && (
                <span className="block text-xs text-muted-foreground">Chính: {formatPrimaryPlace(member)}</span>
              )}
            </div>
          )}
        />
      </CardContent>
    </Card>
  )
}
