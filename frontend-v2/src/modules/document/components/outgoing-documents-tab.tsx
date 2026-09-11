import { Loader2, Sheet } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { downloadFile } from '@/core/api'
import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
  useFilterQuery,
} from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { LIST_TOOLBAR_STICKY } from '@/modules/hr/utils/list-sticky'
import { cn } from '@/shared/utils/cn'
import { AdvancedFilterSection } from '@/shared/ui/advanced-filter-section'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { SearchField } from '@/shared/ui/search-field'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { DocumentCard } from './document-card'
import { DOCUMENT_LIST_FILTER_FIELDS } from '../config/document-list-filter-fields'
import { useActiveDocumentTypes } from '../hooks/use-document-types'
import { useDocuments } from '../hooks/use-documents'
import { useMyDocumentTasks } from '../hooks/use-my-document-approvals'
import { STATUS_LABELS, type DocumentRecord } from '../types/document-record'
import { usePrefetchDocument } from '../hooks/use-prefetch-document'
import { useOutgoingDocumentColumns } from './outgoing-document-columns'

const ALL = 'all'

const FILTER_CONFIG = {
  fields: DOCUMENT_LIST_FILTER_FIELDS,
  allowConjunctionToggle: true,
  //  Ba ô trên thanh công cụ cộng với tab đang mở. Thiếu tên nào ở đây là bấm
  //  "Áp dụng" ở bộ lọc nâng cao xong mất luôn ô đó (riêng `tab` thì màn hình
  //  nhảy về tab kia).
  preserveParams: ['q', 'type', 'status', 'tab'],
}

export function OutgoingDocumentsTab() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <OutgoingDocumentsContent />
    </FilterProvider>
  )
}

/**
 * VĂN BẢN ĐI — nguyên màn «Văn bản» cũ, nay là tab mặc định của màn Văn bản.
 *
 * ⚠️ Không có cột hướng nào trong dữ liệu cả: "đi" ở đây nghĩa là **danh sách
 * văn bản trong tầm đọc của người dùng** (`/api/documents`), đối lại với tab
 * «đến» hỏi `/api/documents/applies-to-me` — văn bản tôi phải làm theo. Hai
 * hướng = hai màn cũ, không phải hai giá trị của một trường.
 *
 * Tìm kiếm và phân trang chạy ở BACKEND, không nạp hết về rồi lọc tại trình
 * duyệt: ngoài chuyện bảng sẽ lên vài chục nghìn dòng, lọc ở client nghĩa là
 * máy người dùng phải nhận về cả những văn bản họ không được xem. Ô tìm chấp
 * nhận cả **số hiệu cũ của bản giấy** (C12).
 */
