import { useCallback, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArchiveRestore, CalendarPlus, TriangleAlert } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
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
import { buildLeaveBalanceColumns } from '../components/leave-balance-columns'
import { LeaveBalanceRowCard } from '../components/leave-balance-row-card'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'
import {
  useAllocateLeaveBalance,
  useCloseLeaveYear,
  useLeaveBalances,
  useLeaveTypes,
} from '../hooks/use-leave'
import {
  flattenLeaveBalanceGroups,
  groupLeaveBalances,
  leaveBalanceRowClass,
  type LeaveBalanceRow,
} from '../utils/group-leave-balances'

const ALL = 'all'

//  Bao nhiêu năm bày ra ô chọn. Quỹ phép không tra ngược quá vài năm — cần xa
//  hơn thì đó là việc của báo cáo, không phải màn thao tác hằng ngày.
const YEAR_SPAN = 3

/**
 * Kéo TRỌN danh sách quỹ của năm đang xem về một lượt.
 *
 * ⚠️ Bảng gom theo NGƯỜI nên phân trang phải đếm theo người, mà backend chỉ cắt
 * trang theo DÒNG QUỸ — để backend cắt thì một nhân sự tám loại nghỉ có thể bị
 * xé đôi qua hai trang và tổng của họ sai ở cả hai. 5000 là trần `page_size`
 * của `core/base_controller.py`; công ty 262 người × 8 loại nghỉ ≈ 2100 dòng,
 * còn dư gấp đôi. Vượt trần thì `truncated` bên dưới nói ra, không nuốt.
 */
