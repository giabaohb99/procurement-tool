import { Search } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'

import { appConfig } from '@/core/config/app-config'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
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
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { cn } from '@/shared/utils/cn'
import { DocumentStatusBadge, ProgressStatusBadge } from '../components/document-status-badge'
import { usePurchaseProgress } from '../hooks/use-purchase-documents'
import {
  PROGRESS_STATUSES,
  type PurchaseProgressRow,
} from '../types/purchase-progress'

const ALL = 'all'

/**
 * Tiến độ mua hàng — báo cáo phẳng theo TỪNG LẦN GIAO của từng dòng đơn hàng,
 * không phải danh sách chứng từ.
 *
 * Endpoint `/api/purchase-progress` KHÔNG chạy qua `apply_filters` mà tự đọc bộ
 * tham số riêng (`company_id`, `department`, `status`, `q`, các cặp ngày…) nên
 * màn này không dùng "Bộ lọc điều kiện" như các danh sách khác.
 */
export function PurchaseProgressPage() {
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [department, setDepartment] = useUrlParamState('department', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const { data: companies } = useCompanies({ page_size: 500, is_active: true })
  const { data: departments } = useDepartments({ page_size: 500, is_active: true })

  useEffect(() => setPage(1), [debouncedValue, companyId, department, status])

  const params: ListParams = { page, page_size: pageSize }
  if (debouncedValue) params.q = debouncedValue
  if (companyId !== ALL) params.company_id = Number(companyId)
  if (department !== ALL) params.department = department
  if (status !== ALL) params.status = status

  const { data, isLoading, isError } = usePurchaseProgress(params)

  // Không có quyền `supplier.read` thì backend xóa trắng cột NCC / vận chuyển —
  // ẩn luôn cho khỏi bày ra một loạt ô rỗng.
  const showSupplier = data?.show_supplier ?? true
  // useCallback để `columns` bên dưới phụ thuộc thẳng vào hàm này thay vì phụ
  // thuộc gián tiếp qua `companies` — cách gián tiếp đúng nhưng dễ vỡ: sửa thân
  // hàm mà quên sửa mảng phụ thuộc là bảng hiện dữ liệu cũ.
  const companyName = useCallback(
    (id: number) =>
      (companies?.items ?? []).find((company) => company.id === id)?.name ?? '—',
    [companies],
  )

  const columns = useMemo<DataTableColumn<PurchaseProgressRow>[]>(() => {
    const all: (DataTableColumn<PurchaseProgressRow> & { supplierOnly?: boolean })[] = [
      {
        key: 'po_code',
        header: 'Mã ĐMH',
        width: 160,
        hideable: false,
        // Bảng này rộng ~24 cột: ghim sẵn mã đơn để cuộn tới cột cuối vẫn biết
        // đang xem đơn nào. Người dùng ghim/bỏ ghim tiếp ở menu "Cột".
        defaultPinned: true,
        cell: (row) => <span className="truncate font-medium">{row.po_code}</span>,
      },
      { key: 'misa_code', header: 'Mã MISA', width: 120, defaultHidden: true, cell: (r) => r.misa_code || '—' },
      { key: 'pr_code', header: 'Mã PYC', width: 130, cell: (r) => r.pr_code || '—' },
      { key: 'company', header: 'Công ty', width: 190, cell: (r) => companyName(r.company_id) },
      { key: 'department', header: 'Bộ phận', width: 150, cell: (r) => r.department || '—' },
      {
        key: 'supplier_name',
        header: 'Nhà cung cấp',
        width: 230,
        supplierOnly: true,
        cell: (r) => (
          <span className="truncate" title={r.supplier_name}>
            {r.supplier_name || r.supplier_code || '—'}
          </span>
        ),
      },
      { key: 'nspt', header: 'NSPT', width: 160, cell: (r) => r.nspt || '—' },
      { key: 'order_date', header: 'Ngày ĐH', width: 110, cell: (r) => formatDate(r.order_date) || '—' },
      { key: 'product_code', header: 'Mã SP', width: 150, cell: (r) => r.product_code || '—' },
      {
        key: 'product_name',
        header: 'Tên SP',
        width: 240,
        cell: (r) => (
          <span className="truncate" title={r.product_name}>
            {r.product_name || '—'}
          </span>
        ),
      },
      { key: 'item_group', header: 'Nhóm hàng', width: 150, defaultHidden: true, cell: (r) => r.item_group || '—' },
      { key: 'unit', header: 'ĐVT', width: 80, cell: (r) => r.unit || '—' },
      {
        key: 'qty_order',
        header: 'SL đặt',
        width: 100,
        align: 'right',
        cell: (r) => <span className="tabular-nums">{formatQuantity(r.qty_order) || 0}</span>,
      },
      {
        key: 'price',
        header: 'Đơn giá',
        width: 120,
        align: 'right',
        cell: (r) => <span className="tabular-nums">{formatUnitPrice(r.price) || 0}</span>,
      },
      {
        key: 'order_amount',
        header: 'Thành tiền ĐH',
        width: 150,
        align: 'right',
        cell: (r) => (
          <span className="font-medium tabular-nums">{formatMoney(r.order_amount) || 0}</span>
        ),
      },
      {
        key: 'progress_status',
        header: 'Tiến độ',
        width: 180,
        cell: (r) => <ProgressStatusBadge status={r.progress_status} />,
      },
      { key: 'delivery_no', header: 'Lần giao', width: 100, align: 'right', defaultHidden: true, cell: (r) => r.delivery_no ?? '—' },
      { key: 'warehouse_code', header: 'Kho', width: 120, defaultHidden: true, cell: (r) => r.warehouse_code || '—' },
      {
        key: 'carrier_name',
        header: 'Đơn vị VC',
        width: 180,
        defaultHidden: true,
        supplierOnly: true,
        cell: (r) => r.carrier_name || '—',
      },
      {
        key: 'received_qty',
        header: 'SL nhận',
        width: 110,
        align: 'right',
        cell: (r) => <span className="tabular-nums">{formatQuantity(r.received_qty) || 0}</span>,
      },
      { key: 'received_date', header: 'Ngày nhận', width: 120, cell: (r) => formatDate(r.received_date) || '—' },
      {
        key: 'diff_regulated',
        header: 'CL quy định',
        width: 120,
        align: 'right',
        defaultHidden: true,
        // Âm = giao trễ so với ngày quy định, dương = sớm.
        cell: (r) => <DiffCell value={r.diff_regulated} />,
      },
      {
        key: 'amount',
        header: 'Thành tiền nhận',
        width: 160,
        align: 'right',
        cell: (r) => (
          <span className="font-medium tabular-nums">{formatMoney(r.amount) || 0}</span>
        ),
      },
      {
        key: 'document_status',
        header: 'Hồ sơ CT',
        width: 190,
        cell: (r) => <DocumentStatusBadge status={r.document_status} />,
      },
    ]

    return all.filter((column) => !column.supplierOnly || showSupplier)
  }, [showSupplier, companyName])

  return (
    <PageContainer fill>
      <PageHeader
        title="Tiến độ mua hàng"
        description="Theo dõi từng lần giao hàng của các dòng đơn mua hàng."
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(row) => `${row.po_id}-${row.product_code}-${row.delivery_no ?? 0}-${row.stt ?? 0}`}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không có dòng tiến độ nào khớp bộ lọc."
          storageKey="procurement.purchase-progress"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'dòng',
          }}
          toolbar={
            <>
              <div className="relative min-w-56 flex-1 md:max-w-xs">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm mã ĐMH / PYC / sản phẩm…"
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

              <Select value={department} onValueChange={setDepartment}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Bộ phận" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả bộ phận</SelectItem>
                  {(departments?.items ?? []).map((item) => (
                    // Backend lọc theo TÊN bộ phận, không phải id.
                    <SelectItem key={item.id} value={item.name}>
                      {item.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="w-52">
                  <SelectValue placeholder="Tiến độ" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả tiến độ</SelectItem>
                  {PROGRESS_STATUSES.map((item) => (
                    <SelectItem key={item} value={item}>
                      {item}
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

/** Chênh lệch ngày: âm = trễ (đỏ), dương = sớm (xanh), 0 = đúng hẹn. */
function DiffCell({ value }: { value: number }) {
  return (
    <span
      className={cn(
        'tabular-nums',
        value < 0 && 'text-destructive',
        value > 0 && 'text-success',
        !value && 'text-muted-foreground',
      )}
    >
      {value || 0}
    </span>
  )
}
