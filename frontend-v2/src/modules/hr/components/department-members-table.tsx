import { Users } from 'lucide-react'
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { useEmployees } from '../hooks/use-employees'
import type { Employee } from '../types/employee'

interface DepartmentMembersTableProps {
  departmentId: number
  /** Trưởng bộ phận được đẩy lên đầu và gắn huy hiệu. */
  managerId?: number
}

/**
 * Danh sách nhân sự thuộc phòng ban, hiện ở trang chi tiết phòng ban.
 * Nạp một lần (tối đa 200 dòng) nên không cần phân trang.
 */
export function DepartmentMembersTable({
  departmentId,
  managerId,
}: DepartmentMembersTableProps) {
  const navigate = useNavigate()
  const { data, isLoading, isError } = useEmployees({
    department_id: departmentId,
    page_size: 200,
  })

  const members = useMemo(
    () => sortManagerFirst(data?.items ?? [], managerId),
    [data?.items, managerId],
  )

  const columns = useMemo<DataTableColumn<Employee>[]>(
    () => [
      { key: 'code', header: 'Mã NV', width: 140, cell: (e) => e.code },
      {
        key: 'full_name',
        header: 'Họ tên',
        width: 320,
        hideable: false,
        cell: (employee) => (
          <span className="flex min-w-0 items-center gap-2">
            <span className="truncate">{employee.full_name}</span>
            {employee.id === managerId && <Badge>Trưởng BP</Badge>}
          </span>
        ),
      },
      { key: 'position', header: 'Chức danh', width: 240, cell: (e) => e.position || '—' },
      {
        key: 'email',
        header: 'Email',
        width: 220,
        defaultHidden: true,
        cell: (e) => e.email || '—',
      },
    ],
    [managerId],
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Users className="size-4 text-muted-foreground" />
          Nhân sự thuộc phòng ({members.length})
        </CardTitle>
      </CardHeader>

      <CardContent>
        <DataTable
          columns={columns}
          rows={members}
          getRowId={(employee) => employee.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Chưa có nhân sự nào thuộc phòng ban này."
          storageKey="hr.department-members"
          onRowClick={(employee) => navigate(appRoutes.hr.employeeDetail(employee.id))}
        />
      </CardContent>
    </Card>
  )
}

/** Trưởng bộ phận lên đầu, phần còn lại xếp theo tên. */
function sortManagerFirst(items: Employee[], managerId?: number): Employee[] {
  return [...items].sort((a, b) => {
    if (a.id === managerId) return -1
    if (b.id === managerId) return 1
    return a.full_name.localeCompare(b.full_name, 'vi')
  })
}
