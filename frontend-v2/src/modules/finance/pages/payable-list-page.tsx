import { FilePlus2, Search } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { ConditionalFilter, FilterProvider, useFilterQuery } from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
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
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { cn } from '@/shared/utils/cn'
import { PayableAgingBadge, PayableStatusBadge } from '../components/payable-badges'
import { PAYABLE_FILTER_FIELDS } from '../config/payable-filter-fields'
import { usePayableSummary, usePayables } from '../hooks/use-payables'
import {
  AGING_BUCKETS,
  PAYABLE_SOURCE_LABELS,
  PAYABLE_STATUS_OPTIONS,
  agingLabel,
  type Payable,
} from '../types/payable'

const ALL = 'all'

/** Năm hiện tại — mặc định của ô "Năm", trùng mặc định của backend khi không gửi param. */
const THIS_YEAR = new Date().getFullYear()

const FILTER_CONFIG = {
  fields: PAYABLE_FILTER_FIELDS,
  allowConjunctionToggle: true,
  // Bốn ô chọn trên thanh công cụ. Thiếu tên nào ở đây là bấm "Áp dụng" bộ lọc
  // nâng cao xong mất luôn ô đó.
  preserveParams: ['company_id', 'status', 'aging', 'year'],
}

export function PayableListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <PayableListContent />
    </FilterProvider>
  )
}

/**
 * Công nợ phải trả — bảng CHỈ ĐỌC. Mỗi dòng do backend sinh ngầm lúc nhận hàng
 * (`payable/service.upsert`), không ai nhập tay được.
 *
 * Khác bản v1 một chỗ, có chủ ý: v1 tải hết 1000 dòng rồi tự cắt trang ở trình
 * duyệt; ở đây phân trang do server làm, nên năm nợ nhiều nghìn dòng không còn
 * treo màn. Nhờ vậy cột tick CHỌN được BẮC QUA TRANG — `selected` giữ cả bản
 * ghi (không chỉ id), tick trang 1 rồi sang trang 2 tick tiếp, bấm "Tạo đề nghị"
 * vẫn gom đủ. Đổi bộ lọc thì xóa lựa chọn để không ôm theo khoản của bộ lọc cũ
 * đã biến khỏi bảng; chỉ SANG TRANG thì giữ nguyên.
 */
