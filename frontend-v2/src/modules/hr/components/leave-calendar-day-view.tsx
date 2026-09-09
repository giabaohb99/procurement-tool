import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { QuickFilterField } from '@/shared/ui/quick-filter-sheet'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import {
  LEAVE_STATUS,
  LEAVE_STATUS_LABELS,
  type Holiday,
  type LeaveRequest,
} from '../types/leave'
import { holidayNamesOn, isWeekend, toISODate } from '../utils/calendar-grid'
import {
  ALL_OPTION,
  filterLeaveRows,
  isFiltering,
  leaveTypesIn,
} from '../utils/filter-leave-rows'
import { LeaveRowsFilterBar } from './leave-rows-filter-bar'
import {
  codeColumn,
  dateColumns,
  employeeColumn,
  leaveTypeColumn,
  reasonColumn,
  statusColumn,
} from './leave-request-columns'
import { LeaveRequestCard } from './leave-request-card'

interface LeaveCalendarDayViewProps {
  anchor: Date
  requestsOn: (iso: string) => LeaveRequest[]
  holidays: Holiday[]
}

/**
 * CHẾ ĐỘ NGÀY — **bảng**, không phải lưới thẻ.
 *
 * ⚠️ Bản đầu (04/09/2026) dựng mỗi người một tấm thẻ bốn dòng, và nó vỡ đúng ở
 * ca mà chế độ này sinh ra để phục vụ: hôm cả phòng nghỉ chung. Mười bốn tấm
 * thẻ lặp y hệt nhau — cùng loại nghỉ, cùng khoảng ngày, cùng lý do, cùng huy
 * hiệu «Chờ duyệt» — trong khi thứ duy nhất khác nhau giữa chúng là CÁI TÊN.
 * Thẻ hợp khi mỗi mục một vẻ; danh sách người cùng nghỉ một ngày thì ngược lại.
 *
 * Bảng thì đọc theo cột: liếc dọc một cột là so được cả mười bốn dòng, và cái
 * gì giống nhau thì tự xếp thẳng hàng chứ không lặp lại mười bốn lần. Dùng
 * `DataTable` như mọi màn danh sách khác của hệ nên có sẵn ẩn/hiện cột, kéo
 * giãn, nhớ bố cục.
 *
 * ⚠️ Lọc ở **phía màn hình**, không gọi lại API: dữ liệu của cả khoảng đang xem
 * đã nằm sẵn trong bộ nhớ (trang cha nạp một lượt rồi gom theo ngày), nên hỏi
 * lại backend cho một ngày là thừa một vòng mạng để lấy đúng thứ vừa có.
 *
 * Cột dùng lại `leave-request-columns` — cùng một tờ đơn thì cột phải giống màn
 * Đơn nghỉ phép, đừng khai một bộ riêng rồi hai chỗ trôi khác nhau.
 *
 * ⚠️ **Dưới 768px thì lại là THẺ** — và không mâu thuẫn với đoạn trên: lập luận
 * "bảng đọc theo cột" đứng được vì mắt liếc dọc được cả bảng cùng lúc. Trên máy
 * 393px không có "cùng lúc" nào cả, bảy cột bề rộng cứng chỉ hiện được hai cột
 * đầu và mọi cột còn lại nằm sau một thao tác cuộn ngang. Thẻ ở đó là hình dạng
 * duy nhất bày trọn một tờ đơn trong tầm mắt (`LeaveRequestCard`).
 */
