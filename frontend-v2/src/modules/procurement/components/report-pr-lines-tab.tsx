import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { PR_LINE_STATUS } from '@/shared/constants/statuses'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { usePrLines } from '../hooks/use-purchase-report'
import { ProgressStatusBadge, StatusBadge } from './document-status-badge'
import { PR_STATUS_LABELS } from '../types/purchase-document'
import type { PrLineRow } from '../types/purchase-report'

const ALL = 'all'

/**
 * Bộ lọc TIẾN ĐỘ dòng hàng: `chua_dat` là giá trị GỘP (backend hiểu = no_po +
 * not_ordered) — đúng mục tiêu báo cáo: soi mã chưa được đặt để khỏi đặt sót đơn.
 */
const LINE_STATUS_OPTIONS = [
  { value: 'chua_dat', label: 'Chưa được đặt hàng (gộp)' },
  ...PR_LINE_STATUS.map((option) => ({ value: option.value, label: option.label })),
]

interface ReportPrLinesTabProps {
  year: string
  companyId?: string
}

/**
 * Báo cáo "Chi tiết YC mua hàng" theo DÒNG hàng (bao-CR-295/299) — dùng chung
 * cho tab trong Báo cáo mua hàng và trang riêng (bao-CR-296).
 *
 * Một YCMH 3 mã hàng / 3 NCC phải ra 3 ĐMH — báo cáo này để NSTM soi mã nào
 * chưa lên đơn, tránh đặt sót. Phân trang phía SERVER như tab Chi phí vận
 * chuyển: một năm vài nghìn dòng, tải hết về trình duyệt là treo trang.
 */
