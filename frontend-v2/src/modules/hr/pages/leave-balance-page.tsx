import { useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArchiveRestore, CalendarPlus } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useScrolled } from '@/shared/hooks/use-scrolled'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
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
import { cn } from '@/shared/utils/cn'
import { LeaveBalanceCard } from '../components/leave-balance-card'
import { LeaveSectionTabs } from '../components/leave-section-tabs'
import { LIST_SECTION_TOOLBAR_STICKY } from '../utils/list-sticky'
import {
  useAllocateLeaveBalance,
  useCloseLeaveYear,
  useLeaveBalances,
  useLeaveTypes,
} from '../hooks/use-leave'
import type { LeaveBalance } from '../types/leave'
import { hasQuota } from '../utils/leave-balance-quota'

const ALL = 'all'

//  Bao nhiêu năm bày ra ô chọn. Quỹ phép không tra ngược quá vài năm — cần xa
//  hơn thì đó là việc của báo cáo, không phải màn thao tác hằng ngày.
const YEAR_SPAN = 3

/**
 * QUỸ PHÉP NĂM — màn của phòng Nhân sự.
 *
 * Ba thao tác, cả ba đều là thao tác **đụng vào ngày phép của người khác**, nên
 * cả ba gác sau `leave_balance.create` / `write` chứ không đi chung khóa với
 * đơn nghỉ:
 *  · **Cấp quỹ năm** — chạy lại được, chỉ tạo dòng còn thiếu. Bấm hai lần không
 *    nhân đôi quỹ, và thêm người giữa năm thì bấm lại là họ có quỹ.
 *  · **Kết sổ cuối năm** (07/09/2026) — đẩy số dư năm cũ sang năm mới theo luật
 *    khai ở từng loại nghỉ (`year_end_mode`). Cũng chạy lại được: dòng đã kết
 *    sổ mang dấu `carried_out_days` nên lượt sau bỏ qua.
 *  · **Điều chỉnh tay** — ghi ĐÈ, bắt buộc có lý do, ghi vào dấu vết. Nằm ở
 *    TRANG CHI TIẾT (`/hr/leave-balances/:id`), không phải popup từ dòng: xem
 *    docstring của `leave-balance-detail-page.tsx`.
 *
 * ⚠️ Thanh công cụ đi ĐÚNG KHUÔN màn Đơn nghỉ phép: ô tìm bên trái rồi tới các
 * ô chọn. Trước 03/09/2026 màn này chỉ có mỗi ô «Năm», nên một công ty vài trăm
 * người là vài chục trang cuộn tay để tìm một cái tên.
 */
