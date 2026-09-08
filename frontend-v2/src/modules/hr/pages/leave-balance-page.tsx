import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArchiveRestore, CalendarPlus, Search } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
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
import { cn } from '@/shared/utils/cn'
import { LeaveSectionTabs } from '../components/leave-section-tabs'
import {
  useAllocateLeaveBalance,
  useCloseLeaveYear,
  useLeaveBalances,
  useLeaveTypes,
} from '../hooks/use-leave'
import type { LeaveBalance } from '../types/leave'

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
        cell: (b) => (
          <DayCount
            value={b.remaining_days}
            alwaysShow
            className={cn(
              'font-semibold',
              b.remaining_days <= 0 ? 'text-destructive' : 'text-foreground',
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

  return (
    <PageContainer fill>
      <PageHeader
        title="Quỹ phép năm"
        description="Cấp phát, theo dõi và điều chỉnh số ngày phép của từng nhân sự."
        actions={
          <>
            {/*  Kết sổ đứng TRƯỚC và ở dạng nút phụ: nó chạy mỗi năm một lần,
                 còn Cấp quỹ là nút hằng ngày. Để hai nút cùng cỡ cùng màu thì
                 người ta bấm nhầm, mà nhầm ở đây là dời phép của cả công ty. */}
            {canCloseYear && (
              <Button variant="outline" onClick={closeYearNow} disabled={closeYear.isPending}>
                <ArchiveRestore className="size-4" />
                Kết sổ năm {Number(year) - 1}
              </Button>
            )}
            {canAllocate && (
              <Button
                onClick={() => allocate.mutate({ year: Number(year) })}
                disabled={allocate.isPending}
              >
                <CalendarPlus className="size-4" />
                Cấp quỹ năm {year}
              </Button>
            )}
          </>
        }
      />

      <LeaveSectionTabs />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
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
          onRowClick={(b) => navigate(appRoutes.hr.leaveBalanceDetail(b.id))}
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
              <div className="relative min-w-56 flex-1 md:max-w-xs">
                <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo tên hoặc mã nhân sự…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              <Select value={leaveTypeId} onValueChange={setLeaveTypeId}>
                <SelectTrigger className="w-44">
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

              {/*  Ô CHỌN chứ không phải ô nhập số: ô số cho gõ "20226" hay "0"
                   và bảng lập tức rỗng không rõ vì sao, lại còn có mũi tên tăng
                   giảm chạy từng năm một. */}
              <Select value={year} onValueChange={setYear}>
                <SelectTrigger className="w-32">
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
            </>
          }
        />
      </Card>

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