function OutgoingDocumentsContent() {
  const navigate = useNavigate()
  const prefetchDocument = usePrefetchDocument()
  const { can } = usePermission()
  const canCreate = can('document', 'create')
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [typeId, setTypeId] = useUrlParamState('type', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  //  Bung MỘT dòng tại một thời điểm: các bản riêng phải hỏi máy chủ, mà hook
  //  không gọi được trong vòng lặp. Mở dòng khác thì dòng đang mở tự đóng —
  //  cũng đúng thói quen dùng: người ta soi từng bản gốc một.
  const [expandedRow, setExpandedRow] = useState<number | null>(null)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const documentTypes = useActiveDocumentTypes()
  //  Văn bản nào trong bảng đang chờ CHÍNH người đang xem duyệt — để đánh dấu
  //  dòng đó. Đọc lại hộp việc đã nạp sẵn cho nút trên thanh trên, không thêm
  //  vòng mạng nào.
  const { items: myApprovalTasks } = useMyDocumentTasks()
  const awaitingMyApproval = useMemo(
    () => new Set(myApprovalTasks.map((row) => row.entity_id)),
    [myApprovalTasks],
  )
  //  Điều kiện của bộ lọc nâng cao, đã dịch sang query param cho backend.
  const { queryParams, queryKey } = useFilterQuery()
  //  Cùng một bộ lọc nâng cao, ở khổ hẹp mở bằng tờ trượt thay vì popover — nên
  //  màn này cần cả `apply`/`reset`/`activeCount` chứ không chỉ query param.
  const filter = useFilterContext()
  //  Đổi bất kỳ điều kiện nào cũng phải về trang 1 — đang ở trang 5 mà lọc còn
  //  ba dòng thì màn hình trống trơn, người dùng tưởng không có kết quả.
  const [page, setPage] = usePageResetOnFilterChange([queryKey, debouncedValue, typeId, status])

  //  Điều kiện lọc gom một chỗ: bảng và nút Xuất Excel phải nhìn cùng một bộ,
  //  nếu không thì file tải về khác hẳn thứ đang hiện trên màn hình.
  const filterParams = {
    ...queryParams,
    q: debouncedValue.trim() || undefined,
    doc_type_id: typeId === ALL ? undefined : Number(typeId),
    status: status === ALL ? undefined : Number(status),
  }

  const { data, isLoading, isError } = useDocuments({
    ...filterParams,
    page,
    page_size: pageSize,
  })

  const [dangXuat, setDangXuat] = useState(false)

  async function exportExcel() {
    setDangXuat(true)
    try {
      //  KHÔNG gửi `cols`: người dùng ẩn cột trên màn hình để nhìn cho gọn,
      //  còn file Excel thì gần như luôn muốn đủ cột để lọc lại trong Excel.
      const query = new URLSearchParams()
      for (const [khoa, value] of Object.entries(filterParams)) {
        if (value !== undefined && value !== null && value !== '') {
          query.set(khoa, String(value))
        }
      }
      const homNay = new Date().toISOString().slice(0, 10)
      await downloadFile(
        `/api/documents/export/xlsx?${query.toString()}`,
        `danh-sach-van-ban-${homNay}.xlsx`,
      )
    } catch {
      toast.error('Không xuất được danh sách. Thử lọc bớt rồi xuất lại.')
    } finally {
      setDangXuat(false)
    }
  }

  //  Các BẢN RIÊNG của dòng đang bung. Backend giấu chúng khỏi danh sách chung
  //  (xem `an_ban_rieng_co_goc_xem_duoc`) nên phải hỏi đích danh theo bản gốc.
  const { data: privateCopies } = useDocuments({
    source_document_id: expandedRow ?? undefined,
    page_size: 100,
  })

  const rows = useMemo(() => {
    const items = data?.items ?? []
    if (!expandedRow) return items
    const con = (privateCopies?.items ?? []).filter((row) => row.source_document_id === expandedRow)

    return items.flatMap((row) => (row.id === expandedRow ? [row, ...con] : [row]))
  }, [data?.items, privateCopies?.items, expandedRow])

  //  Bọc `useCallback` vì hook cột nhận nó vào mảng phụ thuộc của `useMemo`:
  //  hàm mới mỗi lần render là bộ cột dựng lại mỗi lần render.
  const handleExpandRow = useCallback((id: number | null) => setExpandedRow(id), [])

  const columns = useOutgoingDocumentColumns({
    expandedRow,
    setExpandedRow: handleExpandRow,
    awaitingMyApproval,
    canCreate,
  })

  //  ⚠️ Hai ô chọn dựng MỘT LẦN rồi dùng cho cả hai khổ (hàng ngang ở màn rộng ·
  //  tờ trượt ở màn hẹp). Chép hai bản là hai khổ màn lọc ra hai kết quả khác
  //  nhau mà không chỗ nào báo — đúng bài học `buildFields` của duoc-CR-364.
  //  `w-full md:w-48`: trong tờ trượt ô trải hết bề ngang, trên thanh công cụ nó
  //  về lại bề rộng cũ.
  const typeSelect = (
    <Select
      value={typeId}
      onValueChange={(value) => {
        setTypeId(value)
        setPage(1)
      }}
    >
      <SelectTrigger className="w-full md:w-48" aria-label="Lọc theo loại văn bản">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả loại</SelectItem>
        {documentTypes.map((type) => (
          <SelectItem key={type.id} value={String(type.id)}>
            {type.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const statusSelect = (
    <Select
      value={status}
      onValueChange={(value) => {
        setStatus(value)
        setPage(1)
      }}
    >
      <SelectTrigger className="w-full md:w-44" aria-label="Lọc theo trạng thái">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
        {Object.entries(STATUS_LABELS).map(([value, label]) => (
          <SelectItem key={value} value={value}>
            {label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  return (
    //  ⚠️ `p-3` ở khổ hẹp là BẮT BUỘC, không phải chuyện thẩm mỹ: lề âm của dải
    //  thanh công cụ ghim (`-mx-3 -mt-3` trong `LIST_TOOLBAR_STICKY`) tính theo
    //  đúng đệm này. Để `p-4` thì nền của dải hụt 4px mỗi bên và thẻ cuộn qua
    //  lộ ra ở hai khe đó.
    //
    //  `min-w-0`: `TabsContent` là hộp flex, mà ô flex mặc định `min-width:auto`
    //  nên thẻ không co xuống dưới bề rộng tự nhiên của bảng bên trong (~1934px).
    //  Thiếu nó thì CẢ TRANG trượt ngang ở khổ hẹp.
    <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-3 md:p-4">
      <DataTable
        columns={columns}
        rows={rows}
        getRowId={(row: DocumentRecord) => row.id}
        storageKey="document.records"
        fillHeight
        //  ⚠️ `max-md:gap-2` — khe 12px của `DataTable` là cỡ cho hàng có
        //  CHỮ; hàng này ở khổ hẹp là ô tìm cộng ba nút biểu tượng, mà cụm nút
        //  biểu tượng thì 8px là khe quen thuộc. 4px × 3 khe = 12px, đúng phần
        //  còn thiếu để câu gợi ý vừa trọn ô ở 360px.
        toolbarClassName={cn(LIST_TOOLBAR_STICKY, 'max-md:gap-2')}
        //  Ô tìm chiếm trọn hàng đầu ở khổ hẹp, nên hàng nút còn lại dư chỗ và
        //  `ml-auto` mặc định xé nó thành hai mẩu cách nhau 162px. Dồn liền một
        //  cụm — xem `DataTableProps.toolbarActionsClassName`.
        toolbarActionsClassName="max-md:ml-0"
        isLoading={isLoading}
        isError={isError}
        onRowClick={(row) => navigate(appRoutes.document.documentDetail(row.id))}
        //  Rê chuột là nạp trước dữ liệu chi tiết — xem `usePrefetchDocument`.
        onRowHover={(row) => prefetchDocument(row.id)}
        emptyMessage="Chưa có văn bản nào khớp điều kiện đang lọc."
        pagination={{
          page,
          pageSize,
          total: data?.total ?? 0,
          onPageChange: setPage,
          onPageSizeChange: setPageSize,
          unitLabel: 'văn bản',
        }}
        //  Khổ hẹp: THẺ thay bảng — xem `DocumentCard`.
        mobileCard={(row: DocumentRecord) => (
          <DocumentCard doc={row} awaitingMyApproval={awaitingMyApproval.has(row.id)} showOrigin />
        )}
        toolbar={
          <>
            {/*  ⚠️ **MỘT HÀNG ở khổ hẹp** (khách chốt 11/09/2026) — trước đây ô
                 tìm chiếm trọn hàng đầu và bốn khối (tìm · Bộ lọc · Export · Tải
                 lại) rơi xuống hàng thứ hai. Đổi lại vì thanh này **ghim theo
                 cuộn**: mỗi hàng thừa là 48px đứng yên vĩnh viễn trên màn 852px,
                 trả đi trả lại suốt buổi đọc danh sách.

                 Số học của hàng đó rất sát, nên hai vế dưới đây đi kèm nhau chứ
                 không phải làm đẹp thêm — đo ở 393px, bề ngang dùng được 335px:
                 - **`iconOnly`** rút «Bộ lọc» từ 80px còn 36px. Không có vế này
                   thì ô tìm chỉ còn 141px, tức 93px cho chữ — không đủ cho cả
                   câu gợi ý ngắn nhất.
                 - **`placeholderShort`** vì ngay cả khi đã rút nút, ô tìm được
                   185px ≈ 137px chữ, mà câu đủ cần **171px**: trình duyệt sẽ xén
                   thành «Tìm tên, số hiệu, từ k…» — mất đúng chữ *từ khóa*, thứ
                   người dùng chưa đoán được. Câu ngắn 115px thì vừa, và ở 360px
                   (ô còn 152px ≈ 104px chữ) vẫn vừa.
                 Bỏ một trong hai là hàng lại vỡ. Từ `md` trở lên cả hai tắt: nút
                 «Bộ lọc» ẩn hẳn (desktop dùng `ConditionalFilter`) và câu gợi ý
                 về bản đủ. */}
            <SearchField
              value={keyword}
              onChange={(value) => {
                setKeyword(value)
                setPage(1)
              }}
              placeholder="Tìm tên, số hiệu, từ khóa…"
              placeholderShort="Tìm tên, số hiệu…"
              className="md:min-w-56 md:max-w-xs"
            />

            {/*  ⚠️ `activeCount` cộng CẢ HAI tầng lọc — ô nhanh và điều kiện nâng
                 cao — vì dưới 768px cả hai nay nằm sau đúng một nút này. Đếm
                 thiếu một tầng thì người dùng thấy nút không có dấu gì mà danh
                 sách vẫn đang bị lọc, rồi đi tìm lỗi ở dữ liệu.

                 «Đang lọc» = KHÁC mặc định chứ không phải «có giá trị»: mặc định
                 của hai ô là `all` chứ không rỗng, đếm kiểu kia thì nút lúc nào
                 cũng báo đang lọc (bài học duoc-CR-364). */}
            <QuickFilterSheet
              iconOnly
              activeCount={
                (typeId !== ALL ? 1 : 0) + (status !== ALL ? 1 : 0) + filter.activeCount
              }
              onClearAll={() => {
                setTypeId(ALL)
                setStatus(ALL)
                setPage(1)
                filter.reset()
              }}
              onApply={filter.apply}
            >
              <QuickFilterField label="Loại văn bản">{typeSelect}</QuickFilterField>
              <QuickFilterField label="Trạng thái">{statusSelect}</QuickFilterField>
              <AdvancedFilterSection />
            </QuickFilterSheet>

            {/*  ⚠️ `md:contents` chứ KHÔNG `md:flex`: bọc cụm lọc trong một thẻ
                 flex riêng thì cả cụm là MỘT ô của thanh công cụ — không đủ chỗ
                 là nó rớt nguyên khối xuống dòng dưới, để lại khoảng trống dài
                 bên phải ô tìm. `display: contents` cho từng ô thành ô trực tiếp
                 của thanh công cụ nên chúng xếp kín từng dòng.

                 `ConditionalFilter` nằm TRONG đây vì popover của nó neo vào nút,
                 mà ở 390px tấm `95vw` bung ra che gần hết màn và vẫn không đủ
                 ngang cho một hàng điều kiện — khổ hẹp đi bằng `AdvancedFilterSection`
                 trong tờ trượt ở trên. */}
            <div className="hidden md:contents">
              {typeSelect}
              {statusSelect}
              <ConditionalFilter />
            </div>

            {/*  Nút xuất nằm ở THANH CÔNG CỤ chứ không ở đầu trang: file tải
                 về đúng bằng bộ điều kiện đang lọc, nên nó thuộc về hàng chứa
                 mấy ô lọc — mà đầu trang giờ là của cả hai tab.
                 Nhãn «Export» là chữ khách chọn (25/08/2026), không phải sót
                 dịch — đừng "sửa" về «Xuất Excel». Tên tệp tải về vẫn giữ
                 tiếng Việt không dấu.

                 Khổ hẹp rút còn biểu tượng: chữ «Export» ăn ~60px của một hàng
                 chỉ vừa đúng ba khối. `aria-label` bù lại tên đọc được, nếu
                 không trình đọc màn hình gặp một nút chỉ có hình. */}
            <PermissionGate entity="document" action="export">
              <Button
                variant="outline"
                onClick={() => void exportExcel()}
                disabled={dangXuat}
                aria-label="Export danh sách văn bản ra Excel"
                //  ⚠️ `max-md:size-9 max-md:p-0` — ở khổ hẹp nút này chỉ còn
                //  BIỂU TƯỢNG, nên nó phải vuông 36px như hai nút biểu tượng
                //  đứng cạnh (Bộ lọc · Tải lại). Để nguyên cỡ mặc định thì đệm
                //  `px-4` vẫn còn và nút rộng **42px** — lệch 6px giữa ba nút
                //  giống hệt nhau về hình, và 6px đó đúng bằng phần thiếu để câu
                //  gợi ý của ô tìm vừa một hàng ở 360px.
                className="shrink-0 max-md:size-9 max-md:p-0"
              >
                {dangXuat ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Sheet className="size-4" />
                )}
                <span className="max-md:hidden">Export</span>
              </Button>
            </PermissionGate>
          </>
        }
      />
    </Card>
  )
}