const FULL_LIST_PAGE_SIZE = 5000

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
 * ⚠️ **Bảng GOM THEO NGƯỜI, loại nghỉ là dòng con** (19/09/2026). Trước đó bảng
 * bày phẳng mười một cột, một dòng cho mỗi (người × loại nghỉ). Hai chỗ hỏng:
 * ở màn 1600px bảng vẫn tràn và thứ bị đẩy ra ngoài mép phải đúng là cột «Còn
 * lại» — con số duy nhất người ta mở màn này để xem; còn công ty khai đủ tám
 * loại nghỉ thì bảng dài gấp tám lần số người và câu hỏi *"anh A còn mấy ngày"*
 * phải tự cộng tám dòng mới trả lời được. Luật gom nằm ở
 * `utils/group-leave-balances.ts`, cột ở `components/leave-balance-columns.tsx`.
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
  //  Trang TỰ VỀ 1 khi đổi bộ lọc: kết quả mới thường ít hơn, giữ số trang cũ
  //  là rơi vào trang trống. Theo dõi giá trị tìm kiếm ĐÃ HOÃN, không theo ô
  //  nhập thô — kẻo mỗi ký tự gõ vào là một lần đặt lại trang.
  const [page, setPage] = usePageResetOnFilterChange([debouncedValue, year, leaveTypeId])
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  //  Nhóm đang bung, giữ theo id NHÂN SỰ nên đổi trang rồi quay lại vẫn còn.
  const [expanded, setExpanded] = useState<ReadonlySet<number>>(() => new Set())
  const toggleGroup = useCallback((employeeId: number) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (!next.delete(employeeId)) next.add(employeeId)
      return next
    })
  }, [])

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

  //  KHÔNG có `page` trong params: trang cắt ở client theo NGƯỜI (xem
  //  `FULL_LIST_PAGE_SIZE`). Lọc và tìm kiếm vẫn ở backend — `apply_scope` chạy
  //  ở đó, và tìm theo tên nhân sự cần bảng `tab_employee`.
  const params = useMemo<ListParams>(() => {
    const p: ListParams = { page: 1, page_size: FULL_LIST_PAGE_SIZE, year }
    if (debouncedValue) p.search = debouncedValue
    if (leaveTypeId !== ALL) p.leave_type_id = leaveTypeId
    return p
  }, [year, debouncedValue, leaveTypeId])

  const { data, isLoading, isError } = useLeaveBalances(params)

  const groups = useMemo(() => groupLeaveBalances(data?.items), [data])
  //  Vượt trần `page_size` thì danh sách bị cắt cụt ở backend và mọi tổng đều
  //  thiếu. Nói ra chứ đừng để người dùng đọc một con số sai mà không biết.
  const truncated = (data?.total ?? 0) > (data?.items?.length ?? 0)

  const pageGroups = useMemo(
    () => groups.slice((page - 1) * pageSize, page * pageSize),
    [groups, page, pageSize],
  )
  const rows = useMemo(
    () => flattenLeaveBalanceGroups(pageGroups, expanded),
    [pageGroups, expanded],
  )

  const years = useMemo(
    () => Array.from({ length: YEAR_SPAN + 1 }, (_, i) => String(currentYear + 1 - i)),
    [currentYear],
  )

  const columns = useMemo(
    () => buildLeaveBalanceColumns({ expanded, onToggle: toggleGroup }),
    [expanded, toggleGroup],
  )

  //  Bấm vào hàng: hàng NHÓM thì bung/thu (nó không có dòng quỹ nào để mở),
  //  hàng còn lại mở trang chi tiết đúng dòng quỹ đó.
  const openRow = useCallback(
    (row: LeaveBalanceRow) => {
      if (row.kind === 'group') {
        toggleGroup(row.group.employeeId)
        return
      }
      navigate(appRoutes.hr.leaveBalanceDetail(row.balance.id))
    },
    [navigate, toggleGroup],
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

  const filtering = Boolean(debouncedValue) || leaveTypeId !== ALL

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
        {truncated && (
          <p className="mb-2 flex items-center gap-2 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-foreground">
            <TriangleAlert className="size-4 shrink-0 text-warning" />
            Năm {year} có {data?.total} dòng quỹ, vượt trần {FULL_LIST_PAGE_SIZE} dòng tải về
            một lượt — bảng đang thiếu người và các con số tổng chưa đủ. Lọc bớt theo loại nghỉ
            hoặc tìm theo tên để xem đúng.
          </p>
        )}

        <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-3 md:p-4">
          <DataTable
            fillHeight
            columns={columns}
            rows={rows}
            getRowId={(row) => row.id}
            isLoading={isLoading}
            isError={isError}
            emptyMessage={
              filtering
                ? 'Không có dòng quỹ nào khớp bộ lọc.'
                : `Chưa cấp quỹ phép năm ${year}. Bấm «Cấp quỹ năm ${year}» để tạo.`
            }
            //  ⚠️ Khóa `.v2`: bộ cột đổi hẳn (thêm «Tổng cấp», năm cột giải
            //  thích chuyển sang ẩn sẵn). Ai đã từng đụng menu «Cột» thì bản lưu
            //  trong localStorage THẮNG `defaultHidden`, nên giữ khóa cũ là họ
            //  vẫn thấy nguyên cái bảng tràn màn hình vừa đi sửa.
            storageKey="hr.leave-balances.v2"
            toolbarClassName={LIST_TOOLBAR_STICKY_TOP}
            onRowClick={openRow}
            //  Ba mức nền: hàng thường · hàng CHA ĐANG BUNG (nổi bật) · hàng
            //  con. Luật và lý do ở `leaveBalanceRowClass`.
            rowClassName={(row) =>
              leaveBalanceRowClass(
                row,
                row.kind === 'group' && expanded.has(row.group.employeeId),
              )
            }
            //  Khổ hẹp: thẻ thay bảng — bảng này tới mười một cột số, trên máy
            //  393px chỉ thấy cột tên và cả bảng số nằm sau một thao tác cuộn
            //  ngang.
            mobileCard={(row) => (
              <LeaveBalanceRowCard
                row={row}
                expanded={row.kind === 'group' && expanded.has(row.group.employeeId)}
              />
            )}
            pagination={{
              page,
              pageSize,
              //  Đếm theo NGƯỜI, không theo dòng quỹ — đó là thứ bảng đang bày
              //  ra mỗi hàng gốc một cái.
              total: groups.length,
              onPageChange: setPage,
              onPageSizeChange: setPageSize,
              unitLabel: 'nhân sự',
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