export function ReportPrLinesTab({ year, companyId }: ReportPrLinesTabProps) {
  const [status, setStatus] = useState(ALL)
  const [lineStatus, setLineStatus] = useState(ALL)
  const [assignee, setAssignee] = useState(ALL)
  //  Ô tìm kiếm chỉ áp khi Enter / rời ô (như bản v1): áp theo từng phím gõ là
  //  mỗi ký tự một lượt gọi API phân trang server. `searchDraft` là chữ đang gõ,
  //  `search` mới là giá trị đã áp vào bộ lọc.
  const [searchDraft, setSearchDraft] = useState('')
  const [search, setSearch] = useState('')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [page, setPage] = usePageResetOnFilterChange([
    status,
    lineStatus,
    assignee,
    search,
    year,
    companyId,
  ])

  const { data, isLoading, isError } = usePrLines(
    {
      year,
      company_id: companyId,
      status: status === ALL ? undefined : status,
      line_status: lineStatus === ALL ? undefined : lineStatus,
      assignee: assignee === ALL ? undefined : assignee,
      search: search || undefined,
      page,
      page_size: pageSize,
    },
    true,
  )

  const filtersActive = status !== ALL || lineStatus !== ALL || assignee !== ALL || search !== ''

  function commitSearch() {
    const trimmed = searchDraft.trim()
    if (trimmed !== search) setSearch(trimmed)
  }

  const columns = useMemo<DataTableColumn<PrLineRow>[]>(
    () => [
      { key: 'id', header: 'ID', width: 70, cell: (row) => row.id },
      {
        key: 'pr_code',
        header: 'Mã PYC',
        width: 130,
        hideable: false,
        // Bảng 18 cột: ghim mã phiếu để cuộn tới cột tiến độ vẫn biết dòng của phiếu nào.
        defaultPinned: true,
        cell: (row) => (
          <Link
            to={appRoutes.procurement.purchaseRequestDetail(row.pr_id)}
            className="font-medium text-primary hover:underline"
          >
            {row.pr_code || '—'}
          </Link>
        ),
      },
      {
        key: 'created_date',
        header: 'Ngày tạo',
        width: 110,
        cell: (row) => (
          <span className="whitespace-nowrap">{formatDate(row.created_date) || '—'}</span>
        ),
      },
      { key: 'requester', header: 'Người yêu cầu', width: 150, cell: (row) => row.requester || '—' },
      { key: 'department', header: 'Bộ phận', width: 140, cell: (row) => row.department || '—' },
      { key: 'product_code', header: 'Mã hàng', width: 120, cell: (row) => row.product_code || '—' },
      {
        key: 'product_name',
        header: 'Tên sản phẩm',
        width: 220,
        cell: (row) => (
          <span className="truncate" title={row.product_name}>
            {row.product_name || '—'}
          </span>
        ),
      },
      { key: 'warehouse', header: 'Kho nhận', width: 130, cell: (row) => row.warehouse || '—' },
      { key: 'item_group', header: 'Phân loại', width: 140, cell: (row) => row.item_group || '—' },
      { key: 'gram', header: 'Gram', width: 100, cell: (row) => row.gram || '—' },
      {
        key: 'qty',
        header: 'SL',
        width: 90,
        align: 'right',
        cell: (row) => <span className="tabular-nums">{formatQuantity(row.qty)}</span>,
      },
      {
        key: 'price',
        header: 'Đơn giá',
        width: 120,
        align: 'right',
        cell: (row) => <span className="tabular-nums">{formatUnitPrice(row.price)}</span>,
      },
      {
        key: 'vat_pct',
        header: 'VAT',
        width: 80,
        align: 'right',
        cell: (row) =>
          row.vat_pct ? <span className="tabular-nums">{formatQuantity(row.vat_pct)}%</span> : '',
      },
      {
        key: 'amount',
        header: 'Thành tiền',
        width: 140,
        align: 'right',
        cell: (row) => <span className="tabular-nums">{formatMoney(row.amount)}</span>,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 130,
        cell: (row) => <StatusBadge status={row.status} labels={PR_STATUS_LABELS} />,
      },
      {
        key: 'line_status',
        header: 'Tiến độ',
        width: 160,
        cell: (row) => <ProgressStatusBadge status={row.line_status} />,
      },
      {
        key: 'expected_date',
        header: 'Ngày dự kiến có hàng',
        width: 160,
        cell: (row) => (
          <span className="whitespace-nowrap">{formatDate(row.expected_date) || '—'}</span>
        ),
      },
      {
        key: 'assignee',
        header: 'NSTM phụ trách',
        width: 160,
        cell: (row) => row.assignee_name || row.assignee || '—',
      },
    ],
    [],
  )

  return (
    <Card className="flex min-h-0 flex-1 flex-col p-4">
      <h3 className="mb-3 text-sm font-semibold text-navy dark:text-foreground">
        Chi tiết Yêu cầu mua hàng theo dòng hàng{' '}
        <span className="font-normal text-muted-foreground">
          (soi mã hàng chưa được đặt để không đặt sót đơn)
        </span>
      </h3>
      <DataTable
        columns={columns}
        rows={data?.items ?? []}
        getRowId={(row) => String(row.id)}
        isLoading={isLoading}
        isError={isError}
        emptyMessage={filtersActive ? 'Không có dòng khớp bộ lọc.' : 'Chưa có dữ liệu.'}
        storageKey="procurement.purchase-report.pr-lines"
        //  Bộ lọc của BẢNG này nằm ở state cục bộ chứ không lên URL. Năm / công
        //  ty là bộ lọc của cả trang (đầu trang hoặc trang riêng), không khai ở đây.
        filtersActive={filtersActive}
        onResetFilters={() => {
          setStatus(ALL)
          setLineStatus(ALL)
          setAssignee(ALL)
          setSearchDraft('')
          setSearch('')
        }}
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
            <Input
              className="w-52"
              placeholder="Mã hàng / tên SP / mã PYC"
              value={searchDraft}
              onChange={(event) => setSearchDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') commitSearch()
              }}
              onBlur={commitSearch}
            />

            <Select value={lineStatus} onValueChange={setLineStatus}>
              <SelectTrigger className="w-52">
                <SelectValue placeholder="Tiến độ" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>Tất cả tiến độ</SelectItem>
                {LINE_STATUS_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="w-44">
                <SelectValue placeholder="Trạng thái" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
                {Object.entries(PR_STATUS_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={assignee} onValueChange={setAssignee}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="NSTM" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>Tất cả NSTM</SelectItem>
                {(data?.assignees ?? []).map((item) => (
                  <SelectItem key={item.code} value={item.code}>
                    {item.name ? `${item.name} (${item.code})` : item.code}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </>
        }
      />
    </Card>
  )
}
