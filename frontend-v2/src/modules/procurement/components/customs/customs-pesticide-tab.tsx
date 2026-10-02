// Mục «Thuốc BVTV» của Tra cứu thị trường (29/09/2026): danh mục thuốc bảo vệ thực vật được đăng
// ký tại Việt Nam — tra theo tên thuốc, hoạt chất, công ty hoặc số đăng ký; bấm một dòng xem phạm
// vi sử dụng. Nguồn: bản cào danhmuc.thuocbvtv.com, nạp lại bằng nút «Nạp danh mục».
//
// Bộ lọc nằm trên URL với tên RIÊNG (`pq`, `pstatus`, `pgroup`, `pbanned`) — duoc-CR-492: bấm một
// dòng là sang trang chi tiết, bấm lùi phải về đúng bộ lọc đang xem. Không dùng chung `q`: thanh
// lọc dòng hàng hải quan của các mục khác giữ `q` trên URL, dùng chung thì ô tìm thuốc bị ghi đè.
// Số trang vẫn là state cục bộ (về trang 1 khi quay lại) — đổi bộ lọc phải kéo trang về 1.
// Mặc định lọc «Còn hiệu lực» (đại ca chốt 29/09) — thuốc hết hiệu lực vẫn có, bỏ lọc là thấy.
import { Plus, Upload } from 'lucide-react'
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { DataTable } from '@/shared/data-table'
import { appRoutes } from '@/shared/constants/app-routes'
import { fromHere } from '@/shared/hooks/use-back-target'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useSetUrlParams, useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'

import {
  CUSTOMS_PESTICIDE_COLUMNS,
  PESTICIDE_TABLE_STORAGE_KEY,
} from '../../config/customs-pesticide-columns'
import {
  useCustomsPesticideOptions,
  useCustomsPesticides,
  usePesticidePermissions,
} from '../../hooks/use-customs-pesticides'
import { PESTICIDE_STATUS } from '../../types/customs-pesticide'
import {
  ALL_PESTICIDE_OPTIONS,
  BANNED_ONLY,
  buildPesticideParams,
  resolvePesticideEmptyMessage,
} from '../../utils/customs-pesticide'
import { emptyPesticideInput } from '../../utils/customs-pesticide-form'
import { CustomsPesticideExportMenu } from './customs-pesticide-export-menu'
import { CustomsPesticideFilterControls } from './customs-pesticide-filter-controls'
import { CustomsPesticideFormDialog } from './customs-pesticide-form-dialog'
import { CustomsPesticideImportDialog } from './customs-pesticide-import-dialog'

const DEFAULT_PAGE_SIZE = 50
const DEFAULT_STATUS = String(PESTICIDE_STATUS.active)

