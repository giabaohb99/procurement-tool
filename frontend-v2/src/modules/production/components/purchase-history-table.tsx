import { useQuery } from '@tanstack/react-query'
import { Search, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiGet } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import type { PurchaseHistoryRow } from '@/modules/procurement/api/purchase-request-support-api'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { appRoutes } from '@/shared/constants/app-routes'
import type { PaginatedResult } from '@/shared/types/api'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'

interface PurchaseHistoryTableProps {
  productCode?: string
  supplierCode?: string
}

function legacyOrigin(extra?: Record<string, unknown>): string {
  if (!extra) return 'Lần mua trước khi dùng hệ thống — không có đơn mua hàng để mở.'
  const parts = [extra.nguon, extra.sheet, extra.dong_excel ? `dòng ${extra.dong_excel}` : ''].filter(Boolean)
  return parts.length
    ? `Lần mua trước khi dùng hệ thống.\nNguồn: ${parts.join(' · ')}`
    : 'Lần mua trước khi dùng hệ thống — không có đơn mua hàng để mở.'
}

export function PurchaseHistoryTable({ productCode, supplierCode }: PurchaseHistoryTableProps) {
  const { can } = usePermission()
  const [page, setPage] = useState<number>(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [searchInput, setSearchInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchQuery(searchInput.trim())
      setPage(1)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchInput])

  const byProduct = Boolean(productCode)
  const canReadSupplier = can('supplier', 'read')
  const showPartnerColumn = !byProduct || canReadSupplier

  const targetCode = productCode || supplierCode || ''
  const apiUrl = byProduct
    ? `/api/products/${encodeURIComponent(targetCode)}/purchase-history`
    : `/api/suppliers/${encodeURIComponent(targetCode)}/purchase-history`

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['purchase-history', byProduct ? 'product' : 'supplier', targetCode, page, pageSize, searchQuery],
    queryFn: () =>
      apiGet<PaginatedResult<PurchaseHistoryRow>>(apiUrl, {
        params: { page, page_size: pageSize, search: searchQuery },
      }),
    enabled: Boolean(targetCode),
  })

  const columns = useMemo<DataTableColumn<PurchaseHistoryRow>[]>(() => {
    const cols: DataTableColumn<PurchaseHistoryRow>[] = [
      {
        key: 'order_date',
        header: 'Ngày đặt',
        width: 120,
        defaultPinned: true,
        cell: (r) => formatDate(r.order_date) || '—',
      },
      {
        key: 'po_code',
        header: 'Mã PO',
        width: 150,
        defaultPinned: true,
        cell: (r) =>
          r.po_id ? (
            <Link
              to={appRoutes.procurement.purchaseOrderDetail(r.po_id)}
              className="font-semibold text-primary hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              {r.po_code}
            </Link>
          ) : (
            <Badge variant="outline" className="font-normal text-muted-foreground" title={legacyOrigin(r.extra)}>
              Dữ liệu cũ
            </Badge>
          ),
      },
    ]

    if (showPartnerColumn) {
      cols.push({
        key: 'partner',
        header: byProduct ? 'Nhà cung cấp' : 'Sản phẩm',
        width: 260,
        wrap: true,
        cell: (r) => (byProduct ? r.supplier_name || r.supplier_code : r.product_name || r.product_code) || '—',
      })
    }

    cols.push(
      {
        key: 'unit',
        header: 'ĐVT',
        width: 90,
        cell: (r) => r.unit || '—',
      },
      {
        key: 'qty_order',
        header: 'SL đặt',
        width: 110,
        cell: (r) => (
          <div className="text-right font-medium">
            {Number(r.qty_order || 0).toLocaleString('vi-VN')}
          </div>
        ),
      },
      {
        key: 'price',
        header: 'Đơn giá',
        width: 130,
        cell: (r) => <div className="text-right">{formatMoney(r.price)}</div>,
      },
      {
        key: 'vat',
        header: 'VAT %',
        width: 90,
        cell: (r) => <div className="text-right">{r.vat ?? 0}%</div>,
      },
      {
        key: 'amount',
        header: 'Thành tiền',
        width: 150,
        cell: (r) => (
          <div className="text-right font-semibold text-navy">{formatMoney(r.amount)}</div>
        ),
      },
      {
        key: 'company_name',
        header: 'Công ty',
        width: 220,
        wrap: true,
        cell: (r) => r.company_name || '—',
      },
    )

    return cols
  }, [byProduct, showPartnerColumn])

  const toolbar = (
    <div className="flex flex-wrap items-center gap-3">
      <div className="relative w-72 sm:w-80">
        <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
        <Input
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') e.preventDefault()
          }}
          placeholder="Tìm theo mã PO, nhà cung cấp, công ty…"
          className="h-9 pl-9 pr-8 text-sm"
        />
        {searchInput && (
          <button
            type="button"
            onClick={() => setSearchInput('')}
            className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
          >
            <X className="size-4" />
          </button>
        )}
      </div>

      {data?.total !== undefined && (
        <span className="text-xs text-muted-foreground">
          Tổng cộng: <strong className="text-foreground">{data.total}</strong> lần mua
        </span>
      )}
    </div>
  )

  return (
    <Card className="p-4">
      <DataTable
        toolbar={toolbar}
        columns={columns}
        rows={data?.items}
        getRowId={(r) => String(r.id || `${r.po_id}-${r.product_code}`)}
        isLoading={isLoading}
        isError={isError}
        onRefresh={() => refetch()}
        storageKey={`production.${byProduct ? 'product' : 'supplier'}.purchase-history`}
        emptyMessage={
          searchQuery
            ? 'Không tìm thấy lịch sử mua hàng phù hợp với từ khóa.'
            : 'Chưa có lịch sử mua hàng nào.'
        }
        pagination={{
          page,
          pageSize,
          total: data?.total ?? 0,
          onPageChange: setPage,
          onPageSizeChange: setPageSize,
          unitLabel: 'lần mua',
        }}
      />
    </Card>
  )
}
