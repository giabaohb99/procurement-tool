import { Users } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { fromHere } from '@/shared/hooks/use-back-target'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { SearchField } from '@/shared/ui/search-field'
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
//  Mã tình trạng BÌNH THƯỜNG — thẻ ở khổ hẹp im lặng với mã này và chỉ lên
//  tiếng ở ba mã còn lại. ⚠️ `official`, KHÔNG phải `active`: bộ mã sinh từ
//  backend không hề có mã nào tên `active`.
const STATUS_NORMAL = 'official'
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
  const location = useLocation()
  const isMobile = useIsMobile()

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

  //  Ô chọn dựng MỘT LẦN, bày ở hai chỗ (hàng ngang từ `md` · tờ trượt dưới
  //  ngưỡng đó). State cục bộ nên hai bản luôn nói cùng một giá trị.
  const statusSelect = (
    <Select value={status} onValueChange={setStatus}>
      <SelectTrigger className="w-full md:w-44" aria-label="Lọc theo tình trạng">
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
  )

  return (
    <Card className="max-md:gap-4 max-md:py-4">
      <CardHeader className="max-md:px-4">
        <CardTitle className="flex items-center gap-2 text-base">
          <Users className="size-4 text-muted-foreground" />
          Nhân sự thuộc phòng ({data?.total ?? 0})
        </CardTitle>
      </CardHeader>

      <CardContent className="max-md:px-4">
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
          //  Bảng con: bộ lọc nằm ở state cục bộ chứ không lên URL, nên phải tự
          //  khai — nút "Xóa lọc" mặc định của DataTable chỉ biết dọn URL.
          filtersActive={keyword !== '' || status !== ALL}
          onResetFilters={() => {
            setKeyword('')
            setStatus(ALL)
          }}
          //  ⚠️ Gài đường quay lại vào `state` — xem `use-back-target.ts`. Không
          //  có nó thì nút lùi trên hồ sơ nhân sự ghi «Danh sách nhân sự» và
          //  bấm vào ném người dùng ra khỏi phòng ban đang xem.
          onRowClick={(employee) =>
            navigate(appRoutes.hr.employeeDetail(employee.id), { state: fromHere(location) })
          }
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'nhân sự',
          }}
          //  Khổ hẹp: THẺ thay bảng. Sáu cột cộng lại ~1170px, trên máy 390px
          //  chỉ thấy *Mã NV* và một mẩu *Họ tên* — mất đúng hai thứ trả lời
          //  câu hỏi của bảng này (*ai là trưởng bộ phận*, *còn làm việc
          //  không*). Huy hiệu tình trạng chỉ nói khi KHÁC «Chính thức».
          mobileCard={(employee: Employee) => (
            <div className="flex items-center gap-3">
              <div className="min-w-0 flex-1">
                <span className="flex min-w-0 items-center gap-2">
                  <span className="truncate font-medium text-foreground">
                    {employee.full_name}
                  </span>
                  {employee.id === managerId && <Badge className="shrink-0">Trưởng BP</Badge>}
                </span>
                <span className="block truncate text-xs text-muted-foreground">
                  {employee.code}
                  {employee.position ? ` · ${employee.position}` : ''}
                </span>
              </div>

              {employee.status !== STATUS_NORMAL && employee.status_label && (
                <Badge variant="outline" className="shrink-0">
                  {employee.status_label}
                </Badge>
              )}
            </div>
          )}
          toolbar={
            <>
              <SearchField
                value={keyword}
                onChange={setKeyword}
                placeholder={isMobile ? 'Tìm họ tên…' : 'Tìm theo họ tên…'}
                className="md:min-w-56 md:max-w-xs"
              />

              {/*  Khổ hẹp: ô lọc dời vào tờ trượt — hai ô bề rộng cứng trong một
                   thẻ 322px thì rớt thành hai hàng so le. */}
              <QuickFilterSheet
                activeCount={status !== ALL ? 1 : 0}
                onClearAll={() => setStatus(ALL)}
              >
                <QuickFilterField label="Tình trạng">{statusSelect}</QuickFilterField>
              </QuickFilterSheet>

              <div className="hidden items-center gap-3 md:flex">{statusSelect}</div>
            </>
          }
        />
      </CardContent>
    </Card>
  )
}
