import { useCallback, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { TriangleAlert } from 'lucide-react'

import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useClearUrlParams, useUrlParamState } from '@/shared/hooks/use-url-param-state'
import type { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { SearchField } from '@/shared/ui/search-field'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { useLeaveBalances, useLeaveTypes } from '../hooks/use-leave'
import { useLocalTableSort } from '../hooks/use-local-table-sort'
import {
  flattenLeaveBalanceGroups,
  groupLeaveBalances,
  leaveBalanceRowClass,
  type LeaveBalanceRow,
} from '../utils/group-leave-balances'
import { LIST_TOOLBAR_STICKY } from '../utils/list-sticky'
import { sortLeaveBalanceGroups } from '../utils/sort-leave-balance-groups'
import { buildLeaveBalanceColumns } from './leave-balance-columns'
import { LeaveBalanceRowCard } from './leave-balance-row-card'
import { LeaveBalanceYearSelect } from './leave-balance-year-select'

const ALL = 'all'

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

interface LeaveBalanceRowsTableProps {
  year: string
  onYearChange: (year: string) => void
  /** Ô tìm `?q=` — MỘT chủ ở màn cha, dùng chung hai thẻ (review L9). */
  search: ReturnType<typeof useUrlSearchParam>
}

/**
 * Thẻ "Theo dòng quỹ" của màn Quỹ phép năm (tách khỏi `leave-balance-page.tsx`, review L6 của duoc-CR-717).
 *
 * ⚠️ **Bảng GOM THEO NGƯỜI, loại nghỉ là dòng con** (19/09/2026). Trước đó bảng
 * bày phẳng mười một cột, một dòng cho mỗi (người × loại nghỉ). Hai chỗ hỏng:
 * ở màn 1600px bảng vẫn tràn và thứ bị đẩy ra ngoài mép phải đúng là cột "Còn
 * lại" — con số duy nhất người ta mở màn này để xem; còn công ty khai đủ tám
 * loại nghỉ thì bảng dài gấp tám lần số người và câu hỏi *"anh A còn mấy ngày"*
 * phải tự cộng tám dòng mới trả lời được. Luật gom nằm ở
 * `utils/group-leave-balances.ts`, cột ở `components/leave-balance-columns.tsx`.
 *
 * ⚠️ Thanh công cụ đi ĐÚNG KHUÔN màn Đơn nghỉ phép: ô tìm bên trái rồi tới các
 * ô chọn. Trước 03/09/2026 màn này chỉ có mỗi ô "Năm", nên một công ty vài trăm
 * người là vài chục trang cuộn tay để tìm một cái tên.
 */
export function LeaveBalanceRowsTable({ year, onYearChange, search }: LeaveBalanceRowsTableProps) {
  const navigate = useNavigate()
  const currentYear = String(new Date().getFullYear())
  const { value: keyword, setValue: setKeyword, debouncedValue } = search
  const [leaveTypeId, setLeaveTypeId] = useUrlParamState('leave_type_id', ALL)
  const clearUrlParams = useClearUrlParams()
  //  duoc-CR-748: bấm tiêu đề cột xếp các NHÓM NGƯỜI ngay ở trình duyệt (bảng đã nạp trọn năm) — giữ ở state, không
  //  lên URL: cùng trang còn thẻ Ma trận với bảng riêng của nó, hai bảng không tranh nhau một cặp `sort_by`.
  const sort = useLocalTableSort()
  //  Trang TỰ VỀ 1 khi đổi bộ lọc hoặc đổi thứ tự: kết quả mới thường ít hơn, giữ số trang cũ
  //  là rơi vào trang trống. Theo dõi giá trị tìm kiếm ĐÃ HOÃN, không theo ô
  //  nhập thô — kẻo mỗi ký tự gõ vào là một lần đặt lại trang.
  const [page, setPage] = usePageResetOnFilterChange([debouncedValue, year, leaveTypeId, sort.sortBy, sort.sortDir])
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const { data: typeData } = useLeaveTypes()

  //  Nhóm đang bung, giữ theo id NHÂN SỰ nên đổi trang rồi quay lại vẫn còn.
  const [expanded, setExpanded] = useState<ReadonlySet<number>>(() => new Set())
  const toggleGroup = useCallback((employeeId: number) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (!next.delete(employeeId)) next.add(employeeId)
      return next
    })
  }, [])

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

  //  Xếp TRƯỚC khi cắt trang — xếp trong một trang là người đứng đầu trang 2 trông như người đầu danh sách.
  const groups = useMemo(
    () => sortLeaveBalanceGroups(groupLeaveBalances(data?.items), sort.sortBy, sort.sortDir),
    [data, sort.sortBy, sort.sortDir],
  )
  //  Vượt trần `page_size` thì danh sách bị cắt cụt ở backend và mọi tổng đều
  //  thiếu. Nói ra chứ đừng để người dùng đọc một con số sai mà không biết.
  const truncated = (data?.total ?? 0) > (data?.items?.length ?? 0)
  const pageGroups = useMemo(() => groups.slice((page - 1) * pageSize, page * pageSize), [groups, page, pageSize])
  const rows = useMemo(() => flattenLeaveBalanceGroups(pageGroups, expanded), [pageGroups, expanded])
  const columns = useMemo(() => buildLeaveBalanceColumns({ expanded, onToggle: toggleGroup }), [expanded, toggleGroup])

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

  //  Hai ô chọn dựng MỘT LẦN rồi đặt vào một trong hai chỗ tùy khổ màn — xem ghi chú ở thanh công cụ.
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
  const yearSelect = <LeaveBalanceYearSelect value={year} onChange={onYearChange} />
  const filtering = Boolean(debouncedValue) || leaveTypeId !== ALL

  return (
    <>
      {truncated && (
        <p className="mb-2 flex items-center gap-2 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-foreground">
          <TriangleAlert className="size-4 shrink-0 text-warning" />
          Năm {year} có {data?.total} dòng quỹ, vượt trần {FULL_LIST_PAGE_SIZE} dòng tải về một lượt — bảng đang
          thiếu người và các con số tổng chưa đủ. Lọc bớt theo loại nghỉ hoặc tìm theo tên để xem đúng.
        </p>
      )}
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
            : `Chưa cấp quỹ phép năm ${year}. Bấm "Cấp quỹ năm ${year}" để tạo.`
        }
        //  ⚠️ Khóa `.v2`: bộ cột đổi hẳn (thêm "Tổng cấp", năm cột giải thích chuyển sang ẩn sẵn). Ai đã
        //  từng đụng menu "Cột" thì bản lưu trong localStorage THẮNG `defaultHidden`, nên giữ khóa cũ là họ
        //  vẫn thấy nguyên cái bảng tràn màn hình vừa đi sửa.
        storageKey="hr.leave-balances.v2"
        sortBy={sort.sortBy}
        sortDir={sort.sortDir}
        onSortChange={sort.onSortChange}
        toolbarClassName={LIST_TOOLBAR_STICKY}
        onRowClick={openRow}
        //  Ba mức nền: hàng thường · hàng CHA ĐANG BUNG (nổi bật) · hàng con. Luật ở `leaveBalanceRowClass`.
        rowClassName={(row) =>
          leaveBalanceRowClass(row, row.kind === 'group' && expanded.has(row.group.employeeId))
        }
        //  Khổ hẹp: thẻ thay bảng — bảng này tới mười một cột số, trên máy 393px chỉ thấy cột tên.
        mobileCard={(row) => (
          <LeaveBalanceRowCard row={row} expanded={row.kind === 'group' && expanded.has(row.group.employeeId)} />
        )}
        pagination={{
          page,
          pageSize,
          //  Đếm theo NGƯỜI, không theo dòng quỹ — đó là thứ bảng đang bày ra mỗi hàng gốc một cái.
          total: groups.length,
          onPageChange: setPage,
          onPageSizeChange: setPageSize,
          unitLabel: 'nhân sự',
        }}
        toolbar={
          <>
            {/*  ⚠️ Sàn `min-w-56` chỉ áp từ `md`: dưới ngưỡng đó ô tìm là `flex-1` với `flex-basis: 0` nên
                 nó không bao giờ ép nhóm nút bên phải xuống một hàng riêng. Câu gợi ý ngắn để ĐỌC HẾT được
                 ở khổ hẹp (ô còn 142px sau nút Bộ lọc và Tải lại). */}
            <SearchField
              value={keyword}
              onChange={setKeyword}
              placeholder="Tìm tên, mã nhân sự"
              className="md:max-w-xs md:min-w-56"
            />
            {/*  ⚠️ Huy hiệu trên nút "Bộ lọc" đếm CẢ Ô NĂM khi nó khác năm hiện tại: ở khổ hẹp ô năm nằm
                 khuất trong tờ trượt — không có dấu này thì người dùng xem quỹ 2024 và tưởng đang xem 2026. */}
            <QuickFilterSheet
              activeCount={(leaveTypeId !== ALL ? 1 : 0) + (year !== currentYear ? 1 : 0)}
              //  Một lượt ghi URL — gọi từng setter thì chỉ lần cuối ăn (kh-NT2-2b, `useClearUrlParams`).
              onClearAll={() => clearUrlParams(['leave_type_id', 'year'])}
            >
              <QuickFilterField label="Loại nghỉ">{typeSelect}</QuickFilterField>
              <QuickFilterField label="Năm">{yearSelect}</QuickFilterField>
            </QuickFilterSheet>
            {/*  Cùng hai ô chọn dựng hai lần (hàng ngang ở màn rộng · tờ trượt ở màn hẹp). State ở URL nên
                 hai bản luôn nói cùng một giá trị — khuôn của `survey-list-page`. */}
            <div className="hidden items-center gap-3 md:flex">
              {typeSelect}
              {yearSelect}
            </div>
          </>
        }
      />
    </>
  )
}
