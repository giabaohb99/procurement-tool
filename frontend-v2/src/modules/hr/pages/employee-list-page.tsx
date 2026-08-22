import { Plus, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { appConfig } from '@/core/config/app-config'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterQuery,
} from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { EmployeeFormDialog } from '../components/employee-form-dialog'
import { EMPLOYEE_FILTER_FIELDS } from '../config/hr-filter-fields'
import { useDepartments } from '../hooks/use-departments'
import { useEmployees } from '../hooks/use-employees'
import {
  EMPLOYEE_STATUS_OPTIONS,
  employeeInitials,
  type Employee,
} from '../types/employee'

/** Giá trị của mục "tất cả" trong Select — Radix cấm option value rỗng. */
const ALL = 'all'

/**
 * Hằng số ở tầng module, không dựng lại mỗi lần render: `preserveParams` là
 * mảng, đổi identity liên tục sẽ làm `applyChanges` của bộ lọc tái tạo vô ích.
 *
 * `preserveParams` liệt kê param của các select trên thanh công cụ — thiếu tên
 * nào thì bấm "Áp dụng" bộ lọc nâng cao sẽ xóa mất bộ lọc đó khỏi URL.
 */
const FILTER_CONFIG = {
  fields: EMPLOYEE_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: ['department_id', 'status'],
}

export function EmployeeListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <EmployeeListContent />
    </FilterProvider>
  )
}

/**
 * Danh sách nhân sự.
 *
 * Thanh công cụ chỉ giữ ba thứ dùng hằng ngày: ô tìm theo tên, phòng ban và
 * tình trạng làm việc. Mã NV / Email / Chức vụ / trạng thái hồ sơ nằm trong
 * "Bộ lọc" nâng cao — xem `config/hr-filter-fields.ts`.
 */
function EmployeeListContent() {
  const navigate = useNavigate()

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [departmentId, setDepartmentId] = useUrlParamState('department_id', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [isFormOpen, setFormOpen] = useState(false)

  const { data: departments } = useDepartments({ page_size: 500 })
  const { queryParams, queryKey } = useFilterQuery()

  // Đổi BẤT KỲ điều kiện lọc nào cũng phải về trang 1, nếu không sẽ rơi vào
  // trang trống khi kết quả mới ít hơn trang đang đứng.
  const [page, setPage] = usePageResetOnFilterChange([queryKey, debouncedValue, departmentId, status])

  // Chỉ gửi key nằm trong whitelist FILTERABLE của backend.
  const params: ListParams = { page, page_size: pageSize, ...queryParams }
  if (debouncedValue) params.full_name = debouncedValue
  if (departmentId !== ALL) params.department_id = Number(departmentId)
  if (status !== ALL) params.status = status

  const { data, isLoading, isError } = useEmployees(params)

  const columns = useMemo<DataTableColumn<Employee>[]>(
    () => [
      {
        key: 'avatar',
        // Có nhãn để còn hiện được trong menu "Cột" (mục không tên là mục trống).
        header: 'Ảnh',
        width: 72,
        minWidth: 56,
        cell: (employee) => (
          <Avatar className="size-7">
            <AvatarImage src={employee.avatar} alt={employee.full_name} />
            <AvatarFallback className="text-xs">
              {employeeInitials(employee.full_name)}
            </AvatarFallback>
          </Avatar>
        ),
      },
      { key: 'code', header: 'Mã NV', width: 140, cell: (e) => e.code },
      {
        key: 'full_name',
        header: 'Họ tên',
        width: 260,
        // Ẩn cột tên thì bảng không còn nhận ra ai với ai.
        hideable: false,
        cell: (e) => <span className="truncate">{e.full_name}</span>,
      },
      {
        key: 'email',
        header: 'Email',
        width: 220,
        cell: (e) => <span className="text-muted-foreground">{e.email || '—'}</span>,
      },
      {
        key: 'department_name',
        header: 'Phòng ban',
        width: 180,
        cell: (e) => e.department_name || '—',
      },
      { key: 'position', header: 'Chức vụ', width: 180, cell: (e) => e.position || '—' },
      {
        key: 'status',
        header: 'Tình trạng',
        width: 140,
        cell: (e) => (
          // B-03: so với MÃ, hiện NHÃN. Bản cũ so với chuỗi 'Chính thức' — sau khi
          // chuyển mã thì không dòng nào còn tô đậm nữa mà chẳng có lỗi nào nổ ra.
          <Badge variant={e.status === 'official' ? 'default' : 'secondary'}>
            {e.status_label || e.status || '—'}
          </Badge>
        ),
      },
    ],
    [],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Nhân sự"
        description="Hồ sơ nhân viên theo phòng ban, kèm tài khoản đăng nhập."
        actions={
          <PermissionGate entity="employee" action="create">
            <Button onClick={() => setFormOpen(true)}>
              <Plus />
              Thêm mới
            </Button>
          </PermissionGate>
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(employee) => employee.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không tìm thấy nhân sự nào."
          storageKey="hr.employees"
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
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo họ tên…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              <Select value={departmentId} onValueChange={setDepartmentId}>
                <SelectTrigger className="w-52">
                  <SelectValue placeholder="Phòng ban" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả phòng ban</SelectItem>
                  {(departments?.items ?? []).map((department) => (
                    <SelectItem key={department.id} value={String(department.id)}>
                      {department.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="Tình trạng" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả tình trạng</SelectItem>
                  {EMPLOYEE_STATUS_OPTIONS.map((item) => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <ConditionalFilter />
            </>
          }
        />
      </Card>

      <EmployeeFormDialog open={isFormOpen} onOpenChange={setFormOpen} />
    </PageContainer>
  )
}
