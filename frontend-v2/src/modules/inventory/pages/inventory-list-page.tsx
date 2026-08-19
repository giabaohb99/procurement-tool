import { Search, SlidersHorizontal } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { ConditionalFilter, FilterProvider, useFilterQuery } from '@/shared/conditional-filter'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
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
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { InventoryAdjustDialog } from '../components/inventory-adjust-dialog'
import { InventoryDetailDialog } from '../components/inventory-detail-dialog'
import { INVENTORY_FILTER_FIELDS } from '../config/inventory-filter-fields'
import { useInventoryItems } from '../hooks/use-inventory'
import { useItemGroupOptions, useWarehouseOptions } from '../hooks/use-inventory-catalog'
import { QTY_STATUS_OPTIONS, type InventoryItem } from '../types/inventory'

const ALL = 'all'

const FILTER_CONFIG = {
  fields: INVENTORY_FILTER_FIELDS,
  allowConjunctionToggle: true,
  // Bốn ô chọn trên thanh công cụ. Thiếu tên nào ở đây là bấm "Áp dụng" bộ lọc
  // nâng cao xong mất luôn ô đó.
  preserveParams: ['company_id', 'warehouse_code', 'item_group', 'qty_status'],
}

export function InventoryListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <InventoryListContent />
    </FilterProvider>
  )
}

/**
 * Tồn kho hiện tại theo công ty · kho · mã sản phẩm.
 *
 * Số dư ở đây KHÔNG ai gõ thẳng: backend cộng dồn sổ phát sinh
 * (`inventory/service._recompute`) mỗi lần nhận hàng hoặc điều chỉnh tay, rồi
 * ghi lại `qty` / `avg_cost` / `value`. Vì vậy màn này chỉ đọc, đường sửa duy
 * nhất là hộp thoại Điều chỉnh — và mỗi lần chỉnh đều để lại một dòng trong sổ.
 *
 * Khác bản v1 hai chỗ, đều có chủ ý:
 *  - v1 tải 500 dòng rồi tự cắt trang ở trình duyệt; ở đây server phân trang.
 *  - MẤT SẮP XẾP THEO CỘT: `DataTable` chưa hỗ trợ, mà `/api/inventory` cũng
 *    không nhận tham số sort — v1 sắp được chỉ vì đã ôm cả 500 dòng về máy.
 *    Thứ tự server trả (`product_code` tăng dần) đúng bằng mặc định của v1.
 */
