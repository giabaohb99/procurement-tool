import { useMemo, useState } from 'react'

import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { DataTablePagination } from '@/shared/data-table/data-table-pagination'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useSetUrlParams, useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { LookupOption } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { WorkRosterDayList } from '../components/work-roster-day-list'
import { WorkRosterFilterBar } from '../components/work-roster-filter-bar'
import { WorkRosterGrid } from '../components/work-roster-grid'
import { WorkRosterLegend } from '../components/work-roster-legend'
import { WorkRosterShiftActions } from '../components/work-roster-shift-actions'
import { WorkRosterToolbar } from '../components/work-roster-toolbar'
import { WorkShiftCopyWeekDialog } from '../components/work-shift-copy-week-dialog'
import { WorkShiftDialog } from '../components/work-shift-dialog'
import { useCompanies } from '../hooks/use-companies'
import { useDepartments } from '../hooks/use-departments'
import { useRosterShiftEditing } from '../hooks/use-roster-shift-editing'
import { useWorkRoster } from '../hooks/use-work-roster'
import { rangeLabel, shiftAnchor, toISODate } from '../utils/calendar-grid'
import { parseISODate, parseRosterMode, rosterRange, todayInVietnamISO } from '../utils/work-roster-range'
import { resolveAssignmentMode } from '../utils/work-schedule-assignment-mode'
import {
  clampRosterDepartment,
  defaultRosterDepartment,
  departmentAllLabel,
  resolveRosterViewScope,
  viewerDepartmentOptions,
} from '../utils/work-roster-view-scope'

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
 * LỊCH TUẦN — "nhìn vô biết ngày nay ai làm, ai nghỉ". Hàng = nhân sự trong phạm
 * vi `employee.read` của người xem, cột = ngày; mặc định xem TUẦN, có nút sang THÁNG.
 * Đơn nghỉ hiện cả đã duyệt lẫn chờ duyệt (xem `WorkRosterCellView`).
 *
 * Kỳ xem, chế độ và bộ lọc nằm trên URL để dán link cho nhau. Phân trang thật theo
 * nhân sự (backend), không tải cả công ty một lượt.
 *
 * XẾP CA (duoc-CR-761): người có `work_schedule.write` (Nhân sự) hoặc `work_schedule_personal.write` (Trưởng phòng)
 * bấm ô để mở hộp xếp ca, tick dòng rồi "Chép tuần trước" (chế độ tuần). Trưởng phòng mở màn là xem PHÒNG MÌNH
 * (chọn "Các phòng của tôi" thì ghi `department=0` lên URL để không bị kéo về phòng chính).
 *
 * PHẠM VI XEM (`resolveRosterViewScope`, khớp backend): Nhân sự đủ bộ lọc; Trưởng phòng không lọc pháp nhân, ô phòng
 * ban chỉ có phòng của mình (chính + kiêm nhiệm); Giám đốc (chỉ xem) không lọc pháp nhân, ô phòng ban là danh mục phòng
 * của công ty mình; người còn lại chỉ thấy lịch của chính mình — ẩn bộ lọc, ô tìm.
 */
