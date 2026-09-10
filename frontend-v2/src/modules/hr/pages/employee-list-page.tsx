import { Plus } from 'lucide-react'
import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { appConfig } from '@/core/config/app-config'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
  useFilterQuery,
} from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable } from '@/shared/data-table'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useScrolled } from '@/shared/hooks/use-scrolled'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { useUrlSort } from '@/shared/hooks/use-url-sort'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { AdvancedFilterSection } from '@/shared/ui/advanced-filter-section'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { SearchField } from '@/shared/ui/search-field'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { EmployeeCard } from '../components/employee-card'
import { EmployeeFormDialog } from '../components/employee-form-dialog'
import { EMPLOYEE_FILTER_FIELDS } from '../config/hr-filter-fields'
import { useDepartments } from '../hooks/use-departments'
import { EMPLOYEE_COLUMNS } from '../config/employee-columns'
import { useEmployees } from '../hooks/use-employees'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'
import {
  EMPLOYEE_STATUS_OPTIONS,
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
  preserveParams: ['department_id', 'status', 'sort_by', 'sort_dir'],
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
  const { sortBy, sortDir, handleSortChange } = useUrlSort()
  const stickyRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(stickyRef)
  const isMobile = useIsMobile()

  const { data: departments } = useDepartments({ page_size: 500 })
  const { queryParams, queryKey } = useFilterQuery()
  //  Bộ lọc nâng cao: đếm để gắn huy hiệu lên nút «Bộ lọc», và hai hàm để nút
  //  «Xóa lọc» / «Áp dụng» của tờ trượt điều khiển được nó.
  const {
    activeCount: filterActiveCount,
    reset: filterReset,
    apply: filterApply,
  } = useFilterContext()

  //  Bảng đang bị thu hẹp bởi BẤT KỲ đường nào — quyết định câu nói khi rỗng.
  const isFiltering =
    Boolean(debouncedValue) || departmentId !== ALL || status !== ALL || filterActiveCount > 0

  // Đổi BẤT KỲ điều kiện lọc nào cũng phải về trang 1, nếu không sẽ rơi vào
  // trang trống khi kết quả mới ít hơn trang đang đứng.
  const [page, setPage] = usePageResetOnFilterChange([
    queryKey,
    debouncedValue,
    departmentId,
    status,
    sortBy,
    sortDir,
  ])

  // Chỉ gửi key nằm trong whitelist FILTERABLE của backend.
  const params: ListParams = { page, page_size: pageSize, ...queryParams }
  // Ô tìm nhanh dùng `search` — backend quét OR trên mã NV / họ tên / email / SĐT.
  if (debouncedValue) params.search = debouncedValue
  if (departmentId !== ALL) params.department_id = Number(departmentId)
  if (status !== ALL) params.status = status
  if (sortBy) {
    params.sort_by = sortBy
    params.sort_dir = sortDir
  }

  const { data, isLoading, isError } = useEmployees(params)

  //  Hai ô lọc dựng MỘT LẦN, bày ở HAI chỗ: hàng ngang của thanh công cụ từ
  //  `md`, tờ trượt lọc ở dưới ngưỡng đó. State nằm trên URL nên hai bản luôn
  //  nói cùng một giá trị. Bề rộng cứng chỉ áp từ `md`.
  const departmentSelect = (
    <Select value={departmentId} onValueChange={setDepartmentId}>
      <SelectTrigger className="w-full md:w-52" aria-label="Lọc theo phòng ban">
        <SelectValue placeholder="Phòng ban" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả phòng ban</SelectItem>
        {/*  `0` là GIÁ TRỊ THẬT của cột, không phải mã giả cho "tất cả" — hồ sơ
             chưa gán phòng lưu đúng số 0. Có mục này thì nhóm đó mới tìm ra
             được, mà nó lại chính là nhóm người ta cần tìm để đi gắn cho đủ. */}
        <SelectItem value="0">Chưa gán phòng ban</SelectItem>
        {(departments?.items ?? []).map((department) => (
          <SelectItem key={department.id} value={String(department.id)}>
            {department.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const statusSelect = (
    <Select value={status} onValueChange={setStatus}>
      <SelectTrigger className="w-full md:w-44" aria-label="Lọc theo tình trạng">
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
  )

  return (
    //  ⚠️ `fill` chỉ bật từ `md`: ở khổ hẹp bảng đổi thành danh sách thẻ dài, mà
    //  `fill` nhét nó vào một khe vài trăm pixel và biến thành cuộn LỒNG.
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Nhân sự"
        //  Dòng mô tả ẩn ở khổ hẹp: câu giới thiệu màn, đọc một lần rồi thôi.
        description={
          <span className="max-md:hidden">
            Hồ sơ nhân viên theo phòng ban, kèm tài khoản đăng nhập.
          </span>
        }
        actions={
          //  Khổ hẹp: nút chiếm trọn hàng — hành động chính phải dễ chạm nhất.
          <PermissionGate entity="employee" action="create">
            <Button className="max-md:w-full" onClick={() => setFormOpen(true)}>
              <Plus />
              Thêm mới
            </Button>
          </PermissionGate>
        }
      />

      {/*  `group` + `data-scrolled` là đường dẫn tín hiệu «đã cuộn» xuống thanh
           công cụ ghim (do `DataTable` vẽ, tầng này không với tới bằng prop). */}
      <div
        ref={stickyRef}
        data-scrolled={scrolled ? '' : undefined}
        className="group flex min-h-0 flex-1 flex-col"
      >
      <Card className="flex min-h-0 flex-1 flex-col p-3 md:p-4">
        <DataTable
          fillHeight
          columns={EMPLOYEE_COLUMNS}
          rows={data?.items}
          getRowId={(employee) => employee.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage={
            //  Nói rõ RỖNG VÌ BỘ LỌC hay rỗng vì chưa có gì.
            isFiltering
              ? 'Không có nhân sự nào khớp bộ lọc.'
              : 'Chưa có nhân sự nào. Bấm «Thêm mới» để tạo.'
          }
          storageKey="hr.employees"
          //  Khổ hẹp: THẺ thay bảng — xem `EmployeeCard`.
          mobileCard={(employee: Employee) => <EmployeeCard employee={employee} />}
          //  Danh sách thẻ dài hơn một màn và CẢ TRANG cuộn, nên không ghim thì
          //  ô tìm trôi mất ngay nhịp vuốt đầu.
          toolbarClassName={LIST_TOOLBAR_STICKY_TOP}
          onRowClick={(employee) => navigate(appRoutes.hr.employeeDetail(employee.id))}
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={handleSortChange}
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
              {/*  ⚠️ Câu gợi ý rút gọn ở khổ hẹp và đo theo lúc ĐANG LỌC: nút
                   *Bộ lọc* nở thêm 24px khi mọc huy hiệu số. Bản đầy đủ giữ từ
                   `md`, ở đó ô rộng 256px. */}
              <SearchField
                value={keyword}
                onChange={setKeyword}
                placeholder={isMobile ? 'Tìm tên, mã NV…' : 'Tìm theo tên, mã NV, email, SĐT…'}
                className="max-md:min-w-40 md:w-64 md:max-w-sm md:flex-none"
              />

              {/*  Khổ hẹp: hai ô lọc + bộ lọc nâng cao dọn hết vào tờ trượt. Bản
                   cũ để ba ô bề rộng CỨNG trong một thẻ rộng 322px nên mỗi ô rớt
                   xuống một hàng riêng — bốn hàng bậc thang. */}
              <QuickFilterSheet
                activeCount={
                  (departmentId !== ALL ? 1 : 0) + (status !== ALL ? 1 : 0) + filterActiveCount
                }
                onClearAll={() => {
                  setDepartmentId(ALL)
                  setStatus(ALL)
                  filterReset()
                }}
                onApply={filterApply}
              >
                <QuickFilterField label="Phòng ban">{departmentSelect}</QuickFilterField>
                <QuickFilterField label="Tình trạng">{statusSelect}</QuickFilterField>
                <AdvancedFilterSection />
              </QuickFilterSheet>

              <div className="hidden items-center gap-3 md:flex">
                {departmentSelect}
                {statusSelect}
                <ConditionalFilter />
              </div>
            </>
          }
        />
      </Card>
      </div>

      <EmployeeFormDialog open={isFormOpen} onOpenChange={setFormOpen} />
    </PageContainer>
  )
}
