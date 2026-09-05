import { Search } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'

import { appConfig } from '@/core/config/app-config'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlRangeParam } from '@/shared/hooks/use-url-range-param'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Card } from '@/shared/ui/card'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Tabs, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { PO_PROGRESS_STATUS } from '@/shared/constants/statuses'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { cn } from '@/shared/utils/cn'
import { DocumentStatusBadge, ProgressStatusBadge } from '../components/document-status-badge'
import { SurveyQuotingPanel } from '../components/survey-quoting-panel'
import { usePurchaseProgress } from '../hooks/use-purchase-documents'
import type { PurchaseProgressRow } from '../types/purchase-progress'

const ALL = 'all'

/**
 * P6-6 (bao-CR-284): màn GỘP — bộ lọc theo BƯỚC của luồng mua hàng (doc/erp/12 §2.7).
 * "Đang so giá" là bảng dòng YCBG chưa lên đơn (`SurveyQuotingPanel`, đọc
 * `/api/survey-progress?phase=quoting`); ba bước còn lại là bảng ĐMH này, trong đó
 * "Đang mua"/"Đang nhận hàng" gửi `step=` để backend lọc theo NHÓM mã tiến độ.
 */
const STEPS = [
  { value: ALL, label: 'Tất cả đơn hàng' },
  { value: 'quoting', label: 'Đang so giá' },
  { value: 'purchasing', label: 'Đang mua' },
  { value: 'receiving', label: 'Đang nhận hàng' },
] as const

/**
 * Khoảng ngày lọc theo MỐC nào. Một dòng ở đây là MỘT LẦN GIAO, nên hai mốc lệch
 * nhau thật: đơn đặt tháng 7 mà giao làm ba đợt thì cùng một dòng đặt hàng nằm
 * rải khắp tháng 8-9. Hỏi "đặt trong kỳ" và "nhận trong kỳ" ra hai tập khác hẳn.
 *
 * Mặc định là NGÀY ĐẶT HÀNG — đó là mốc của chứng từ, cũng là cột bảng đang xếp
 * theo. Backend đọc sẵn cả hai cặp (`purchase_progress/controller.py`).
 */
const DATE_FIELDS = [
  { value: 'order', label: 'Theo ngày ĐH', from: 'order_date_from', to: 'order_date_to' },
  {
    value: 'received',
    label: 'Theo ngày nhận',
    from: 'received_date_from',
    to: 'received_date_to',
  },
] as const

const DEFAULT_DATE_FIELD = DATE_FIELDS[0].value

/**
 * Tiến độ mua hàng — báo cáo phẳng theo TỪNG LẦN GIAO của từng dòng đơn hàng,
 * không phải danh sách chứng từ.
 *
 * Endpoint `/api/purchase-progress` KHÔNG chạy qua `apply_filters` mà tự đọc bộ
 * tham số riêng (`company_id`, `department_id`, `status`, `q`, các cặp ngày…) nên
 * màn này không dùng "Bộ lọc điều kiện" như các danh sách khác.
 */