export function WorkRosterPage() {
  const isMobile = useIsMobile()
  const { can } = usePermission()
  const { user } = useAuth()
  const setUrlParams = useSetUrlParams()
  const isPersonalArranger = resolveAssignmentMode(can, 'write') === 'personal'
  const scope = resolveRosterViewScope(can)
  const ownDepartments = useMemo(() => viewerDepartmentOptions(user), [user])
  //  Trưởng phòng mặc định xem phòng CHÍNH của mình.
  const defaultDepartment = String(defaultRosterDepartment(scope, ownDepartments))

  const todayISO = todayInVietnamISO()
  const [modeParam] = useUrlParamState('mode', 'week')
  const [dateParam, setDate] = useUrlParamState('date', todayISO)
  const [companyParam] = useUrlParamState('company', '0')
  const [departmentParam, setDepartment] = useUrlParamState('department', defaultDepartment)
  const search = useUrlSearchParam('q')

  const mode = parseRosterMode(modeParam)
  const anchor = useMemo(() => parseISODate(dateParam) ?? parseISODate(todayISO) ?? new Date(), [dateParam, todayISO])
  const range = useMemo(() => rosterRange(anchor, mode), [anchor, mode])
  //  Ngoài phạm vi Nhân sự: không lọc pháp nhân; phòng chỉ trong phòng của mình; người chỉ xem mình thì không lọc gì.
  const companyId = scope === 'all' ? parseId(companyParam) : 0
  const departmentId = scope === 'self' ? 0 : clampRosterDepartment(scope, parseId(departmentParam), ownDepartments)

  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [page, setPage] = usePageResetOnFilterChange([companyId, departmentId, search.debouncedValue, pageSize])

  //  ⚠️ Hai danh mục này MƯỢN quyền của phân hệ khác — tắt khi thiếu quyền, kẻo ăn 403.
  const canCompany = scope === 'all' && can('company', 'read')
  const canDepartment = (scope === 'all' || scope === 'company') && can('department', 'read')
  //  Giám đốc: danh mục phòng của công ty mình (backend cũng chỉ trả người trong công ty đó).
  const departmentCompanyId = scope === 'company' ? user?.company_id || undefined : companyId || undefined
  const { data: companies } = useCompanies({ page: 1, page_size: LOOKUP_PAGE_SIZE }, { enabled: canCompany })
  const { data: departments } = useDepartments(
    { page: 1, page_size: LOOKUP_PAGE_SIZE, company_id: departmentCompanyId },
    { enabled: canDepartment },
  )

  const trimmedQ = scope === 'self' ? '' : search.debouncedValue.trim()
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

  const shifts = useRosterShiftEditing(items, { selectable: scope !== 'self' && mode === 'week' && !isMobile })
  const nameOf = (id: number) => items.find((i) => i.employee_id === id)?.full_name
  const copyIds = shifts.selectedIds.length > 0 ? shifts.selectedIds : shifts.copyDefaultIds

  //  Ô phòng ban: Nhân sự đọc danh mục (khi có quyền); Trưởng phòng chỉ phòng của mình từ hồ sơ đăng nhập.
  let departmentOptions: LookupOption[] | null = null
  if (scope === 'all' || scope === 'company') departmentOptions = canDepartment ? (departments?.items ?? []) : null
  else if (scope === 'departments' && ownDepartments.length > 0) departmentOptions = ownDepartments

  const hasFilter = companyId > 0 || String(departmentId) !== defaultDepartment || trimmedQ !== ''
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
          actions={
            shifts.canArrange && mode === 'week' ? (
              <WorkRosterShiftActions
                selectedCount={shifts.selectedIds.length}
                onClearSelection={shifts.clearSelection}
                onCopyWeek={() => shifts.setCopyOpen(true)}
                disabled={shifts.selectedIds.length === 0 && shifts.copyDefaultIds.length === 0}
              />
            ) : undefined
          }
        />
        <WorkRosterFilterBar
          companies={canCompany ? (companies?.items ?? []) : null}
          departments={departmentOptions}
          departmentAllLabel={departmentAllLabel(scope, ownDepartments.length)}
          showSearch={scope !== 'self'}
          companyId={companyId}
          departmentId={departmentId}
          //  Đổi pháp nhân thì phòng ban đang chọn có thể không thuộc pháp nhân mới → bỏ chọn, MỘT lượt URL.
          onCompanyChange={(id) =>
            setUrlParams({ company: id ? String(id) : null, department: null })
          }
          onDepartmentChange={(id) => setDepartment(id ? String(id) : '0')}
          search={search.value}
          onSearchChange={search.setValue}
        />
        {scope === 'self' && <p className="text-sm text-muted-foreground">Bạn đang xem lịch của chính mình.</p>}
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
            <WorkRosterDayList
              days={days}
              items={items}
              selectedISO={selectedISO}
              onSelect={setPickedISO}
              todayISO={todayISO}
              onEditRow={shifts.canArrange && selectedISO ? (item) => shifts.openCell(item, selectedISO) : undefined}
            />
          ) : (
            <WorkRosterGrid days={days} items={items} mode={mode} todayISO={todayISO} interaction={shifts.interaction} />
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

      {shifts.canArrange && (
        <>
          <WorkShiftDialog target={shifts.target} onClose={shifts.closeCell} days={days} items={items} todayISO={todayISO} />
          <WorkShiftCopyWeekDialog
            open={shifts.copyOpen}
            onClose={() => shifts.setCopyOpen(false)}
            targetWeekStart={range.from}
            employeeIds={copyIds}
            fromSelection={shifts.selectedIds.length > 0}
            ownDepartmentsOnly={isPersonalArranger}
            skipsPastDays={isPersonalArranger}
            nameOf={nameOf}
          />
        </>
      )}
    </PageContainer>
  )
}
