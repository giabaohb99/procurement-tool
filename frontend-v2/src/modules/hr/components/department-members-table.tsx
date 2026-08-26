import { Search, Users } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { useEmployees } from '../hooks/use-employees'
import type { ListParams } from '@/shared/types/api'
import { EMPLOYEE_STATUS_OPTIONS, type Employee } from '../types/employee'

interface DepartmentMembersTableProps {
  departmentId: number
  /** Trưởng bộ phận được gắn huy hiệu trong cột họ tên. */
  managerId?: number
}

const ALL = 'all'
/** Ô tìm gõ tay, không đẩy lên URL: đây là bảng con của trang chi tiết. */
const SEARCH_DELAY_MS = 350

/**
 * Danh sách nhân sự thuộc phòng ban, hiện ở trang chi tiết phòng ban.
 *
 * Bảng con nhưng vẫn đủ **tìm kiếm · lọc tình trạng · phân trang** như mọi màn
 * danh sách khác (`docs/ui/table.md` §3): phòng lớn có vài chục người, trước đây
 * đổ tối đa 200 dòng một lượt rồi để người dùng tự cuộn tìm — cuộn qua 37 dòng
 * đã khó chịu, 200 thì không dùng được.
 *
 * ⚠️ KHÔNG còn đẩy trưởng bộ phận lên đầu. Phân trang chạy ở máy chủ nên xếp
 * lại trong một trang là nói dối về thứ tự: người đứng đầu trang 2 trông như
 * người đầu danh sách. Trưởng bộ phận nhận diện bằng huy hiệu, và có sẵn ở ô
 * *Trưởng bộ phận* ngay phía trên.
 */
export function DepartmentMembersTable({
  departmentId,
  managerId,
}: DepartmentMembersTableProps) {
  const navigate = useNavigate()

  const [keyword, setKeyword] = useState('')
  const debouncedKeyword = useDebouncedValue(keyword, SEARCH_DELAY_MS)
  const [status, setStatus] = useState(ALL)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [page, setPage] = usePageResetOnFilterChange([debouncedKeyword, status, departmentId])

  //  Chỉ gửi key nằm trong whitelist FILTERABLE của backend.
  const params: ListParams = { department_id: departmentId, page, page_size: pageSize }
  if (debouncedKeyword) params.full_name = debouncedKeyword
  if (status !== ALL) params.status = status

  const { data, isLoading, isError } = useEmployees(params)

  const columns = useMemo<DataTableColumn<Employee>[]>(
    () => [
      { key: 'code', header: 'Mã NV', width: 140, cell: (e) => e.code },
      {
        key: 'full_name',
        header: 'Họ tên',
        width: 300,
        hideable: false,
        cell: (employee) => (
          <span className="flex min-w-0 items-center gap-2">
            <span className="truncate">{employee.full_name}</span>
            {employee.id === managerId && <Badge>Trưởng BP</Badge>}
          </span>
        ),
      },
      { key: 'position', header: 'Chức danh', width: 220, cell: (e) => e.position || '—' },
      {
        key: 'status',
        header: 'Tình trạng',
        width: 140,
        cell: (e) => <Badge variant="secondary">{e.status_label || '—'}</Badge>,
      },
      { key: 'email', header: 'Email', width: 220, defaultHidden: true, cell: (e) => e.email || '—' },
      { key: 'phone', header: 'Điện thoại', width: 150, defaultHidden: true, cell: (e) => e.phone || '—' },
    ],
    [managerId],
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Users className="size-4 text-muted-foreground" />
          Nhân sự thuộc phòng ({data?.total ?? 0})
        </CardTitle>
      </CardHeader>

      <CardContent>
        <DataTable
          columns={columns}
          rows={data?.items}
          getRowId={(employee) => employee.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage={
            debouncedKeyword || status !== ALL
              ? 'Không có nhân sự nào khớp bộ lọc.'
              : 'Chưa có nhân sự nào thuộc phòng ban này.'
          }
          storageKey="hr.department-members"
          onRowClick={(employee) => navigate(appRoutes.hr.employeeDetail(employee.id))}
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'nhân sự',
          }}
          toolbar={
            <>
              <div className="relative min-w-56 flex-1 md:max-w-sm">
                <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo họ tên…"
                  value={keyword}
                  onChange={(event) => setKeyword(event.target.value)}
                />
              </div>

              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="w-44">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả tình trạng</SelectItem>
                  {EMPLOYEE_STATUS_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </>
          }
        />
      </CardContent>
    </Card>
  )
}