function InventoryListContent() {
  const { can } = usePermission()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [warehouseCode, setWarehouseCode] = useUrlParamState('warehouse_code', ALL)
  const [itemGroup, setItemGroup] = useUrlParamState('item_group', ALL)
  const [qtyStatus, setQtyStatus] = useUrlParamState('qty_status', ALL)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const [detailItem, setDetailItem] = useState<InventoryItem | null>(null)
  const [adjustOpen, setAdjustOpen] = useState(false)
  const [adjustPreset, setAdjustPreset] = useState<InventoryItem | null>(null)

  const { data: companies } = useCompanies({ page_size: 500, is_active: true })
  const { data: warehouses } = useWarehouseOptions()
  const { data: itemGroups } = useItemGroupOptions()
  const { queryParams, queryKey } = useFilterQuery()

  const [page, setPage] = usePageResetOnFilterChange([
    queryKey,
    debouncedValue,
    companyId,
    warehouseCode,
    itemGroup,
    qtyStatus,
  ])

  const params: ListParams = { ...queryParams, page, page_size: pageSize }
  // Ô tìm kiếm gửi tham số TRẦN -> `apply_filters` dịch thành LIKE %tên%.
  if (debouncedValue) params.product_name = debouncedValue
  if (companyId !== ALL) params.company_id = Number(companyId)
  // Mã kho thì phải KHỚP CHÍNH XÁC: gửi trần thì kho "K1" kéo theo cả "K10".
  if (warehouseCode !== ALL) params.warehouse_code__eq = warehouseCode
  if (itemGroup !== ALL) params.item_group = itemGroup
  if (qtyStatus !== ALL) params.qty_status = qtyStatus

  const { data, isLoading, isError } = useInventoryItems(params)

  // useCallback để đưa được vào deps của `columns` mà không phá memo.
  const companyName = useCallback(
    (id: number) => (companies?.items ?? []).find((company) => company.id === id)?.name ?? '—',
    [companies],
  )

  const columns = useMemo<DataTableColumn<InventoryItem>[]>(
    () => [
      { key: 'company', header: 'Công ty', width: 200, cell: (r) => companyName(r.company_id) },
      { key: 'warehouse_code', header: 'Kho', width: 110, cell: (r) => r.warehouse_code || '—' },
      {
        key: 'product_code',
        header: 'Mã SP',
        width: 150,
        cell: (r) => <span className="font-medium">{r.product_code}</span>,
      },
      {
        key: 'product_name',
        header: 'Tên sản phẩm',
        width: 280,
        hideable: false,
        cell: (r) => (
          <span className="truncate" title={r.product_name}>
            {r.product_name || '—'}
          </span>
        ),
      },
      { key: 'unit', header: 'ĐVT', width: 90, cell: (r) => r.unit || '—' },
      {
        key: 'qty',
        header: 'Tồn hiện tại',
        width: 130,
        align: 'right',
        // Tồn âm = xuất nhiều hơn nhập, gần như luôn là sai sót chứng từ chứ
        // không phải tình trạng kho thật -> tô đỏ để không trôi qua mắt.
        cell: (r) => (
          <span className={cn('font-semibold tabular-nums', r.qty < 0 && 'text-destructive')}>
            {formatQuantity(r.qty)}
          </span>
        ),
      },
      {
        key: 'avg_cost',
        header: 'Đơn giá BQ',
        width: 140,
        align: 'right',
        cell: (r) => <span className="tabular-nums">{formatUnitPrice(r.avg_cost)}</span>,
      },
      {
        key: 'value',
        header: 'Giá trị tồn',
        width: 150,
        align: 'right',
        cell: (r) => <span className="font-semibold tabular-nums">{formatMoney(r.value)}</span>,
      },
    ],
    [companyName],
  )

  const canWrite = can('inventory', 'write')

  return (
    <PageContainer fill>
      <PageHeader
        title="Tồn kho"
        description="Số dư tồn theo công ty, kho và mã sản phẩm — hệ thống tự tính từ sổ phát sinh."
        actions={
          canWrite ? (
            <Button
              onClick={() => {
                setAdjustPreset(null)
                setAdjustOpen(true)
              }}
            >
              <SlidersHorizontal />
              Điều chỉnh tồn
            </Button>
          ) : undefined
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(r) => r.id}
          onRowClick={(r) => setDetailItem(r)}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không có dòng tồn nào khớp bộ lọc."
          storageKey="inventory.stock"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'dòng tồn',
          }}
          toolbar={
            <>
              <div className="relative min-w-56 flex-1 md:max-w-xs">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo tên sản phẩm…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              <Select value={companyId} onValueChange={setCompanyId}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Công ty" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả công ty</SelectItem>
                  {(companies?.items ?? []).map((company) => (
                    <SelectItem key={company.id} value={String(company.id)}>
                      {company.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={warehouseCode} onValueChange={setWarehouseCode}>
                <SelectTrigger className="w-52">
                  <SelectValue placeholder="Kho" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả kho</SelectItem>
                  {(warehouses?.items ?? []).map((warehouse) => (
                    <SelectItem key={warehouse.id} value={warehouse.code}>
                      {warehouse.code} — {warehouse.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/*
                Giá trị gửi đi là TÊN phân loại, không phải mã: backend so
                `Product.item_group == item_group`, mà cột đó lưu tên.
                Kèm theo một lỗ hổng dữ liệu có sẵn: 685 sản phẩm đang mang tên
                phân loại KHÔNG có trong danh mục (ICARE, Chai, Can, Bao…) nên
                không lọc tới được từ ô này. Bản v1 cũng vậy; chỗ sửa là dọn dữ
                liệu danh mục, không phải sửa màn này.
              */}
              <Select value={itemGroup} onValueChange={setItemGroup}>
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="Phân loại" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả phân loại</SelectItem>
                  {(itemGroups?.items ?? []).map((group) => (
                    <SelectItem key={group.id} value={group.name}>
                      {group.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={qtyStatus} onValueChange={setQtyStatus}>
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="Trạng thái tồn" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Mọi trạng thái tồn</SelectItem>
                  {QTY_STATUS_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <ConditionalFilter />
            </>
          }
        />
      </Card>

      <InventoryDetailDialog
        item={detailItem}
        onOpenChange={(open) => {
          if (!open) setDetailItem(null)
        }}
        companyName={detailItem ? companyName(detailItem.company_id) : '—'}
        onAdjust={
          canWrite
            ? () => {
                setAdjustPreset(detailItem)
                setDetailItem(null)
                setAdjustOpen(true)
              }
            : undefined
        }
      />

      <InventoryAdjustDialog
        open={adjustOpen}
        onOpenChange={setAdjustOpen}
        preset={adjustPreset}
      />
    </PageContainer>
  )
}
