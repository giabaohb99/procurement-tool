import { useMemo, useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { DataTablePagination } from '@/shared/data-table/data-table-pagination'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useSetUrlParams, useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { WorkRosterDayList } from '../components/work-roster-day-list'
import { WorkRosterFilterBar } from '../components/work-roster-filter-bar'
import { WorkRosterGrid } from '../components/work-roster-grid'
import { WorkRosterLegend } from '../components/work-roster-legend'
import { WorkRosterToolbar } from '../components/work-roster-toolbar'
import { useCompanies } from '../hooks/use-companies'
import { useDepartments } from '../hooks/use-departments'
import { useWorkRoster } from '../hooks/use-work-roster'
import { rangeLabel, shiftAnchor, toISODate } from '../utils/calendar-grid'
import { parseISODate, parseRosterMode, rosterRange, todayInVietnamISO } from '../utils/work-roster-range'

/** Cỡ trang mặc định theo hợp đồng API (1..100). */
const DEFAULT_PAGE_SIZE = 50
/** Danh mục cho ô lọc — một lượt, đủ rộng cho số pháp nhân / phòng ban hiện có. */
const LOOKUP_PAGE_SIZE = 100

/** Chuỗi trên URL → id nguyên không âm; hỏng thì `0` (= mọi). */
function parseId(value: string): number {
  const n = Number(value)
  return Number.isInteger(n) && n > 0 ? n : 0
}

/**
 * LỊCH TUẦN — «nhìn vô biết ngày nay ai làm, ai nghỉ». Hàng = nhân sự trong phạm
 * vi `employee.read` của người xem, cột = ngày; mặc định xem TUẦN, có nút sang THÁNG.
 * Đơn nghỉ hiện cả đã duyệt lẫn chờ duyệt (xem `WorkRosterCellView`).
 *
 * Kỳ xem, chế độ và bộ lọc nằm trên URL để dán link cho nhau. Phân trang thật theo
 * nhân sự (backend), không tải cả công ty một lượt.
 */
export function WorkRosterPage() {
  const isMobile = useIsMobile()
  const { can } = usePermission()
  const setUrlParams = useSetUrlParams()

  const todayISO = todayInVietnamISO()
  const [modeParam] = useUrlParamState('mode', 'week')
  const [dateParam, setDate] = useUrlParamState('date', todayISO)
  const [companyParam] = useUrlParamState('company', '0')
  const [departmentParam, setDepartment] = useUrlParamState('department', '0')
  const search = useUrlSearchParam('q')

  const mode = parseRosterMode(modeParam)
  const anchor = useMemo(() => parseISODate(dateParam) ?? parseISODate(todayISO) ?? new Date(), [dateParam, todayISO])
  const range = useMemo(() => rosterRange(anchor, mode), [anchor, mode])
  const companyId = parseId(companyParam)
  const departmentId = parseId(departmentParam)

  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [page, setPage] = usePageResetOnFilterChange([companyId, departmentId, search.debouncedValue, pageSize])

  //  ⚠️ Hai danh mục này MƯỢN quyền của phân hệ khác — tắt khi thiếu quyền, kẻo ăn 403.
  const canCompany = can('company', 'read')
  const canDepartment = can('department', 'read')
  const { data: companies } = useCompanies({ page: 1, page_size: LOOKUP_PAGE_SIZE }, { enabled: canCompany })
  const { data: departments } = useDepartments(
    { page: 1, page_size: LOOKUP_PAGE_SIZE, company_id: companyId || undefined },
    { enabled: canDepartment },
  )

  const trimmedQ = search.debouncedValue.trim()
  const { data, isLoading, isError, isFetching, refetch } = useWorkRoster({
    from_date: range.from,
    to_date: range.to,
    company_id: companyId,
    department_id: departmentId,
    q: trimmedQ || undefined,
    page,
    page_size: pageSize,
  })

  const days = data?.days ?? []
  const items = data?.items ?? []
  const total = data?.total ?? 0

  //  Ngày đang chọn ở khổ hẹp: ngày người dùng bấm nếu còn trong kỳ, không thì hôm nay, không thì ngày đầu kỳ.
  const [pickedISO, setPickedISO] = useState('')
  const selectedISO = days.some((d) => d.date === pickedISO)
    ? pickedISO
    : days.some((d) => d.date === todayISO)
      ? todayISO
      : (days[0]?.date ?? '')

  const hasFilter = companyId > 0 || departmentId > 0 || trimmedQ !== ''
  const clearFilters = () => {
    setUrlParams({ company: null, department: null, q: null })
    search.setValue('')
  }

  return (
    <PageContainer>
      <PageHeader
        title="Lịch làm việc"
        description={<span className="max-md:hidden">Ngày nào ai đi làm, ai nghỉ — gồm cả đơn nghỉ đang chờ duyệt.</span>}
      />

      <div className="space-y-3 pb-3">
        <WorkRosterToolbar
          mode={mode}
          onModeChange={(m) => setUrlParams({ mode: m === 'week' ? null : m })}
          label={rangeLabel(anchor, mode)}
          onShift={(step) => setDate(toISODate(shiftAnchor(anchor, mode, step)))}
          onToday={() => setUrlParams({ date: null })}
        />
        <WorkRosterFilterBar
          companies={canCompany ? (companies?.items ?? []) : null}
          departments={canDepartment ? (departments?.items ?? []) : null}
          companyId={companyId}
          departmentId={departmentId}
          //  Đổi pháp nhân thì phòng ban đang chọn có thể không thuộc pháp nhân mới → bỏ chọn, MỘT lượt URL.
          onCompanyChange={(id) => setUrlParams({ company: id ? String(id) : null, department: null })}
          onDepartmentChange={(id) => setDepartment(id ? String(id) : '0')}
          search={search.value}
          onSearchChange={search.setValue}
        />
        <WorkRosterLegend />
      </div>

      {isError ? (
        <div role="alert" className="flex flex-col items-start gap-2 rounded-md border border-destructive/40 p-4 text-sm">
          <p>Không tải được lịch làm việc. Kiểm tra quyền xem nhân sự hoặc thử lại.</p>
          <Button size="sm" variant="outline" onClick={() => void refetch()}>
            Thử lại
          </Button>
        </div>
      ) : isLoading ? (
        <p className="py-8 text-center text-sm text-muted-foreground">Đang tải…</p>
      ) : items.length === 0 ? (
        <div className="space-y-2 rounded-md border border-dashed p-8 text-center text-sm text-muted-foreground">
          <p>
            {hasFilter
              ? 'Không có nhân sự nào khớp bộ lọc.'
              : total > 0
                ? 'Trang này không còn nhân sự nào.'
                : 'Chưa có nhân sự nào trong phạm vi bạn được xem.'}
          </p>
          {hasFilter && (
            <Button size="sm" variant="outline" onClick={clearFilters}>
              Xóa lọc
            </Button>
          )}
        </div>
      ) : (
        <div className={isFetching ? 'opacity-70 transition-opacity' : undefined}>
          {isMobile ? (
            <WorkRosterDayList days={days} items={items} selectedISO={selectedISO} onSelect={setPickedISO} todayISO={todayISO} />
          ) : (
            <WorkRosterGrid days={days} items={items} mode={mode} todayISO={todayISO} />
          )}
        </div>
      )}

      <DataTablePagination
        page={page}
        pageSize={pageSize}
        total={total}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
        unitLabel="nhân sự"
      />
    </PageContainer>
  )
}