export function LeaveBalancePage() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const canAllocate = can('leave_balance', 'create')

  const currentYear = new Date().getFullYear()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [year, setYear] = useUrlParamState('year', String(currentYear))
  const [leaveTypeId, setLeaveTypeId] = useUrlParamState('leave_type_id', ALL)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  //  Dải ghim đầu trang đổ bóng khi có nội dung trôi bên dưới — xem
  //  `list-sticky.ts`. Đo ở khối bọc vì nó nằm cùng khung cuộn với hai dải.
  const stickyRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(stickyRef)

  const allocate = useAllocateLeaveBalance()
  const closeYear = useCloseLeaveYear()
  const { data: typeData } = useLeaveTypes()

  //  Kết sổ SỬA hai dòng quỹ đã có (trừ bên năm cũ, cộng bên năm mới) nên gác
  //  bằng `write` như cột điều chỉnh tay, không phải `create` như nút Cấp quỹ.
  const canCloseYear = can('leave_balance', 'write')

  //  Kết sổ năm TRƯỚC năm đang xem: số dư của năm vừa xong mới là thứ cần đẩy
  //  đi. Hỏi lại trước khi chạy — nó chạm tới quỹ của mọi người trong phạm vi,
  //  và câu hỏi là chỗ duy nhất nói ra rằng nó chỉ chuyển những loại nghỉ CÓ
  //  khai luật, chứ không phải mọi loại.
  const closeYearNow = async () => {
    const target = Number(year) - 1
    const ok = await confirm({
      title: `Kết sổ quỹ phép năm ${target}?`,
      message:
        `Số dư năm ${target} của những loại nghỉ có khai «Mang sang năm sau» hoặc ` +
        `«Quy đổi sang loại nghỉ khác» sẽ được đẩy sang năm ${target + 1}. ` +
        'Loại để mặc định «Hết năm là mất» thì không đụng tới. ' +
        'Chạy lại được: dòng đã kết sổ sẽ bị bỏ qua, không nhân đôi số ngày.',
      confirmLabel: 'Kết sổ',
      tone: 'default',
    })
    if (ok) closeYear.mutate({ year: target })
  }

  const params = useMemo<ListParams>(() => {
    const p: ListParams = { page, page_size: pageSize, year }
    if (debouncedValue) p.search = debouncedValue
    if (leaveTypeId !== ALL) p.leave_type_id = leaveTypeId
    return p
  }, [page, pageSize, year, debouncedValue, leaveTypeId])

  const { data, isLoading, isError } = useLeaveBalances(params)

  const years = useMemo(
    () => Array.from({ length: YEAR_SPAN + 1 }, (_, i) => String(currentYear + 1 - i)),
    [currentYear],
  )

  const columns = useMemo<DataTableColumn<LeaveBalance>[]>(
    () => [
      {
        key: 'employee_name',
        header: 'Nhân sự',
        cell: (b) => (
          <span className="font-medium">{b.employee_name || `#${b.employee_id}`}</span>
        ),
        width: 220,
        hideable: false,
        defaultPinned: true,
      },
      {
        key: 'leave_type_name',
        header: 'Loại nghỉ',
        cell: (b) => b.leave_type_name || `#${b.leave_type_id}`,
        width: 150,
      },
      {
        key: 'allocated_days',
        header: 'Hạn mức',
        cell: (b) => <DayCount value={b.allocated_days} />,
        width: 110,
        align: 'right',
      },
      {
        key: 'seniority_days',
        header: 'Thâm niên',
        //  Tách khỏi «Hạn mức» để màn hình giải thích được "12 + 2" thay vì
        //  trưng ra con số 14 không rõ từ đâu ra.
        cell: (b) => <DayCount value={b.seniority_days} signed />,
        width: 110,
        align: 'right',
      },
      {
        key: 'carried_days',
        header: 'Chuyển năm trước',
        cell: (b) => <DayCount value={b.carried_days} signed />,
        width: 150,
        align: 'right',
      },
      {
        key: 'carried_out_days',
        header: 'Đã chuyển đi',
        //  Phần đã mang sang năm sau lúc kết sổ. Nó ĐÃ bị trừ khỏi «Còn lại»,
        //  nên không có cột này thì số dư năm cũ tụt mà không dòng nào giải
        //  thích — và người xem sẽ đi tìm xem ai vừa nghỉ mấy ngày đó.
        cell: (b) => <DayCount value={b.carried_out_days} />,
        width: 130,
        align: 'right',
      },
      {
        key: 'carried_expired_days',
        header: 'Hết hạn',
        //  Phép mang sang quá hạn dùng thì mất. Cột này KHÔNG nằm trong công
        //  thức còn lại — nó chỉ nói ra chỗ số ngày đã đi đâu.
        cell: (b) => (
          <DayCount
            value={b.carried_expired_days}
            className="text-muted-foreground line-through"
          />
        ),
        width: 110,
        align: 'right',
      },
      {
        key: 'adjusted_days',
        header: 'Điều chỉnh tay',
        //  Cột DUY NHẤT mang được số âm — `signed` tự xử dấu, gắn `+` cứng ở
        //  đây sẽ ra "+-2".
        cell: (b) => <DayCount value={b.adjusted_days} signed />,
        width: 140,
        align: 'right',
      },
      {
        key: 'used_days',
        header: 'Đã nghỉ',
        cell: (b) => <DayCount value={b.used_days} />,
        width: 110,
        align: 'right',
      },
      {
        key: 'pending_days',
        header: 'Chờ duyệt',
        //  Hổ phách vì đây là ngày ĐANG GIỮ CHỖ: chưa nghỉ nhưng cũng không
        //  tiêu được nữa. Số 0 vẫn để mờ như mọi cột khác — tô cả cột vàng khè
        //  trong khi chẳng có gì đang chờ là màu mất hết nghĩa.
        cell: (b) => (
          <DayCount value={b.pending_days} className="text-amber-600 dark:text-amber-400" />
        ),
        width: 110,
        align: 'right',
      },
      {
        key: 'remaining_days',
        header: 'Còn lại',
        //  ⚠️ KHÔNG `text-primary`: primary là navy — đúng màu nút hành động
        //  chính — nên con số đọc ra như một cái link bấm được. Đây là cột người
        //  ta quét mắt tìm, đậm hơn là đủ. Hết phép thì tô đỏ, vì đó là thứ Nhân
        //  sự cần thấy ngay giữa một bảng toàn số.
        //
        //  ⚠️ Nhưng chỉ đỏ khi CÓ QUỸ mà tiêu hết. Loại nghỉ không cấp hạn mức
        //  (tang chế, cưới hỏi, nghỉ bù…) luôn còn 0 và chiếm phần lớn số dòng —
        //  tô đỏ hết thì màu đỏ mất nghĩa đúng chỗ nó cần có nghĩa. Xem `hasQuota`.
        cell: (b) => (
          <DayCount
            value={b.remaining_days}
            alwaysShow
            className={cn(
              'font-semibold',
              b.remaining_days > 0
                ? 'text-foreground'
                : hasQuota(b)
                  ? 'text-destructive'
                  : 'text-muted-foreground',
            )}
          />
        ),
        width: 110,
        align: 'right',
        hideable: false,
      },
    ],
    [],
  )

  //  Hai ô chọn dựng MỘT LẦN rồi đặt vào một trong hai chỗ tùy khổ màn — xem
  //  ghi chú ở thanh công cụ bên dưới.
  const typeSelect = (
    <Select value={leaveTypeId} onValueChange={setLeaveTypeId}>
      <SelectTrigger className="w-full md:w-44" aria-label="Lọc theo loại nghỉ">
        <SelectValue placeholder="Loại nghỉ" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả loại nghỉ</SelectItem>
        {(typeData?.items ?? []).map((t) => (
          <SelectItem key={t.id} value={String(t.id)}>
            {t.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  //  Ô CHỌN chứ không phải ô nhập số: ô số cho gõ "20226" hay "0" và bảng lập
  //  tức rỗng không rõ vì sao, lại còn có mũi tên tăng giảm chạy từng năm một.
  const yearSelect = (
    <Select value={year} onValueChange={setYear}>
      <SelectTrigger className="w-full md:w-32" aria-label="Chọn năm">
        <SelectValue placeholder="Năm" />
      </SelectTrigger>
      <SelectContent>
        {years.map((y) => (
          <SelectItem key={y} value={y}>
            Năm {y}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  return (
    //  ⚠️ `fill` chỉ bật từ `md`: ở khổ hẹp bảng biến thành danh sách thẻ dài,
    //  mà `fill` nhét nó vào một khe vài trăm pixel và biến thành cuộn LỒNG —
    //  vuốt trúng mép ngoài khe thì trang không nhúc nhích. Cùng bài học với
    //  `leave-request-list-page`.
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Quỹ phép năm"
        //  Dòng mô tả ẩn trên máy hẹp: câu giới thiệu, đọc một lần rồi thôi,
        //  nhưng chiếm hai dòng ở đầu MỌI lần mở màn.
        description={
          <span className="max-md:hidden">
            Cấp phát, theo dõi và điều chỉnh số ngày phép của từng nhân sự.
          </span>
        }
        actions={
          <>
            {/*  Kết sổ đứng TRƯỚC và ở dạng nút phụ: nó chạy mỗi năm một lần,
                 còn Cấp quỹ là nút hằng ngày. Để hai nút cùng cỡ cùng màu thì
                 người ta bấm nhầm, mà nhầm ở đây là dời phép của cả công ty.

                 ⚠️ Khổ hẹp: hai nút CHIA ĐÔI một hàng (`max-md:flex-1`) và rút
                 nhãn còn «Kết sổ 2025» / «Cấp quỹ 2026». Nhãn đầy đủ làm mỗi nút
                 chiếm trọn một hàng, tức 96px chỉ để bày hai việc mà phòng Nhân
                 sự bấm vài lần một NĂM — trong khi thứ người ta mở màn này để
                 xem bị đẩy xuống dưới nếp gấp.

                 ⚠️ Nhãn rút gọn giữ tới tận `lg`, không phải chỉ dưới `md`. Ở
                 dải 768–1024px (máy bảng, cửa sổ chia đôi màn) nhãn đầy đủ cộng
                 tiêu đề vượt bề ngang, nên cụm nút rớt xuống một hàng riêng và —
                 vì `PageHeader` canh phải — nó nằm nép mép phải chừa một khoảng
                 trắng bằng nửa hàng. Nhãn ngắn thì cả cụm ở lại cùng hàng với
                 tiêu đề. */}
            {canCloseYear && (
              <Button
                variant="outline"
                className="max-md:flex-1 max-md:px-2 max-md:text-xs"
                onClick={closeYearNow}
                disabled={closeYear.isPending}
              >
                <ArchiveRestore className="size-4" />
                <span className="lg:hidden">Kết sổ {Number(year) - 1}</span>
                <span className="max-lg:hidden">Kết sổ năm {Number(year) - 1}</span>
              </Button>
            )}
            {canAllocate && (
              <Button
                className="max-md:flex-1 max-md:px-2 max-md:text-xs"
                onClick={() => allocate.mutate({ year: Number(year) })}
                disabled={allocate.isPending}
              >
                <CalendarPlus className="size-4" />
                <span className="lg:hidden">Cấp quỹ {year}</span>
                <span className="max-lg:hidden">Cấp quỹ năm {year}</span>
              </Button>
            )}
          </>
        }
      />

      {/*  `group` + `data-scrolled` là đường dẫn tín hiệu «trang đã cuộn» xuống
           tới dải ghim nằm sâu bên trong (thanh công cụ do `DataTable` vẽ, tầng
           trang không với tới được bằng prop). Bóng đổ của dải đó đọc thuộc tính
           này — xem `list-sticky.ts`. */}
      <div
        ref={stickyRef}
        data-scrolled={scrolled ? '' : undefined}
        className="group flex min-h-0 flex-1 flex-col"
      >
        <LeaveSectionTabs sticky />

        <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-3 md:p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(b) => b.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage={
            debouncedValue || leaveTypeId !== ALL
              ? 'Không có dòng quỹ nào khớp bộ lọc.'
              : `Chưa cấp quỹ phép năm ${year}. Bấm «Cấp quỹ năm ${year}» để tạo.`
          }
          storageKey="hr.leave-balances"
          toolbarClassName={LIST_SECTION_TOOLBAR_STICKY}
          onRowClick={(b) => navigate(appRoutes.hr.leaveBalanceDetail(b.id))}
          //  Khổ hẹp: thẻ thay bảng — bảng này mười một cột, trên máy 393px chỉ
          //  thấy hai cột đầu và cả mười con số nằm sau một thao tác cuộn ngang.
          mobileCard={(b) => <LeaveBalanceCard balance={b} />}
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'dòng quỹ',
          }}
          toolbar={
            <>
              {/*  ⚠️ Sàn `min-w-56` chỉ áp từ `md`: dưới ngưỡng đó ô tìm là
                   `flex-1` với `flex-basis: 0` nên nó không bao giờ ép nhóm nút
                   bên phải xuống một hàng riêng.

                   Câu gợi ý ngắn để ĐỌC HẾT được ở khổ hẹp: ô còn 142px sau khi
                   chia chỗ cho nút Bộ lọc và nút Tải lại, bản cũ cần 206px nên
                   cụt thành «Tìm theo tên hoặc m». */}
              <SearchField
                value={keyword}
                onChange={setKeyword}
                placeholder="Tìm tên, mã nhân sự"
                className="md:min-w-56 md:max-w-xs"
              />

              {/*  ⚠️ Huy hiệu trên nút «Bộ lọc» đếm CẢ Ô NĂM khi nó khác năm hiện
                   tại. Năm là thứ quyết định mọi con số trên bảng, mà ở khổ hẹp
                   nó nằm khuất trong tờ trượt — không có dấu này thì người dùng
                   xem quỹ 2024 và tưởng đang xem 2026, rồi đi hỏi vì sao ai cũng
                   hết phép. */}
              <QuickFilterSheet
                activeCount={
                  (leaveTypeId !== ALL ? 1 : 0) + (year !== String(currentYear) ? 1 : 0)
                }
                onClearAll={() => {
                  setLeaveTypeId(ALL)
                  setYear(String(currentYear))
                }}
              >
                <QuickFilterField label="Loại nghỉ">{typeSelect}</QuickFilterField>
                <QuickFilterField label="Năm">{yearSelect}</QuickFilterField>
              </QuickFilterSheet>

              {/*  Cùng hai ô chọn dựng hai lần (hàng ngang ở màn rộng · tờ trượt
                   ở màn hẹp). State nằm ở màn cha nên hai bản luôn nói cùng một
                   giá trị — khuôn của `survey-list-page`, không phải trùng lặp
                   cần dọn. */}
              <div className="hidden items-center gap-3 md:flex">
                {typeSelect}
                {yearSelect}
              </div>
            </>
          }
        />
        </Card>
      </div>
    </PageContainer>
  )
}

/**
 * Một ô SỐ NGÀY trong bảng quỹ.
 *
 * ⚠️ Số `0` hiện thành dấu gạch mờ, không phải chữ "0". Bảng này có bảy cột số
 * mà bốn cột trong đó hầu như luôn bằng 0 (thâm niên, chuyển năm, điều chỉnh
 * tay) — in "0" và "+0" ra hết thì cả bảng đặc số, và mắt không còn nhặt ra
 * được ô nào thật sự có giá trị. Cột «Còn lại» thì `alwaysShow`: ở đó số 0 mang
 * nghĩa **hết phép**, đúng thứ phải đập vào mắt.
 */
function DayCount({
  value,
  signed = false,
  alwaysShow = false,
  className,
}: {
  value: number
  /** Thêm dấu `+` khi dương. Số âm tự mang dấu `-`, không ghép tay. */
  signed?: boolean
  alwaysShow?: boolean
  className?: string
}) {
  if (!value && !alwaysShow) {
    return <span className="text-muted-foreground/40">—</span>
  }
  const prefix = signed && value > 0 ? '+' : ''
  return <span className={cn('tabular-nums', className)}>{`${prefix}${value}`}</span>
}