//  Quyền SỬA danh mục là khóa riêng `customs_pesticide` (duoc-CR-490); XEM theo `customs_price.read`
//  — trang cha đã gác quyền xem trước khi dựng mục này.
export function CustomsPesticideTab() {
  //  Sửa / xóa ở trang chi tiết; mục danh sách chỉ còn «Thêm thuốc» và «Nạp danh mục».
  const { canCreate, canImport, canExport } = usePesticidePermissions()
  const [creating, setCreating] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const search = useUrlSearchParam('pq')
  const keyword = search.value
  const debouncedKeyword = search.debouncedValue
  const [status, setStatus] = useUrlParamState('pstatus', DEFAULT_STATUS)
  const [pestGroup, setPestGroup] = useUrlParamState('pgroup', ALL_PESTICIDE_OPTIONS)
  //  01/10/2026 — lọc Lĩnh vực (backend đã có từ đầu, màn chưa bày); cột tra cứu ở trang chi tiết
  //  mở thẳng danh sách với tham số này.
  const [sector, setSector] = useUrlParamState('psector', ALL_PESTICIDE_OPTIONS)
  const [banned, setBanned] = useUrlParamState('pbanned', ALL_PESTICIDE_OPTIONS)
  const setUrlParams = useSetUrlParams()
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [importOpen, setImportOpen] = useState(false)

  //  Mang theo chỗ đang đứng (bộ lọc trên URL) để nút lùi của trang chi tiết quay về đúng đây.
  function openDetail(id: number) {
    navigate(appRoutes.procurement.customsPesticideDetail(id), { state: fromHere(location) })
  }

  const filters = { q: debouncedKeyword, status, pestGroup, sector, banned }
  const [page, setPage] = usePageResetOnFilterChange([
    debouncedKeyword,
    status,
    pestGroup,
    sector,
    banned,
  ])
  const options = useCustomsPesticideOptions()
  const list = useCustomsPesticides({ ...buildPesticideParams(filters), page, page_size: pageSize })
  const catalogTotal = options.data?.total ?? 0
  //  «Xóa lọc» khai tay: «xóa» nghĩa là về MẶC ĐỊNH (còn hiệu lực), không phải bỏ hết
  //  (docs/ui/table.md §3). Đặt bốn param trong MỘT lượt — gọi bốn setter liền tay thì lượt sau
  //  đọc URL cũ và ghi đè lượt trước (xem `useSetUrlParams`).
  const filtersActive =
    keyword !== '' ||
    status !== DEFAULT_STATUS ||
    pestGroup !== ALL_PESTICIDE_OPTIONS ||
    sector !== ALL_PESTICIDE_OPTIONS ||
    banned !== ALL_PESTICIDE_OPTIONS

  function resetFilters() {
    search.setValue('')
    setUrlParams({ pq: null, pstatus: null, pgroup: null, psector: null, pbanned: null })
  }

  return (
    <Card className="p-4">
      <DataTable
        columns={CUSTOMS_PESTICIDE_COLUMNS}
        rows={list.data?.items}
        getRowId={(row) => row.id}
        isLoading={list.isLoading}
        isError={list.isError}
        emptyMessage={resolvePesticideEmptyMessage(
          catalogTotal,
          canImport,
          banned === BANNED_ONLY ? options.data?.banned_rules : undefined,
        )}
        storageKey={PESTICIDE_TABLE_STORAGE_KEY}
        onRowClick={(row) => openDetail(row.id)}
        filtersActive={filtersActive}
        onResetFilters={resetFilters}
        //  Một hàng duy nhất: tìm → ba ô chọn → Nạp danh mục …… Xóa lọc · Tải lại · Cột
        //  (docs/ui/table.md §3). Ô chọn dùng `Select` có mục «Tất cả …» như mọi màn danh sách.
        toolbar={
          <>
            <CustomsPesticideFilterControls
              keyword={keyword}
              onKeywordChange={search.setValue}
              status={status}
              onStatusChange={setStatus}
              pestGroup={pestGroup}
              onPestGroupChange={setPestGroup}
              sector={sector}
              onSectorChange={setSector}
              banned={banned}
              onBannedChange={setBanned}
              options={options.data}
            />
            {canCreate && (
              <Button
                type="button"
                onClick={() => setCreating(true)}
              >
                <Plus className="size-4" />
                Thêm thuốc
              </Button>
            )}
            {canImport && (
              <Button type="button" variant="outline" onClick={() => setImportOpen(true)}>
                <Upload className="size-4" />
                Nạp danh mục
              </Button>
            )}
            {canExport && (
              <CustomsPesticideExportMenu
                filterParams={buildPesticideParams(filters)}
                page={page}
                pageSize={pageSize}
                pageRowCount={list.data?.items.length ?? 0}
                disabled={catalogTotal === 0}
              />
            )}
          </>
        }
        pagination={{
          page,
          pageSize,
          total: list.data?.total ?? 0,
          onPageChange: setPage,
          onPageSizeChange: (size) => {
            setPageSize(size)
            setPage(1)
          },
          unitLabel: 'thuốc',
        }}
      />

      {creating && (
        <CustomsPesticideFormDialog
          pesticideId={null}
          initial={emptyPesticideInput()}
          fromSource={false}
          onClose={() => setCreating(false)}
          onSaved={(saved) => {
            setCreating(false)
            openDetail(saved.id)
          }}
        />
      )}
      {importOpen && (
        <CustomsPesticideImportDialog
          currentTotal={catalogTotal}
          manualCount={options.data?.manual_count ?? 0}
          lastLoadedAt={options.data?.last_loaded_at ?? null}
          onClose={() => setImportOpen(false)}
        />
      )}
    </Card>
  )
}
