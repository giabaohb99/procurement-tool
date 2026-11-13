import { Users } from 'lucide-react'
import { useMemo } from 'react'
import { useLocation } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { fromHere } from '@/shared/hooks/use-back-target'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { useConcurrentMembers } from '../hooks/use-concurrent-members'
import type { ConcurrentMember } from '../types/concurrent-member'
import { CONCURRENT_KIND_COMPANY } from '../types/employee-concurrent'
import { formatConcurrentPeriod, formatPrimaryPlace } from '../utils/concurrent-member-display'
import { ConcurrentMemberName } from './concurrent-member-name'
import { EmployeeConcurrentStatusBadge } from './employee-concurrent-status-badge'

interface CompanyConcurrentMembersTableProps {
  companyId: number
}

/**
 * Người KIÊM NHIỆM cả công ty này (duoc-CR-756) — dòng loại **Công ty** (`kind=2`) của người có pháp nhân chính ở công
 * ty khác, đặt dưới biểu mẫu chi tiết công ty. Người đó được tính như người của công ty này theo bậc vai trò, nhưng quân
 * số và báo cáo vẫn đếm ở công ty chính của họ — nên bảng riêng, không trộn vào danh sách nhân sự.
 *
 * Bản TÓM TẮT (không điện thoại, email, ngày sinh — API đã không trả). Tên là liên kết khi `can_open`. Backend gác
 * `employee.read` + lọc theo phạm vi người xem; thiếu quyền thì không gọi (403 trên GET không bật toast). Nạp đủ (trần
 * 200), backend xếp theo họ tên. Ẩn cả khối khi không có ai, lỗi tải thì vẫn hiện khung — cùng nếp bảng ở trang phòng ban.
 */
export function CompanyConcurrentMembersTable({ companyId }: CompanyConcurrentMembersTableProps) {
  const location = useLocation()
  const { can } = usePermission()
  const canRead = can('employee', 'read')
  const { data, isLoading, isError } = useConcurrentMembers(
    { company_id: companyId, kind: CONCURRENT_KIND_COMPANY },
    { enabled: canRead },
  )

  const columns = useMemo<DataTableColumn<ConcurrentMember>[]>(
    () => [
      { key: 'code', header: 'Mã NV', width: 110, cell: (m) => m.code },
      {
        key: 'full_name',
        header: 'Họ tên',
        width: 240,
        hideable: false,
        cell: (m) => <ConcurrentMemberName member={m} backState={fromHere(location)} showStatus={false} />,
      },
      { key: 'position_label', header: 'Chức vụ kiêm nhiệm', width: 150, wrap: true, cell: (m) => m.position_label || '—' },
      { key: 'period', header: 'Thời hạn', width: 170, cell: (m) => formatConcurrentPeriod(m.from_date, m.to_date) },
      { key: 'status', header: 'Trạng thái', width: 120, cell: (m) => <EmployeeConcurrentStatusBadge row={m} /> },
      {
        key: 'primary_place',
        header: 'Nơi làm chính',
        width: 240,
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
          Kiêm nhiệm tại công ty này ({data?.total ?? 0})
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          Người thuộc công ty khác đang kiêm nhiệm cả công ty này, được tính như người của công ty theo bậc vai trò.
          Quân số và báo cáo vẫn tính ở công ty chính của họ.
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
          emptyMessage="Chưa có ai kiêm nhiệm ở công ty này."
          storageKey="hr.company-concurrent-members"
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
