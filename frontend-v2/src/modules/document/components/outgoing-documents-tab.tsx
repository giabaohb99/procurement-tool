import { Loader2, Search, Sheet } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { downloadFile } from '@/core/api'
import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { ConditionalFilter, FilterProvider, useFilterQuery } from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { DOCUMENT_LIST_FILTER_FIELDS } from '../config/document-list-filter-fields'
import { useActiveDocumentTypes } from '../hooks/use-document-types'
import { useDocuments } from '../hooks/use-documents'
import { useMyDocumentTasks } from '../hooks/use-my-document-approvals'
import { STATUS_LABELS, type DocumentRecord } from '../types/document-record'
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
  const { can } = usePermission()
  const canCreate = can('document', 'create')
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [typeId, setTypeId] = useUrlParamState('type', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  //  Bung MỘT dòng tại một thời điểm: các bản riêng phải hỏi máy chủ, mà hook
  //  không gọi được trong vòng lặp. Mở dòng khác thì dòng đang mở tự đóng —
  //  cũng đúng thói quen dùng: người ta soi từng bản gốc một.
  const [dongDangBung, setDongDangBung] = useState<number | null>(null)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const documentTypes = useActiveDocumentTypes()
  //  Văn bản nào trong bảng đang chờ CHÍNH người đang xem duyệt — để đánh dấu
  //  dòng đó. Đọc lại hộp việc đã nạp sẵn cho nút trên thanh trên, không thêm
  //  vòng mạng nào.
  const { items: viecDuyetCuaToi } = useMyDocumentTasks()
  const choToiDuyet = useMemo(
    () => new Set(viecDuyetCuaToi.map((row) => row.entity_id)),
    [viecDuyetCuaToi],
  )
  //  Điều kiện của bộ lọc nâng cao, đã dịch sang query param cho backend.
  const { queryParams, queryKey } = useFilterQuery()
  //  Đổi bất kỳ điều kiện nào cũng phải về trang 1 — đang ở trang 5 mà lọc còn
  //  ba dòng thì màn hình trống trơn, người dùng tưởng không có kết quả.
  const [page, setPage] = usePageResetOnFilterChange([queryKey, debouncedValue, typeId, status])

  //  Điều kiện lọc gom một chỗ: bảng và nút Xuất Excel phải nhìn cùng một bộ,
  //  nếu không thì file tải về khác hẳn thứ đang hiện trên màn hình.
  const dieuKienLoc = {
    ...queryParams,
    q: debouncedValue.trim() || undefined,
    doc_type_id: typeId === ALL ? undefined : Number(typeId),
    status: status === ALL ? undefined : Number(status),
  }

  const { data, isLoading, isError } = useDocuments({
    ...dieuKienLoc,
    page,
    page_size: pageSize,
  })

  const [dangXuat, setDangXuat] = useState(false)

  async function xuatExcel() {
    setDangXuat(true)
    try {
      //  KHÔNG gửi `cols`: người dùng ẩn cột trên màn hình để nhìn cho gọn,
      //  còn file Excel thì gần như luôn muốn đủ cột để lọc lại trong Excel.
      const query = new URLSearchParams()
      for (const [khoa, giaTri] of Object.entries(dieuKienLoc)) {
        if (giaTri !== undefined && giaTri !== null && giaTri !== '') {
          query.set(khoa, String(giaTri))
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
  const { data: banRieng } = useDocuments({
    source_document_id: dongDangBung ?? undefined,
    page_size: 100,
  })

  const rows = useMemo(() => {
    const items = data?.items ?? []
    if (!dongDangBung) return items
    const con = (banRieng?.items ?? []).filter((row) => row.source_document_id === dongDangBung)

    return items.flatMap((row) => (row.id === dongDangBung ? [row, ...con] : [row]))
  }, [data?.items, banRieng?.items, dongDangBung])

  //  Bọc `useCallback` vì hook cột nhận nó vào mảng phụ thuộc của `useMemo`:
  //  hàm mới mỗi lần render là bộ cột dựng lại mỗi lần render.
  const doiDongDangBung = useCallback((id: number | null) => setDongDangBung(id), [])

  const columns = useOutgoingDocumentColumns({
    dongDangBung,
    setDongDangBung: doiDongDangBung,
    choToiDuyet,
    canCreate,
  })

  return (
    <Card className="flex min-h-0 flex-1 flex-col p-4">
      <DataTable
        columns={columns}
        rows={rows}
        getRowId={(row: DocumentRecord) => row.id}
        storageKey="document.records"
        fillHeight
        isLoading={isLoading}
        isError={isError}
        onRowClick={(row) => navigate(appRoutes.document.documentDetail(row.id))}
        emptyMessage="Chưa có văn bản nào khớp điều kiện đang lọc."
        pagination={{
          page,
          pageSize,
          total: data?.total ?? 0,
          onPageChange: setPage,
          onPageSizeChange: setPageSize,
          unitLabel: 'văn bản',
        }}
        toolbar={
          <>
            <div className="relative w-full max-w-xs">
              <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Tìm theo tên, số hiệu, số hiệu cũ, từ khóa…"
                value={keyword}
                onChange={(event) => {
                  setKeyword(event.target.value)
                  setPage(1)
                }}
              />
            </div>

            <Select
              value={typeId}
              onValueChange={(value) => {
                setTypeId(value)
                setPage(1)
              }}
            >
              <SelectTrigger className="w-48">
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

            <Select
              value={status}
              onValueChange={(value) => {
                setStatus(value)
                setPage(1)
              }}
            >
              <SelectTrigger className="w-44">
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

            <ConditionalFilter />

            {/*  Xuất Excel nằm ở THANH CÔNG CỤ chứ không ở đầu trang: file tải
                 về đúng bằng bộ điều kiện đang lọc, nên nó thuộc về hàng chứa
                 mấy ô lọc — mà đầu trang giờ là của cả hai tab. */}
            <PermissionGate entity="document" action="export">
              <Button variant="outline" onClick={() => void xuatExcel()} disabled={dangXuat}>
                {dangXuat ? <Loader2 className="size-4 animate-spin" /> : <Sheet className="size-4" />}
                Xuất Excel
              </Button>
            </PermissionGate>
          </>
        }
      />
    </Card>
  )
}