export function PurchaseProgressPage() {
  const [step, setStep] = useUrlParamState('step', ALL)
  //  URL sửa tay ra bước không có thật thì về "Tất cả" — đừng ném lỗi, cũng đừng
  //  hiện tab nào đó đang chọn mà bảng lại bày tập khác.
  const activeStep = STEPS.some((item) => item.value === step) ? step : ALL

  return (
    <PageContainer fill>
      <PageHeader
        title="Tiến độ mua hàng"
        description="Theo dõi cả luồng mua theo từng bước: so giá, đặt hàng, nhận hàng."
      />

      <Tabs value={activeStep} onValueChange={setStep}>
        <TabsList>
          {STEPS.map((item) => (
            <TabsTrigger key={item.value} value={item.value}>
              {item.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        {activeStep === 'quoting' ? (
          <SurveyQuotingPanel />
        ) : (
          <PurchaseOrderProgressTable step={activeStep} />
        )}
      </Card>
    </PageContainer>
  )
}

function PurchaseOrderProgressTable({ step }: { step: string }) {
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  // CR-088: lọc theo ID phòng ban. Gửi TÊN thì phòng đổi tên là bộ lọc trượt sạch,
  // danh sách rỗng mà không báo gì. Backend vẫn nhận `department=<tên>` cho các
  // đường dẫn cũ đã lưu, chỉ có màn này thôi không gửi nữa.
  const [departmentId, setDepartmentId] = useUrlParamState('department_id', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [dateField, setDateField] = useUrlParamState('date_field', DEFAULT_DATE_FIELD)
  const [dateFrom, dateTo, setDateRange] = useUrlRangeParam('date_from', 'date_to')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const { data: companies } = useCompanies({ page_size: 500, is_active: true })
  const { data: departments } = useDepartments({ page_size: 500, is_active: true })

  const [page, setPage] = usePageResetOnFilterChange([
    step,
    debouncedValue,
    companyId,
    departmentId,
    status,
    dateField,
    dateFrom,
    dateTo,
  ])

  const params: ListParams = { page, page_size: pageSize }
  if (step !== ALL) params.step = step
  if (debouncedValue) params.q = debouncedValue
  if (companyId !== ALL) params.company_id = Number(companyId)
  if (departmentId !== ALL) params.department_id = Number(departmentId)
  if (status !== ALL) params.status = status
  if (dateFrom || dateTo) {
    const field = DATE_FIELDS.find((item) => item.value === dateField) ?? DATE_FIELDS[0]
    if (dateFrom) params[field.from] = dateFrom
    if (dateTo) params[field.to] = dateTo
  }

  const { data, isLoading, isError } = usePurchaseProgress(params)

  // Không có quyền `supplier.read` thì backend xóa trắng cột NCC / vận chuyển —
  // ẩn luôn cho khỏi bày ra một loạt ô rỗng.
  const showSupplier = data?.show_supplier ?? true
  // useCallback để đưa được vào deps của `columns` mà không phá memo:
  // hàm khai báo thẳng trong thân component sẽ đổi danh tính mỗi lần render.
  const companyName = useCallback(
    (id: number) => (companies?.items ?? []).find((company) => company.id === id)?.name ?? '',
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
        //  `wrap` cho cột chữ: khách cần ĐỌC ĐỦ, không phải đoán qua dấu "…"
        //  (khách nêu 31/08/2026). Cột số và cột ngày để nguyên một dòng, kẻo
        //  hàng cao lệch nhau nhìn rối. Lưu ý: gắn `truncate` trong `cell` là
        //  vô hiệu hóa `wrap` — class ô con thắng lớp bọc của bảng.
        wrap: true,
        cell: (row) => <span className="font-medium">{row.po_code}</span>,
      },
      {
        key: 'misa_code',
        header: 'Mã MISA',
        width: 120,
        defaultHidden: true,
        wrap: true,
        cell: (r) => r.misa_code || '',
      },
      { key: 'pr_code', header: 'Mã PYC', width: 130, wrap: true, cell: (r) => r.pr_code || '' },
      // P6-5 (bao-CR-283): giai đoạn hai nguồn — đơn cũ bám YCMH (pr_code), đơn mới
      // lên thẳng từ phiếu YCBG gộp (survey_code, pr_code rỗng). Bày cả hai cột cạnh
      // nhau để nhìn một dòng là biết đơn về từ nguồn nào.
      {
        key: 'survey_code',
        header: 'Mã YCBG',
        width: 130,
        wrap: true,
        cell: (r) => r.survey_code || '',
      },
      {
        key: 'company',
        header: 'Công ty',
        width: 190,
        wrap: true,
        cell: (r) => companyName(r.company_id),
      },
      {
        key: 'department',
        header: 'Bộ phận',
        width: 150,
        wrap: true,
        cell: (r) => r.department || '',
      },
      {
        key: 'supplier_name',
        header: 'Nhà cung cấp',
        width: 230,
        supplierOnly: true,
        wrap: true,
        cell: (r) => r.supplier_name || r.supplier_code || '',
      },
      { key: 'nspt', header: 'NSPT', width: 160, wrap: true, cell: (r) => r.nspt || '' },
      {
        key: 'order_date',
        header: 'Ngày ĐH',
        width: 110,
        cell: (r) => formatDate(r.order_date) || '',
      },
      {
        key: 'product_code',
        header: 'Mã SP',
        width: 150,
        wrap: true,
        cell: (r) => r.product_code || '',
      },
      {
        key: 'product_name',
        header: 'Tên SP',
        width: 240,
        wrap: true,
        cell: (r) => r.product_name || '',
      },
      {
        key: 'item_group',
        header: 'Nhóm hàng',
        width: 150,
        defaultHidden: true,
        wrap: true,
        cell: (r) => r.item_group || '',
      },
      { key: 'unit', header: 'ĐVT', width: 80, cell: (r) => r.unit || '' },
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
      {
        key: 'delivery_no',
        header: 'Lần giao',
        width: 100,
        align: 'right',
        defaultHidden: true,
        cell: (r) => r.delivery_no ?? '',
      },
      {
        key: 'warehouse_code',
        header: 'Kho',
        width: 120,
        defaultHidden: true,
        wrap: true,
        cell: (r) => r.warehouse_code || '',
      },
      {
        key: 'carrier_name',
        header: 'Đơn vị VC',
        width: 180,
        defaultHidden: true,
        supplierOnly: true,
        wrap: true,
        cell: (r) => r.carrier_name || '',
      },
      {
        key: 'received_qty',
        header: 'SL nhận',
        width: 110,
        align: 'right',
        cell: (r) => <span className="tabular-nums">{formatQuantity(r.received_qty) || 0}</span>,
      },
      {
        key: 'received_date',
        header: 'Ngày nhận',
        width: 120,
        cell: (r) => formatDate(r.received_date) || '',
      },
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
        cell: (r) => <span className="font-medium tabular-nums">{formatMoney(r.amount) || 0}</span>,
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
            <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="h-9 pl-9 text-xs"
              placeholder="Tìm mã ĐMH, MISA, PYC, YCBG, NCC, NSPT, mã/tên sản phẩm…"
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

          <Select value={departmentId} onValueChange={setDepartmentId}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Bộ phận" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>Tất cả bộ phận</SelectItem>
              {(departments?.items ?? []).map((item) => (
                <SelectItem key={item.id} value={String(item.id)}>
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
              {PO_PROGRESS_STATUS.map((item) => (
                <SelectItem key={item.value} value={item.value}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/*  Chọn MỐC trước, rồi tới khoảng ngày — đọc xuôi thành một câu
                   "theo ngày nhận, từ … tới …". Hai ô đứng liền nhau để không ai
                   lọc nhầm mốc mà không để ý. */}
          <Select value={dateField} onValueChange={setDateField}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Mốc ngày" />
            </SelectTrigger>
            <SelectContent>
              {DATE_FIELDS.map((field) => (
                <SelectItem key={field.value} value={field.value}>
                  {field.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <DateRangePicker
            from={dateFrom}
            to={dateTo}
            onChange={setDateRange}
            placeholder="Từ ngày – tới ngày"
          />
        </>
      }
    />
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