function PayableListContent() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [aging, setAging] = useUrlParamState('aging', ALL)
  const [year, setYear] = useUrlParamState('year', String(THIS_YEAR))
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  // Khoản đang tick để lên đề nghị thanh toán. Giữ CẢ BẢN GHI (không chỉ id) để
  // đếm được số NCC và truyền thẳng sang màn tạo phiếu, khỏi phải tải lại theo id.
  const [selected, setSelected] = useState<Record<number, Payable>>({})

  const { data: companies } = useCompanies({ page_size: 500, is_active: true })
  const { queryParams, queryKey } = useFilterQuery()

  const [page, setPage] = usePageResetOnFilterChange([
    queryKey,
    debouncedValue,
    companyId,
    status,
    aging,
    year,
  ])

  // Đổi bộ lọc thì bỏ hết tick (dùng đúng chữ ký của phần lọc — KHÔNG có `page`,
  // nên chỉ sang trang thì lựa chọn được giữ nguyên).
  const filterChanged = useHasChanged(
    JSON.stringify([queryKey, debouncedValue, companyId, status, aging, year]),
  )
  if (filterChanged) setSelected({})

  // Tách riêng phần LỌC khỏi phần phân trang: bốn ô tổng phải tính trên cả tập
  // kết quả chứ không phải trên 20 dòng đang hiện.
  const filterParams: ListParams = { ...queryParams, year }
  if (debouncedValue) filterParams.po_code = debouncedValue
  if (companyId !== ALL) filterParams.company_id = Number(companyId)
  if (status !== ALL) filterParams.status = status
  if (aging !== ALL) filterParams.aging = aging

  const { data, isLoading, isError } = usePayables({ page, page_size: pageSize, ...filterParams })
  const { data: summary, isLoading: isSummaryLoading } = usePayableSummary(filterParams)

  // useCallback để đưa được vào deps của `columns` mà không phá memo.
  const companyName = useCallback(
    (id: number) => (companies?.items ?? []).find((company) => company.id === id)?.name ?? '—',
    [companies],
  )

  const canCreatePayment = can('payment_request', 'create')

  // Chỉ tick được khoản CHƯA tất toán, CÒN nợ và ĐÃ có số hóa đơn — đúng ba điều
  // kiện backend cần để lên đề nghị thanh toán.
  const isPayable = useCallback(
    (p: Payable) => p.status !== 'paid' && p.remaining > 0 && p.invoice_no.trim() !== '',
    [],
  )

  const toggleRow = useCallback((row: Payable) => {
    setSelected((prev) => {
      const next = { ...prev }
      if (next[row.id]) delete next[row.id]
      else next[row.id] = row
      return next
    })
  }, [])

  const columns = useMemo<DataTableColumn<Payable>[]>(() => {
    const base: DataTableColumn<Payable>[] = [
      {
        key: 'supplier_name',
        header: 'Nhà cung cấp',
        width: 240,
        hideable: false,
        // Bảng 15 cột: ghim tên NCC để cuộn tới cột tiền vẫn biết đang xem nợ ai.
        defaultPinned: true,
        cell: (p) => (
          <span className="truncate font-medium" title={p.supplier_name || p.supplier_code}>
            {p.supplier_name || p.supplier_code || '—'}
          </span>
        ),
      },
      {
        key: 'supplier_code',
        header: 'Mã NCC',
        width: 130,
        cell: (p) => <span className="text-muted-foreground">{p.supplier_code || '—'}</span>,
      },
      {
        key: 'source_type',
        header: 'Loại nợ',
        width: 120,
        cell: (p) => PAYABLE_SOURCE_LABELS[p.source_type] ?? p.source_type,
      },
      { key: 'company', header: 'Công ty', width: 200, cell: (p) => companyName(p.company_id) },
      { key: 'po_code', header: 'Mã ĐMH', width: 150, cell: (p) => p.po_code || '—' },
      {
        key: 'invoice_no',
        header: 'Số hóa đơn',
        width: 150,
        // Chưa có số HĐ = chưa lên được yêu cầu thanh toán, nên phải nhìn ra ngay
        // chứ không để trống như một ô rỗng bình thường.
        cell: (p) =>
          p.invoice_no || <span className="text-xs text-destructive">chưa có HĐ</span>,
      },
      {
        key: 'incur_date',
        header: 'Ngày phát sinh',
        width: 130,
        // v1 hiện `created_at` ở cột này. Dùng `incur_date` mới đúng nghĩa: đó là
        // ngày NHẬN HÀNG, còn `created_at` chỉ là lúc dòng nợ được ghi vào sổ —
        // hai mốc lệch nhau khi nhập bù chứng từ cũ. Giữ `created_at` ở cột ẩn
        // bên dưới cho ai cần đối chiếu.
        cell: (p) => formatDate(p.incur_date) || '—',
      },
      {
        key: 'created_at',
        header: 'Ngày ghi sổ',
        width: 160,
        defaultHidden: true,
        cell: (p) => formatDateTime(p.created_at) || '—',
      },
      { key: 'due_date', header: 'Hạn trả', width: 120, cell: (p) => formatDate(p.due_date) || '—' },
      {
        key: 'aging',
        header: 'Tuổi nợ',
        width: 140,
        cell: (p) => <PayableAgingBadge aging={p.aging} />,
      },
      {
        key: 'amount',
        header: 'Tiền trước VAT',
        width: 150,
        align: 'right',
        defaultHidden: true,
        cell: (p) => <span className="tabular-nums">{formatMoney(p.amount)}</span>,
      },
      {
        key: 'vat',
        header: 'VAT',
        width: 130,
        align: 'right',
        defaultHidden: true,
        cell: (p) => <span className="tabular-nums">{formatMoney(p.vat)}</span>,
      },
      {
        key: 'total',
        header: 'Tổng nợ',
        width: 150,
        align: 'right',
        cell: (p) => <span className="tabular-nums">{formatMoney(p.total)}</span>,
      },
      {
        key: 'paid_amount',
        header: 'Đã trả',
        width: 150,
        align: 'right',
        cell: (p) => <span className="tabular-nums">{formatMoney(p.paid_amount)}</span>,
      },
      {
        key: 'remaining',
        header: 'Còn lại',
        width: 150,
        align: 'right',
        cell: (p) => (
          <span className="font-semibold tabular-nums">{formatMoney(p.remaining)}</span>
        ),
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 170,
        cell: (p) => <PayableStatusBadge status={p.status} />,
      },
    ]

    // Không có quyền lập đề nghị thanh toán thì bỏ hẳn cột tick — người chỉ được
    // xem công nợ không cần chỗ chọn.
    if (!canCreatePayment) return base

    // Cột tick — lối CHÍNH để lên đề nghị thanh toán (nút phụ là form trắng ở màn
    // YCTT). Luôn hiện, ghim trái để cuộn tới cột tiền vẫn tick được.
    const selectColumn: DataTableColumn<Payable> = {
      key: 'select',
      header: 'Chọn',
      width: 56,
      minWidth: 44,
      align: 'center',
      hideable: false,
      defaultPinned: true,
      cell: (p) => (
        <span
          className="flex items-center justify-center"
          // Ô tick nằm trên hàng bấm-được (mở ĐMH) — chặn nổi bọt kẻo tick lại mở đơn.
          onClick={(e) => e.stopPropagation()}
        >
          <Checkbox
            checked={!!selected[p.id]}
            disabled={!isPayable(p)}
            aria-label="Chọn khoản nợ này để lên đề nghị thanh toán"
            onCheckedChange={() => toggleRow(p)}
          />
        </span>
      ),
    }
    return [selectColumn, ...base]
  }, [companyName, canCreatePayment, selected, isPayable, toggleRow])

  const selectedRows = useMemo(() => Object.values(selected), [selected])
  const selectedSupplierCount = useMemo(
    () => new Set(selectedRows.map((r) => r.supplier_code)).size,
    [selectedRows],
  )

  // KHÔNG tạo phiếu ngay tại đây (tránh đẻ phiếu nháp): đẩy các khoản đã tick
  // sang màn tạo, chỉ khi bấm "Tạo phiếu" ở đó mới ghi DB. Kèm cả `rows` qua
  // state để màn tạo khỏi tải lại theo id; thiếu state nó vẫn tự fetch theo
  // `?payables=`. Nhiều NCC thì backend tự tách thành nhiều phiếu.
  function createRequest() {
    if (!selectedRows.length) return
    const ids = selectedRows.map((r) => r.id).join(',')
    navigate(`${appRoutes.finance.paymentRequestNew}?payables=${ids}`, {
      state: { rows: selectedRows },
    })
  }

  // Bấm dòng thì mở ĐƠN MUA HÀNG sinh ra khoản nợ đó — đường tra ngược duy nhất
  // từ sổ nợ về chứng từ gốc. Không có quyền đọc ĐMH thì bỏ hẳn, kẻo bấm xong
  // rơi vào màn báo thiếu quyền.
  const canOpenOrder = can('purchase_order', 'read')

  return (
    <PageContainer fill>
      <PageHeader
        title="Công nợ phải trả"
        description="Khoản phải trả nhà cung cấp và đơn vị vận chuyển, sinh tự động khi nhận hàng."
        actions={
          canCreatePayment ? (
            <Button disabled={selectedRows.length === 0} onClick={createRequest}>
              <FilePlus2 className="size-4" />
              Tạo đề nghị thanh toán
              {selectedRows.length > 0 &&
                ` (${selectedRows.length} khoản · ${selectedSupplierCount} NCC)`}
            </Button>
          ) : undefined
        }
      />

      <div className="mb-4 grid shrink-0 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard label="Tổng nợ" value={summary?.total} loading={isSummaryLoading} />
        <SummaryCard
          label="Đã trả"
          value={summary?.paid}
          loading={isSummaryLoading}
          className="text-success"
        />
        <SummaryCard
          label="Còn phải trả"
          value={summary?.remaining}
          loading={isSummaryLoading}
          className="text-info"
        />
        <SummaryCard
          label="Quá hạn"
          value={summary?.overdue}
          loading={isSummaryLoading}
          className="text-destructive"
        />
      </div>

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(p) => p.id}
          onRowClick={
            canOpenOrder
              ? (p) => {
                  if (p.po_id > 0) navigate(appRoutes.procurement.purchaseOrderDetail(p.po_id))
                }
              : undefined
          }
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không có khoản công nợ nào khớp bộ lọc."
          storageKey="finance.payables"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'khoản',
          }}
          toolbar={
            <>
              <div className="relative min-w-56 flex-1 md:max-w-xs">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo mã ĐMH…"
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

              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Trạng thái" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
                  {PAYABLE_STATUS_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={aging} onValueChange={setAging}>
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="Tuổi nợ" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Mọi tuổi nợ</SelectItem>
                  {AGING_BUCKETS.map((bucket) => (
                    <SelectItem key={bucket} value={bucket}>
                      {agingLabel(bucket)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={year} onValueChange={setYear}>
                <SelectTrigger className="w-36">
                  <SelectValue placeholder="Năm" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả các năm</SelectItem>
                  {[THIS_YEAR, THIS_YEAR - 1, THIS_YEAR - 2].map((item) => (
                    <SelectItem key={item} value={String(item)}>
                      {item}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <ConditionalFilter />
            </>
          }
        />
      </Card>

      <p className="mt-2 shrink-0 text-xs text-muted-foreground">
        Chỉ khoản nợ <b>đã có Số hóa đơn</b> mới lên được đề nghị thanh toán. Nợ hàng hóa nhập số
        HĐ ở chi tiết sản phẩm trên đơn mua hàng; nợ vận chuyển tự lấy theo Mã MISA + Mã SP.
      </p>

      {selectedSupplierCount > 1 && (
        <p className="mt-1 shrink-0 text-xs text-info">
          Đang chọn {selectedSupplierCount} nhà cung cấp — hệ thống sẽ tách thành{' '}
          {selectedSupplierCount} phiếu đề nghị thanh toán riêng.
        </p>
      )}
    </PageContainer>
  )
}

/** Ô tổng tiền ở đầu trang. Chỉ để ĐỌC — khác `SummaryCard` bấm được của Báo cáo khảo sát. */
function SummaryCard({
  label,
  value,
  loading,
  className,
}: {
  label: string
  value: number | undefined
  loading: boolean
  className?: string
}) {
  return (
    <div className="rounded-lg border bg-card px-4 py-3">
      <p className="text-sm text-muted-foreground">{label}</p>
      {loading ? (
        <Skeleton className="mt-1.5 h-7 w-32" />
      ) : (
        <p className={cn('mt-0.5 text-xl font-semibold text-navy dark:text-foreground', className)}>
          {formatMoney(value ?? 0)}
        </p>
      )}
    </div>
  )
}
