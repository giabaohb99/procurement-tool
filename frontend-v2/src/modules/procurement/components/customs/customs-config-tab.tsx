// bao-CR-501 — thẻ «Cấu hình» của màn Tra cứu thị trường: gom BA danh mục vào NGAY màn tra
// cứu — từ khóa nhãn Thành phẩm / Nguyên liệu (bao-CR-494), từ đồng nghĩa tìm kiếm (bao-CR-495)
// và danh mục hóa chất theo văn bản (bao-CR-470). Đại ca chốt 26/09: chức năng này càng ít màn
// hình càng tốt, không đẻ màn / mục menu riêng.
//
// Không nhúng `CrudListPage`: nó ghi ô tìm vào tham số `q` (trùng ô tìm tên hàng của màn tra
// cứu) và bộ lọc nâng cao viết lại cả thanh địa chỉ (xóa bộ lọc + thẻ đang mở). Ở đây ô tìm
// số trang, lọc nhanh là state cục bộ; hộp Thêm/Sửa/Xóa dùng lại `CrudFormDialog` với đúng
// cấu hình cũ (hộp tự ẩn nút Lưu / Xóa khi thiếu quyền, nên người chỉ xem vẫn mở ra đọc được).
import { Plus } from 'lucide-react'
import { useState } from 'react'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { CrudFormDialog, useCrudList, type CrudConfig, type CrudRecord } from '@/shared/crud'
import { DataTable } from '@/shared/data-table'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { SearchField } from '@/shared/ui/search-field'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'

import { CUSTOMS_KIND_KEYWORD_CRUD_CONFIG } from '../../config/customs-kind-keyword-crud'
import { CUSTOMS_REGULATION_CRUD_CONFIG } from '../../config/customs-regulation-crud'
import { CUSTOMS_SEARCH_SYNONYM_CRUD_CONFIG } from '../../config/customs-search-synonym-crud'

const PAGE_SIZE = 10

/**
 * Hai khối đầu thuộc khóa `customs_price` (hiện khi sửa được — `canConfigure`), khối hóa chất
 * thuộc khóa riêng `customs_regulation` (hiện khi XEM được — trước đây nút «Danh mục hóa chất»
 * trên đầu màn cũng mở cho người chỉ có quyền đọc).
 */
export function CustomsConfigTab({
  canConfigure,
  canReadRegulations,
}: {
  canConfigure: boolean
  canReadRegulations: boolean
}) {
  return (
    <div className="flex flex-col gap-3">
      {canConfigure && <CustomsCatalogCard config={CUSTOMS_KIND_KEYWORD_CRUD_CONFIG} />}
      {canConfigure && <CustomsCatalogCard config={CUSTOMS_SEARCH_SYNONYM_CRUD_CONFIG} />}
      {canReadRegulations && <CustomsCatalogCard config={CUSTOMS_REGULATION_CRUD_CONFIG} />}
    </div>
  )
}

function CustomsCatalogCard<T extends CrudRecord>({ config }: { config: CrudConfig<T> }) {
  const [keyword, setKeyword] = useState('')
  const debouncedKeyword = useDebouncedValue(keyword, 350)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(PAGE_SIZE)
  // undefined = đóng · null = THÊM mới · bản ghi = SỬA (cùng quy ước `CrudListPage`).
  const [formItem, setFormItem] = useState<T | null | undefined>(undefined)
  const [quickValues, setQuickValues] = useState<Record<string, string>>({})
  const quickFilters = (config.quickFilters ?? []).filter((qf) => qf.type === 'select' && qf.options)

  const params: ListParams = { page, page_size: pageSize }
  if (debouncedKeyword) params[config.searchParam || 'name'] = debouncedKeyword
  for (const [key, value] of Object.entries(quickValues)) {
    if (value && value !== 'all') params[key] = value
  }
  const isFiltering =
    Boolean(debouncedKeyword) || Object.values(quickValues).some((value) => value && value !== 'all')
  const { data, isLoading, isError } = useCrudList<T>(config.apiPath, params)
  const idKey = (config.idKey as string) || 'id'

  return (
    <Card className="gap-3 p-4">
      <div className="flex flex-wrap items-start gap-2">
        <div className="min-w-60 flex-1">
          <h3 className="text-base font-semibold">{config.title}</h3>
          {config.description && (
            <p className="text-muted-foreground mt-1 text-sm">{config.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {config.renderToolbarExtra?.()}
          <PermissionGate entity={config.entity} action="create">
            <Button type="button" onClick={() => setFormItem(null)}>
              <Plus className="mr-1.5 size-4" /> Thêm {config.unitLabel}
            </Button>
          </PermissionGate>
        </div>
      </div>

      <DataTable
        columns={config.columns}
        rows={data?.items}
        getRowId={(row: T) => String(row[idKey])}
        isLoading={isLoading}
        isError={isError}
        emptyMessage={
          isFiltering
            ? `Không có ${config.unitLabel} nào khớp bộ lọc.`
            : `Chưa có ${config.unitLabel} nào. Bấm «Thêm ${config.unitLabel}» để tạo.`
        }
        storageKey={config.storageKey}
        onRowClick={(row: T) => setFormItem(row)}
        pagination={{
          page,
          pageSize,
          total: data?.total ?? 0,
          onPageChange: setPage,
          onPageSizeChange: (size) => {
            setPageSize(size)
            setPage(1)
          },
          unitLabel: config.unitLabel,
        }}
        toolbar={
          <>
            <SearchField
              value={keyword}
              onChange={(next) => {
                setKeyword(next)
                setPage(1)
              }}
              placeholder={config.searchPlaceholder || `Tìm ${config.unitLabel}…`}
              className="max-md:min-w-40 md:w-64 md:max-w-sm md:flex-none"
            />
            {quickFilters.map((qf) => (
              <Select
                key={qf.key}
                value={quickValues[qf.key] || 'all'}
                onValueChange={(next) => {
                  setQuickValues((prev) => ({ ...prev, [qf.key]: next }))
                  setPage(1)
                }}
              >
                <SelectTrigger className="h-9 w-full text-xs md:w-44" aria-label={qf.label}>
                  <SelectValue placeholder={qf.label} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả {qf.label.toLowerCase()}</SelectItem>
                  {(qf.options ?? []).map((opt) => (
                    <SelectItem key={String(opt.value)} value={String(opt.value)}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ))}
          </>
        }
      />

      {formItem !== undefined && (
        <CrudFormDialog
          open
          onOpenChange={(next) => !next && setFormItem(undefined)}
          config={config}
          item={formItem ?? undefined}
        />
      )}
    </Card>
  )
}