export function LeaveCalendarDayView({
  anchor,
  requestsOn,
  holidays,
}: LeaveCalendarDayViewProps) {
  const navigate = useNavigate()
  const isMobile = useIsMobile()
  const [keyword, setKeyword] = useState('')
  const [status, setStatus] = useState(ALL_OPTION)
  const [typeId, setTypeId] = useState(ALL_OPTION)

  const iso = toISODate(anchor)
  const all = useMemo(() => requestsOn(iso), [requestsOn, iso])
  const names = holidayNamesOn(holidays, iso)

  const types = useMemo(() => leaveTypesIn(all), [all])

  const items = useMemo(() => {
    const rows = filterLeaveRows(all, { keyword, typeId })
    //  Lọc trạng thái là ô RIÊNG của màn này — hai màn hộp việc duyệt không có
    //  nó (mọi dòng ở đó cùng một trạng thái), nên nó không nằm ở phần dùng chung.
    return status === ALL_OPTION ? rows : rows.filter((r) => r.status === Number(status))
  }, [all, keyword, typeId, status])

  const approved = items.filter((r) => r.status === LEAVE_STATUS.APPROVED).length
  const pending = items.length - approved
  const filtering = isFiltering({ keyword, typeId }) || status !== ALL_OPTION

  const columns = useMemo<DataTableColumn<LeaveRequest>[]>(
    () => [
      employeeColumn(),
      statusColumn(),
      leaveTypeColumn(),
      {
        //  Cột này chỉ có nghĩa TRONG chế độ ngày nên khai tại chỗ, không đẩy
        //  vào bộ cột dùng chung: nó phụ thuộc ngày đang xem, mà bộ kia không
        //  biết gì về ngày nào cả.
        //
        //  Ngày đầu / ngày cuối là thứ quyết định có giao được việc cho người ta
        //  hay không: đơn kết thúc chiều nay khác hẳn đơn còn kéo thêm một tuần,
        //  mà cả hai đều "đang nghỉ hôm nay".
        key: 'position',
        header: 'Trong đợt nghỉ',
        cell: (r) => {
          if (r.from_date === r.to_date) return 'Nghỉ một ngày'
          if (r.from_date === iso) return 'Ngày đầu'
          if (r.to_date === iso) return 'Ngày cuối'
          return 'Đang giữa đợt'
        },
        width: 140,
      },
      ...dateColumns(),
      //  Mã đơn KHÔNG ghim ở đây — xem docstring của `codeColumn`.
      codeColumn({ pinned: false }),
      reasonColumn(),
    ],
    [iso],
  )

  //  Ô lọc trạng thái dựng MỘT LẦN rồi đặt vào một trong hai chỗ tùy khổ màn:
  //  hàng công cụ (khổ rộng) hoặc tờ trượt «Bộ lọc» (khổ hẹp). Dựng hai bản rồi
  //  ẩn bớt bằng `md:hidden` thì có hai ô cùng tên trong cây DOM.
  const statusSelect = (
    <Select value={status} onValueChange={setStatus}>
      <SelectTrigger className="w-full md:w-40" aria-label="Lọc theo trạng thái">
        <SelectValue placeholder="Trạng thái" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL_OPTION}>Mọi trạng thái</SelectItem>
        {/*  Lịch CHỈ hiện hai trạng thái này (xem `leave-calendar-page`), nên bày
             cả sáu ra là bốn lựa chọn dẫn tới bảng rỗng. */}
        <SelectItem value={String(LEAVE_STATUS.APPROVED)}>
          {LEAVE_STATUS_LABELS[LEAVE_STATUS.APPROVED]}
        </SelectItem>
        <SelectItem value={String(LEAVE_STATUS.PENDING)}>
          {LEAVE_STATUS_LABELS[LEAVE_STATUS.PENDING]}
        </SelectItem>
      </SelectContent>
    </Select>
  )

  //  Cụm đếm đầu người — cũng chỉ MỘT bản, nhưng đổi chỗ theo khổ màn: khổ rộng
  //  nó đứng ngay sau ô lọc (đọc thành KẾT QUẢ của bộ lọc vừa đặt), khổ hẹp thì
  //  hàng công cụ đã kín nên nó thành một dòng riêng ngay trên danh sách thẻ.
  const counts = items.length > 0 && (
    <div
      className={cn(
        'flex flex-wrap items-center gap-3 text-xs text-muted-foreground',
        !isMobile && 'border-l pl-3',
      )}
    >
      <span className="font-medium text-foreground">{items.length} người nghỉ</span>
      {approved > 0 && (
        <span className="flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-emerald-500" />
          {approved} đã duyệt
        </span>
      )}
      {/*  Số CHỜ DUYỆT tách riêng vì nó là số người *có thể* vẫn đi làm — người
           xếp việc cần biết đâu là chắc chắn, đâu là chưa. */}
      {pending > 0 && (
        <span className="flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-amber-500" />
          {pending} chờ duyệt
        </span>
      )}
    </div>
  )

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3">
      {(names.length > 0 || isWeekend(anchor)) && (
        <div className="shrink-0 rounded-md border border-rose-200 bg-rose-50/60 px-4 py-2.5 text-sm dark:border-rose-900 dark:bg-rose-950/20">
          <span className="font-medium text-rose-800 dark:text-rose-200">
            {names.length > 0 ? names.join(' · ') : 'Cuối tuần'}
          </span>
          <span className="ml-2 text-muted-foreground">— không tính vào ngày phép.</span>
        </div>
      )}

      {isMobile && counts}

      <DataTable
        fillHeight
        columns={columns}
        rows={items}
        getRowId={(r) => r.id}
        emptyMessage={
          filtering ? 'Không có ai khớp bộ lọc.' : 'Không ai nghỉ ngày này.'
        }
        storageKey="hr.leave-calendar-day"
        //  ⚠️ Phải khai CẢ HAI, đừng để `DataTable` tự suy: mặc định của nó là
        //  "URL còn param nào thì coi như đang lọc, bấm Xóa lọc là quét sạch
        //  param". Mà URL của màn này mang `mode` + `date` — hai thứ nói mình
        //  đang xem NGÀY NÀO, không phải bộ lọc. Không khai thì nút «Xóa lọc»
        //  hiện thường trực dù chưa lọc gì, và bấm vào là văng về lịch tháng của
        //  hôm nay. Bộ lọc thật ở đây nằm trong state cục bộ, nên dọn bằng tay.
        filtersActive={filtering}
        onResetFilters={() => {
          setKeyword('')
          setStatus(ALL_OPTION)
          setTypeId(ALL_OPTION)
        }}
        onRowClick={(r) => navigate(appRoutes.hr.leaveRequestDetail(r.id))}
        //  Khổ hẹp: thẻ thay bảng. Bảng này khai bảy cột với bề rộng cứng
        //  (~1000px), trên máy 393px người dùng chỉ thấy hai cột đầu và phải
        //  cuộn ngang mới biết người ta nghỉ mấy ngày.
        mobileCard={(r) => <LeaveRequestCard request={r} />}
        toolbar={
          <LeaveRowsFilterBar
            keyword={keyword}
            onKeywordChange={setKeyword}
            typeId={typeId}
            onTypeChange={setTypeId}
            types={types}
            extraFilters={<QuickFilterField label="Trạng thái">{statusSelect}</QuickFilterField>}
            extraFilterCount={status !== ALL_OPTION ? 1 : 0}
            onClearExtraFilters={() => setStatus(ALL_OPTION)}
          >
            {statusSelect}

            {/*  ⚠️ KHÔNG `ml-auto`. `DataTable` đã đặt `ml-auto` cho nhóm nút
                 Tải lại / Cột của nó, nên thêm một cái nữa là cụm đếm bị đẩy ra
                 lơ lửng giữa hàng. Đứng ngay sau ô lọc thì nó đọc thành KẾT QUẢ
                 của bộ lọc vừa đặt. */}
            {!isMobile && counts}
          </LeaveRowsFilterBar>
        }
      />
    </div>
  )
}
