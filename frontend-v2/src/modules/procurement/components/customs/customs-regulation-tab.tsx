// Mục «Pháp lý» của Tra cứu thị trường (29/09/2026): bảng DUYỆT toàn bộ danh mục hóa chất theo
// văn bản — hoạt chất BVTV cấm (TT 75/2025), NĐ 24/2026 phụ lục I–IV (phụ lục IV có ngưỡng khối
// lượng), hóa chất phải công bố theo lô (TT 01/2026). Trước đây chỉ tra được từng từ trong mục
// «Pháp lý & thuế»; mục đó nay chỉ còn phần thuế («Thuế»).
//
// Bộ lọc là state CỤC BỘ: ô tìm `q` trên URL là của thanh lọc dòng hàng hải quan, dùng chung thì
// đổi mục là ô tìm hóa chất bị ghi đè bằng tên hàng. Riêng thẻ cảnh báo trên đầu vẫn đọc từ khóa
// dòng hàng đang tra — dải cảnh báo ở các mục khác bảo «xem mục Pháp lý» là trỏ vào thẻ đó.
import { useMemo, useState } from 'react'

import { DataTable } from '@/shared/data-table'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { Card, CardTitle } from '@/shared/ui/card'
import { SearchField } from '@/shared/ui/search-field'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'

import {
  buildRegulationPesticideColumn,
  CUSTOMS_REGULATION_COLUMNS,
} from '../../config/customs-regulation-columns'
import { useCustomsRegulationOptions, useCustomsRegulations } from '../../hooks/use-customs'
import type { CustomsRegulationHit } from '../../types/customs'
import { buildRegulationParams, resolveRegulationEmptyMessage } from '../../utils/customs-regulation'
import { CustomsBannedPesticideDialog } from './customs-banned-pesticide-dialog'
import { CustomsRegulationAlertTable } from './customs-regulation-alert-table'

const ALL = 'all'
const DEFAULT_PAGE_SIZE = 50
//  v2 (29/09/2026): thêm cột «Thuốc BVTV chứa» — bản lưu bố cục cũ thắng cột mới (table.md §4).
const STORAGE_KEY = 'procurement.customs-regulations-v2'

interface CustomsRegulationTabProps {
  /** Từ khóa dòng hàng đang tra (thanh lọc trang) và các cảnh báo khớp nó. */
  keyword: string
  alerts: CustomsRegulationHit[]
}

export function CustomsRegulationTab({ keyword, alerts }: CustomsRegulationTabProps) {
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search, 350)
  const [listCode, setListCode] = useState(ALL)
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [page, setPage] = usePageResetOnFilterChange([debouncedSearch, listCode])
  const [pesticidesOf, setPesticidesOf] = useState<CustomsRegulationHit | null>(null)
  //  Cột «Thuốc BVTV chứa» đứng TRƯỚC «Lưu ý» (cột rộng nhất): đặt cuối thì nó rơi ra ngoài khung
  //  ở màn 1440px, phải cuộn ngang mới thấy — mà nó là thứ mới của bảng này.
  const columns = useMemo(() => {
    const at = CUSTOMS_REGULATION_COLUMNS.findIndex((column) => column.key === 'obligation')
    const pesticide = buildRegulationPesticideColumn(setPesticidesOf)
    return at < 0
      ? [...CUSTOMS_REGULATION_COLUMNS, pesticide]
      : [...CUSTOMS_REGULATION_COLUMNS.slice(0, at), pesticide, ...CUSTOMS_REGULATION_COLUMNS.slice(at)]
  }, [])

  const options = useCustomsRegulationOptions()
  const list = useCustomsRegulations({
    ...buildRegulationParams(debouncedSearch, listCode),
    page,
    page_size: pageSize,
  })
  const filtersActive = search !== '' || listCode !== ALL

  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs text-muted-foreground">
        Tra cứu tham khảo từ văn bản đã nạp (NĐ 24/2026/NĐ-CP · TT 75/2025/TT-BNNMT · TT
        01/2026/TT-BCT). Không thay cho ý kiến pháp chế — đối chiếu văn bản gốc trước khi quyết định.
      </p>

      {alerts.length > 0 && (
        <Card className="gap-3 p-4">
          <CardTitle className="text-base">Cảnh báo cho từ khóa đang tra «{keyword}»</CardTitle>
          <CustomsRegulationAlertTable items={alerts} />
        </Card>
      )}

      <Card className="p-4">
        <DataTable
          columns={columns}
          rows={list.data?.items}
          getRowId={(row) => row.id}
          isLoading={list.isLoading}
          isError={list.isError}
          emptyMessage={resolveRegulationEmptyMessage(options.data?.total ?? 0)}
          storageKey={STORAGE_KEY}
          filtersActive={filtersActive}
          onResetFilters={() => {
            setSearch('')
            setListCode(ALL)
          }}
          pagination={{
            page,
            pageSize,
            total: list.data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: (size) => {
              setPageSize(size)
              setPage(1)
            },
            unitLabel: 'hóa chất',
          }}
          toolbar={
            <>
              <SearchField
                value={search}
                onChange={setSearch}
                placeholder="Tên, số CAS hoặc công thức (vd H2SO4)…"
                placeholderShort="Tên, số CAS…"
                aria-label="Tìm hóa chất theo văn bản"
                className="w-full max-w-xs"
              />
              <Select value={listCode} onValueChange={setListCode}>
                <SelectTrigger className="w-64 max-md:w-full" aria-label="Lọc theo văn bản">
                  <SelectValue placeholder="Văn bản" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả văn bản</SelectItem>
                  {(options.data?.lists ?? []).map((item) => (
                    <SelectItem key={item.value} value={String(item.value)}>
                      {item.label} ({item.count.toLocaleString('vi-VN')})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </>
          }
        />
      </Card>

      <CustomsBannedPesticideDialog regulation={pesticidesOf} onClose={() => setPesticidesOf(null)} />
    </div>
  )
}
