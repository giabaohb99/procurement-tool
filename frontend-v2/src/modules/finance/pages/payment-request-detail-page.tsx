import { ArrowLeft, Ban, Banknote, Check, Info, Loader2, Plus, Printer, Save, Send, Undo2 } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { useQuery } from '@tanstack/react-query'

import { usePermission } from '@/core/authorization/use-permission'
import { DocumentAttachmentsCard } from '@/modules/procurement/components/document-attachments-card'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useSuppliers } from '@/modules/production/hooks/use-suppliers'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { queryKeys } from '@/shared/constants/query-keys'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/shared/ui/alert-dialog'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { DatePicker } from '@/shared/ui/date-picker'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { ErrorState } from '@/shared/ui/error-state'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { PageContainer } from '@/shared/ui/page-container'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { ReasonConfirmDialog } from '@/shared/ui/reason-confirm-dialog'
import { SearchSelect } from '@/shared/ui/search-select'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { payableApi } from '../api/payable-api'
import {
  PaymentRequestLinesTable,
  type EditablePaymentLine,
} from '../components/payment-request-lines-table'
import { PaymentRequestStatusBadge } from '../components/payment-request-status-badge'
import {
  useCreatePaymentRequests,
  useDeletePaymentRequest,
  usePaymentRequest,
  usePaymentRequestAction,
  usePrepayHanging,
  useRefundPrepay,
  useUpdatePaymentRequest,
} from '../hooks/use-payment-requests'
import type { Payable } from '../types/payable'
import {
  PAYMENT_METHOD_LABELS,
  PAYMENT_SOURCE_LABELS,
  type PaymentMethod,
  type PaymentRequestCreateInput,
  type PaymentRequestLine,
  type PrintTexts,
} from '../types/payment-request'
import { autoPrintText } from '../utils/print-texts'

/**
 * Chi tiết / tạo mới Yêu cầu thanh toán (YCTT).
 *
 * `/new` KHÔNG phải phiếu đã tạo mà là màn NHẬP LIỆU — chỉ ghi DB khi bấm "Tạo
 * phiếu"; rời màn giữa chừng không sinh phiếu nháp nào (CR-025). Vì thế trang tách
 * hẳn hai nhánh: TẠO (từ Công nợ hoặc form trắng) và XEM/SỬA (một phiếu đã có).
 */
export function PaymentRequestDetailPage() {
  const { id } = useParams()
  const isNew = !id || id === 'new'

  return isNew ? <PaymentRequestCreate /> : <PaymentRequestView paymentRequestId={Number(id)} />
}

/** Khóa React ổn định cho dòng chưa lưu — chưa có id server. */
let lineSeq = 0
function nextKey(): string {
  lineSeq += 1
  return `pr-line-${lineSeq}`
}

/** Dòng trống (form trắng) — chưa gắn khoản nợ nào. */
function blankLine(): EditablePaymentLine {
  return {
    key: nextKey(),
    payable_id: 0,
    supplier_code: '',
    supplier_name: '',
    source_type: '',
    po_code: '',
    invoice_no: '',
    invoice_date: '',
    due_date: '',
    payable_total: 0,
    payable_paid: 0,
    amount: 0,
    offset_amount: 0,
  }
}

/**
 * Một khoản Công nợ đã tick -> một dòng phiếu.
 *
 * Công nợ KHÔNG trả `invoice_date` (bảng sinh ngầm lúc nhận hàng, chưa gắn ngày
 * hóa đơn), nên để trống cho người lập điền — khớp `_out()` của controller.
 */
function fromPayable(row: Payable): EditablePaymentLine {
  return {
    key: nextKey(),
    payable_id: row.id,
    supplier_code: row.supplier_code,
    supplier_name: row.supplier_name,
    source_type: row.source_type || 'goods',
    po_code: row.po_code,
    invoice_no: row.invoice_no,
    invoice_date: '',
    due_date: row.due_date,
    payable_total: Number(row.total) || 0,
    payable_paid: Number(row.paid_amount) || 0,
    amount: Number(row.remaining) || 0,
    offset_amount: 0,
  }
}

/** Dòng của phiếu đã lưu -> hình dạng dòng sửa được. */
function fromRequestLine(line: PaymentRequestLine, index: number): EditablePaymentLine {
  return {
    key: line.id ? `pr-line-saved-${line.id}` : `pr-line-new-${index}`,
    payable_id: line.payable_id,
    supplier_code: '',
    supplier_name: '',
    source_type: '',
    po_code: line.po_code,
    invoice_no: line.invoice_no,
    invoice_date: line.invoice_date,
    due_date: line.due_date,
    payable_total: line.payable_total,
    payable_paid: line.payable_paid,
    amount: line.amount,
    offset_amount: line.offset_amount ?? 0,
  }
}

/** Ngày hôm nay dạng `yyyy-mm-dd` cho ô Ngày lập mặc định. */
function today(): string {
  return new Date().toISOString().slice(0, 10)
}

/**
 * Màn TẠO. Hai lối vào:
 *  - từ màn Công nợ (`?payables=1,2,3` + `state.rows`): nạp sẵn các khoản đã tick;
 *  - FORM TRẮNG (CR-066): tự chọn NCC / công ty / loại nợ rồi gõ tay từng dòng.
 * Server tách mỗi (NCC × loại nợ) thành một phiếu riêng nên một lần bấm có thể
 * sinh nhiều phiếu — hiện trước con số để người lập biết.
 */
function PaymentRequestCreate() {
  const navigate = useNavigate()
  const location = useLocation()
  const { can } = usePermission()
  const [searchParams] = useSearchParams()

  const idsParam = searchParams.get('payables') ?? ''
  const ids = useMemo(() => idsParam.split(',').map(Number).filter(Boolean), [idsParam])
  const blankMode = ids.length === 0

  const navState = location.state as { rows?: Payable[]; prepay?: boolean } | null
  const stateRows = navState?.rows

  // F5 / mở bằng link: mất state điều hướng -> nạp lại đúng các khoản đã tick.
  const needRefetch = ids.length > 0 && !stateRows?.length
  const { data: refetched, isLoading: loadingPayables } = useQuery({
    queryKey: queryKeys.finance.payables({ ids: idsParam, year: 'all', page_size: 500 }),
    queryFn: () => payableApi.list({ ids: idsParam, year: 'all', page_size: 500 }),
    enabled: needRefetch,
  })

  const { data: suppliersData } = useSuppliers(
    { page_size: 1000, is_active: true },
    { enabled: blankMode && can('supplier', 'read') },
  )
  const { data: companiesData } = useCompanies({ page_size: 500, is_active: true }, { enabled: blankMode })

  const [lines, setLines] = useState<EditablePaymentLine[]>(() => {
    if (stateRows?.length) return stateRows.map(fromPayable)
    if (blankMode) return [blankLine()]
    return []
  })
  const [requestDate, setRequestDate] = useState<string>(() => today())
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('transfer')
  const [note, setNote] = useState('')
  const [supplierCode, setSupplierCode] = useState<string>(() => stateRows?.[0]?.supplier_code ?? '')
  const [companyId, setCompanyId] = useState<number>(() => stateRows?.[0]?.company_id ?? 0)
  const [sourceType, setSourceType] = useState<string>(() => stateRows?.[0]?.source_type ?? 'goods')
  // CR-268 — phiếu THANH TOÁN TRƯỚC: đi từ hộp thoại "Lập thanh toán trước" của ĐMH
  // (CR-267) thì tick sẵn; form trắng thì kế toán tự tick khi tạm ứng NCC.
  const [prepay, setPrepay] = useState<boolean>(() => Boolean(navState?.prepay))

  // Khoản nợ nạp về sau (F5) -> đổ vào bảng đúng một lần.
  const refetchedChanged = useHasChanged(refetched)
  if (refetchedChanged && refetched) setLines(refetched.items.map(fromPayable))

  const createMutation = useCreatePaymentRequests()

  // Dòng gõ tay bám vào NCC nào: form trắng theo ô đã chọn, đi từ Công nợ theo khoản nợ đầu tiên.
  const headPayableLine = lines.find((line) => line.payable_id)
  const headSupplier = blankMode ? supplierCode : (headPayableLine?.supplier_code ?? '')
  const headSource = blankMode ? sourceType : (headPayableLine?.source_type ?? 'goods')

  const groupCount = useMemo(() => {
    const set = new Set<string>()
    lines.forEach((line) =>
      set.add(line.payable_id ? `${line.supplier_code}||${line.source_type}` : `${headSupplier}||${headSource}`),
    )
    return set.size
  }, [lines, headSupplier, headSource])

  const noInvoiceCount = lines.filter((line) => !line.invoice_no.trim()).length
  const total = useMemo(() => lines.reduce((sum, line) => sum + (Number(line.amount) || 0), 0), [lines])

  // CR-260 — NCC còn tiền treo cấp NCC (không gắn đơn) thì mở thêm cột "Cấn trừ trả
  // trước": người lập GHI Ý ĐỊNH cấn trừ lên dòng, backend thực thi khi phiếu được
  // Duyệt. Phiếu trả trước (prepay) là phiếu SINH treo nên không có cột này.
  const { data: hangingData } = usePrepayHanging(
    { supplier_code: headSupplier, unlinked: 1, source_type: headSource },
    { enabled: !prepay && Boolean(headSupplier) && can('payment_request', 'read') },
  )
  const hangingAvailable = hangingData?.total ?? 0
  const offsetTotal = useMemo(
    () => lines.reduce((sum, line) => sum + (Number(line.offset_amount) || 0), 0),
    [lines],
  )
  const showOffsetColumn = !prepay && (hangingAvailable > 0.01 || offsetTotal > 0.01)

  const supplierName = (code: string) =>
    (suppliersData?.items ?? []).find((supplier) => supplier.code === code)?.name

  function supplierDisplay(row: EditablePaymentLine): string {
    if (row.payable_id) return row.supplier_name || row.supplier_code
    return supplierName(headSupplier) ?? headPayableLine?.supplier_name ?? headSupplier
  }

  function sourceDisplay(row: EditablePaymentLine): string {
    const source = row.payable_id ? row.source_type : headSource
    return PAYMENT_SOURCE_LABELS[source] ?? source
  }

  function patchLine(index: number, patch: Partial<EditablePaymentLine>) {
    setLines((current) => current.map((line, i) => (i === index ? { ...line, ...patch } : line)))
  }

  function removeLine(index: number) {
    setLines((current) => current.filter((_, i) => i !== index))
  }

  async function handleCreate() {
    if (!lines.length) {
      toast.error('Chưa có dòng nào để tạo phiếu')
      return
    }
    if (!headSupplier) {
      toast.error('Chưa chọn nhà cung cấp')
      return
    }
    const payload: PaymentRequestCreateInput = {
      request_date: requestDate,
      note,
      payment_method: paymentMethod,
      supplier_code: headSupplier,
      company_id: companyId,
      source_type: headSource,
      // CR-268 — phiếu trả trước: backend miễn khớp công nợ lúc gửi duyệt, tiền
      // đã chi trở thành TIỀN TREO chờ đối trừ.
      prepay: prepay ? 1 : 0,
      lines: lines.map((line) => ({
        payable_id: line.payable_id,
        po_code: line.po_code,
        invoice_no: line.invoice_no,
        invoice_date: line.invoice_date,
        amount: Number(line.amount) || 0,
        // CR-260 — chỉ là Ý ĐỊNH cấn trừ, backend thực thi khi phiếu được Duyệt.
        offset_amount: prepay ? 0 : Number(line.offset_amount) || 0,
      })),
    }
    try {
      const created = await createMutation.mutateAsync(payload)
      toast.success(
        created.length === 1
          ? 'Đã tạo yêu cầu thanh toán'
          : `Đã tạo ${created.length} phiếu yêu cầu thanh toán (mỗi nhà cung cấp một phiếu).`,
      )
      if (created.length === 1) {
        navigate(appRoutes.finance.paymentRequestDetail(created[0].id), { replace: true })
      } else {
        navigate(appRoutes.finance.paymentRequests, { replace: true })
      }
    } catch {
      // httpClient đã tự toast lỗi non-GET — không toast lại ở đây.
    }
  }

  if (needRefetch && loadingPayables) {
    return (
      <PageContainer>
        <Skeleton className="mb-4 h-16 w-full" />
        <Skeleton className="h-[420px] w-full" />
      </PageContainer>
    )
  }

  return (
    <PageContainer className="bg-slate-50/70 lg:p-4">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Button variant="outline" size="icon" asChild aria-label="Về danh sách yêu cầu thanh toán">
          <Link to={appRoutes.finance.paymentRequests}>
            <ArrowLeft />
          </Link>
        </Button>
        <h1 className="text-xl font-semibold tracking-tight text-navy dark:text-foreground">
          Tạo yêu cầu thanh toán
        </h1>
        <Badge variant="secondary" className="border-0">
          Chưa lưu
        </Badge>

        <div className="min-w-4 flex-1" />
        <div className="flex flex-wrap items-center justify-end gap-2">
          {blankMode && (
            <Button variant="outline" asChild>
              <Link to={appRoutes.finance.payables}>
                <Banknote />
                Chọn từ Công nợ
              </Link>
            </Button>
          )}
          <Button onClick={() => void handleCreate()} disabled={createMutation.isPending || !lines.length}>
            {createMutation.isPending ? <Loader2 className="animate-spin" /> : <Check />}
            {groupCount > 1 ? `Tạo ${groupCount} phiếu` : 'Tạo phiếu'}
          </Button>
        </div>
      </div>

      <p className="mb-4 flex items-start gap-2 rounded-md border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
        <Info className="mt-0.5 size-4 shrink-0" />
        <span>
          Soát lại số tiền đề nghị rồi bấm <b>Tạo phiếu</b> (rời màn này sẽ không lưu nháp).
          {groupCount > 1 && (
            <>
              {' '}
              Tự động tách thành <b>{groupCount} phiếu</b> theo từng nhà cung cấp / loại nợ.
            </>
          )}
          {noInvoiceCount > 0 && (
            <> · Dòng chưa có số hóa đơn có thể in nháp để ký tay (cần điền đủ khi gửi duyệt).</>
          )}
        </span>
      </p>

      {showOffsetColumn && (
        <p className="mb-4 flex items-start gap-2 rounded-md border border-info/30 bg-info/8 px-3 py-2 text-sm">
          <Info className="mt-0.5 size-4 shrink-0 text-info" />
          <span>
            Nhà cung cấp này còn <b className="tabular-nums">{formatMoney(hangingAvailable)}</b> tiền
            treo trả trước (không gắn đơn). Muốn dùng thì ghi số vào cột{' '}
            <b>Cấn trừ trả trước</b> — phần này chỉ là đề nghị trên phiếu, kế toán bấm{' '}
            <b>Duyệt</b> mới cấn trừ thật vào công nợ.
          </span>
        </p>
      )}

      <div className="min-w-0 space-y-4">
        <Card className="gap-4 py-4">
          <CardHeader className="min-h-9 border-b px-4 pb-3!">
            <CardTitle className="text-base text-navy dark:text-foreground">Thông tin phiếu</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 px-4 sm:grid-cols-2 lg:grid-cols-3">
            {blankMode && (
              <>
                <div className="space-y-1.5">
                  <Label>Nhà cung cấp</Label>
                  <SearchSelect
                    value={supplierCode}
                    onChange={setSupplierCode}
                    options={(suppliersData?.items ?? []).map((supplier) => ({
                      value: supplier.code,
                      label: `${supplier.code} — ${supplier.name}`,
                    }))}
                    placeholder="Chọn/tìm nhà cung cấp…"
                    clearable
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Công ty</Label>
                  <SearchSelect
                    value={companyId ? String(companyId) : ''}
                    onChange={(value) => setCompanyId(Number(value) || 0)}
                    options={(companiesData?.items ?? []).map((company) => ({
                      value: String(company.id),
                      label: company.name,
                    }))}
                    placeholder="Chọn/tìm công ty…"
                    clearable
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Loại công nợ</Label>
                  <Select value={sourceType} onValueChange={setSourceType}>
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(PAYMENT_SOURCE_LABELS).map(([value, label]) => (
                        <SelectItem key={value} value={value}>
                          {label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}
            <div className="space-y-1.5">
              <Label>Ngày lập</Label>
              <DatePicker value={requestDate} onChange={setRequestDate} />
            </div>
            <div className="space-y-1.5">
              <Label>Hình thức thanh toán</Label>
              <Select value={paymentMethod} onValueChange={(value) => setPaymentMethod(value as PaymentMethod)}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(PAYMENT_METHOD_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">{paymentMethodHint(paymentMethod)}</p>
            </div>
            {/* CR-149 (thay CR-146) từng BỎ ô chọn prepay vì lúc đó cờ chỉ đổi câu chữ
                bản in. CR-268 đưa lại dưới dạng ô tick với NGHĨA THẬT: phiếu trả trước
                được miễn cổng khớp công nợ (CR-066) và tiền đã chi thành TIỀN TREO. */}
            {/* Chỉ hiện ở FORM TRẮNG: tạo từ Công nợ nghĩa là trả cho khoản nợ có thật,
                tick trả trước ở đó là vô nghĩa. */}
            {blankMode && (
              <div className="flex items-start gap-2 sm:col-span-2 lg:col-span-3">
                <Checkbox
                  id="prepay-checkbox"
                  checked={prepay}
                  onCheckedChange={(checked) => setPrepay(checked === true)}
                  className="mt-0.5"
                />
                <div className="space-y-0.5">
                  <Label htmlFor="prepay-checkbox" className="cursor-pointer">
                    Thanh toán trước / tạm ứng nhà cung cấp
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    Phiếu KHÔNG cần khớp công nợ khi gửi duyệt. Sau khi chi, số tiền trở thành
                    &ldquo;tiền treo&rdquo;: dòng có mã ĐMH sẽ tự đối trừ khi đơn đó nhận hàng, dòng
                    không gắn đơn thì kế toán cấn trừ tay ở màn Công nợ hoặc ghi nhận NCC hoàn tiền.
                  </p>
                </div>
              </div>
            )}
            <div className="space-y-1.5 sm:col-span-2 lg:col-span-3">
              <Label>Ghi chú</Label>
              <Textarea
                value={note}
                onChange={(event) => setNote(event.target.value)}
                placeholder="Ghi chú áp dụng cho các phiếu được tạo…"
              />
            </div>
          </CardContent>
        </Card>

        <PaymentRequestLinesTable
          rows={lines}
          editable
          storageKey="finance.payment-request-create-lines"
          showSupplierColumns
          lockLinkedPo
          showOffsetColumn={showOffsetColumn}
          supplierDisplay={supplierDisplay}
          sourceDisplay={sourceDisplay}
          onPatch={patchLine}
          onRemove={removeLine}
        />

        <div className="flex flex-wrap items-center gap-3">
          <Button variant="outline" size="sm" onClick={() => setLines((current) => [...current, blankLine()])}>
            <Plus />
            Thêm dòng
          </Button>
          <div className="min-w-4 flex-1" />
          <span className="text-base text-navy dark:text-foreground">
            {offsetTotal > 0.01 && (
              <>
                Cấn trừ trả trước: <b className="tabular-nums">{formatMoney(offsetTotal)}</b>
                <span className="mx-2 text-muted-foreground">·</span>
              </>
            )}
            Tổng đề nghị thanh toán: <b className="tabular-nums">{formatMoney(total)}</b>
          </span>
        </div>
      </div>
    </PageContainer>
  )
}

/** Màn XEM / SỬA một phiếu đã có. Chỉ bản NHÁP mới sửa được (backend cũng chặn). */
function PaymentRequestView({ paymentRequestId }: { paymentRequestId: number }) {
  const navigate = useNavigate()
  const { can } = usePermission()

  const { data: req, isLoading, isError } = usePaymentRequest(paymentRequestId)
  const { data: companiesData } = useCompanies({ page_size: 500, is_active: true })

  const update = useUpdatePaymentRequest(paymentRequestId)
  const remove = useDeletePaymentRequest()
  const runAction = usePaymentRequestAction(paymentRequestId)
  const refundPrepay = useRefundPrepay(paymentRequestId)

  // CR-260 — treo cấp NCC còn lại: mở cột "Cấn trừ trả trước" khi sửa nháp và cho
  // người duyệt thấy treo có còn đủ trước khi gật. Duyệt xong thì thôi, khỏi gọi.
  const { data: hangingData } = usePrepayHanging(
    {
      supplier_code: req?.supplier_code ?? '',
      unlinked: 1,
      source_type: req?.source_type,
    },
    {
      enabled:
        Boolean(req && !req.prepay && ['draft', 'submitted'].includes(req.status)) &&
        can('payment_request', 'read'),
    },
  )

  const [lines, setLines] = useState<EditablePaymentLine[]>([])
  const [note, setNote] = useState('')
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('transfer')
  const [printTexts, setPrintTexts] = useState<PrintTexts>({})
  const [rejectOpen, setRejectOpen] = useState(false)
  const [payOpen, setPayOpen] = useState(false)
  // CR-268 — hộp "Ghi nhận NCC hoàn tiền" của phiếu trả trước còn treo.
  const [refundOpen, setRefundOpen] = useState(false)
  const [refundAmountText, setRefundAmountText] = useState('')
  const [refundNote, setRefundNote] = useState('')

  // Dữ liệu server về (hoặc lưu xong nạp lại) -> đổ lại bản nháp đang sửa.
  const reqChanged = useHasChanged(req)
  if (reqChanged && req) {
    setLines((req.lines ?? []).map(fromRequestLine))
    setNote(req.note ?? '')
    setPaymentMethod(req.payment_method ?? 'transfer')
    // CR-149: ĐIỀN SẴN câu tự động vào 3 ô "Nội dung bản in" — người dùng sửa
    // thẳng; xóa trống rồi lưu thì backend nhận "" và bản in rơi về câu tự động.
    const auto = autoPrintText(req)
    setPrintTexts({
      content: req.print_texts?.content || auto,
      line_desc: req.print_texts?.line_desc || auto,
      transfer: req.print_texts?.transfer || auto,
    })
  }

  if (isLoading) {
    return (
      <PageContainer>
        <Skeleton className="mb-4 h-16 w-full" />
        <Skeleton className="h-[420px] w-full" />
      </PageContainer>
    )
  }

  if (isError || !req) {
    return (
      <ErrorState
        title="Không mở được yêu cầu thanh toán"
        description="Phiếu có thể đã bị xóa, hoặc ngoài phạm vi dữ liệu bạn được xem."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.finance.paymentRequests)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  const editable = req.status === 'draft' && can('payment_request', 'write')
  // CR-149: câu chữ bản in sửa được cả khi phiếu Chờ duyệt / Đã duyệt (người dùng
  // in sau khi duyệt) — backend chỉ nhận PATCH *chỉ chứa* print_texts ở 2 trạng thái đó.
  const printTextsEditable =
    ['draft', 'submitted', 'approved'].includes(req.status) && can('payment_request', 'write')
  const companyName =
    (companiesData?.items ?? []).find((company) => company.id === req.company_id)?.name ?? '—'
  const total = lines.reduce((sum, line) => sum + (Number(line.amount) || 0), 0)
  const unmatchedCount = (req.lines ?? []).filter((line) => !line.matched).length

  // CR-268 — phiếu TRẢ TRƯỚC đã chi: cộng ba con số từ chính dòng phiếu (backend
  // trả kèm `allocated_amount` / `refunded_amount` / `hanging` trên mỗi dòng).
  const isPrepay = Boolean(req.prepay)
  const prepayLines = req.lines ?? []
  const allocatedTotal = prepayLines.reduce((sum, line) => sum + (line.allocated_amount ?? 0), 0)
  const refundedTotal = prepayLines.reduce((sum, line) => sum + (line.refunded_amount ?? 0), 0)
  const hangingTotal = prepayLines.reduce((sum, line) => sum + (line.hanging ?? 0), 0)
  const showPrepayCard = isPrepay && req.status === 'paid'
  const canRefund = showPrepayCard && hangingTotal > 0.01 && can('payment_request', 'write')

  // CR-260 — phần CẤN TRỪ tiền treo ghi trên dòng phiếu: nháp/chờ duyệt là Ý ĐỊNH,
  // bấm Duyệt backend mới thực thi. Cột chỉ hiện khi có gì để nhìn: phiếu đã mang
  // phần cấn trừ, hoặc đang sửa nháp mà NCC còn treo để dùng.
  const hangingAvailable = hangingData?.total ?? 0
  const offsetTotal = lines.reduce((sum, line) => sum + (Number(line.offset_amount) || 0), 0)
  const showOffsetColumn = !isPrepay && (offsetTotal > 0.01 || (editable && hangingAvailable > 0.01))

  function patchLine(index: number, patch: Partial<EditablePaymentLine>) {
    setLines((current) => current.map((line, i) => (i === index ? { ...line, ...patch } : line)))
  }

  function removeLine(index: number) {
    setLines((current) => current.filter((_, i) => i !== index))
  }

  async function handleSave() {
    await update.mutateAsync({
      request_date: req?.request_date,
      note,
      payment_method: paymentMethod,
      print_texts: printTexts,
      lines: lines.map((line) => ({
        payable_id: line.payable_id,
        po_code: line.po_code,
        invoice_no: line.invoice_no,
        invoice_date: line.invoice_date,
        amount: Number(line.amount) || 0,
        // CR-260 — ý định cấn trừ, thực thi khi Duyệt.
        offset_amount: Number(line.offset_amount) || 0,
      })),
    })
  }

  const noop = () => ''

  return (
    <PageContainer className="bg-slate-50/70 lg:p-4">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Button variant="outline" size="icon" asChild aria-label="Về danh sách yêu cầu thanh toán">
          <Link to={appRoutes.finance.paymentRequests}>
            <ArrowLeft />
          </Link>
        </Button>
        <h1 className="text-xl font-semibold tracking-tight text-navy dark:text-foreground">
          Yêu cầu thanh toán {req.code || ''}
        </h1>
        <PaymentRequestStatusBadge status={req.status} />
        {isPrepay && (
          <Badge variant="secondary" className="border-0 bg-info/10 text-info">
            Trả trước
          </Badge>
        )}

        <div className="min-w-4 flex-1" />
        <div className="flex flex-wrap items-center justify-end gap-2">
          {can('payment_request', 'print') && (
            <Button variant="outline" asChild>
              <Link
                to={appRoutes.finance.paymentRequestPrint(req.id)}
                target="_blank"
                rel="noreferrer"
              >
                <Printer />
                In phiếu
              </Link>
            </Button>
          )}

          {editable && (
            <Button onClick={() => void handleSave()} disabled={update.isPending}>
              {update.isPending ? <Loader2 className="animate-spin" /> : <Save />}
              Lưu
            </Button>
          )}

          {req.status === 'draft' && can('payment_request', 'write') && (
            <Button variant="outline" onClick={() => runAction.mutate({ action: 'submit' })} disabled={runAction.isPending}>
              <Send />
              Gửi duyệt
            </Button>
          )}

          {req.status === 'submitted' && can('payment_request', 'approve') && (
            <>
              <Button onClick={() => runAction.mutate({ action: 'approve' })} disabled={runAction.isPending}>
                <Check />
                Duyệt
              </Button>
              <Button
                variant="outline"
                className="text-destructive hover:text-destructive"
                onClick={() => setRejectOpen(true)}
              >
                <Ban />
                Từ chối
              </Button>
            </>
          )}

          {req.status === 'approved' && can('payment_request', 'write') && (
            <Button onClick={() => setPayOpen(true)} disabled={runAction.isPending}>
              <Banknote />
              Ghi nhận đã chi
            </Button>
          )}

          {editable && can('payment_request', 'delete') && (
            <DeleteConfirmButton
              recordName={req.code || `#${req.id}`}
              pending={remove.isPending}
              warning="Phiếu và các dòng khoản nợ kèm theo sẽ bị xóa."
              onConfirm={async () => {
                await remove.mutateAsync(req.id)
                navigate(appRoutes.finance.paymentRequests)
              }}
            />
          )}
        </div>
      </div>

      {req.status === 'cancelled' && req.reject_reason && (
        <p className="mb-4 flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/8 px-3 py-2 text-sm text-destructive">
          <Info className="mt-0.5 size-4 shrink-0" />
          <span>
            <b>Lý do từ chối:</b> {req.reject_reason}
          </span>
        </p>
      )}

      <div className="min-w-0 space-y-4">
        <Card className="gap-4 py-4">
          <CardHeader className="min-h-9 border-b px-4 pb-3!">
            <CardTitle className="text-base text-navy dark:text-foreground">Thông tin phiếu</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 px-4 sm:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-1.5">
              <Label>Nhà cung cấp</Label>
              <ReadOnlyValue>{req.supplier_name || req.supplier_code}</ReadOnlyValue>
            </div>
            <div className="space-y-1.5">
              <Label>Loại công nợ</Label>
              <ReadOnlyValue>{PAYMENT_SOURCE_LABELS[req.source_type] ?? req.source_type}</ReadOnlyValue>
            </div>
            <div className="space-y-1.5">
              <Label>Công ty</Label>
              <ReadOnlyValue>{companyName}</ReadOnlyValue>
            </div>
            <div className="space-y-1.5">
              <Label>Người yêu cầu</Label>
              <ReadOnlyValue>{req.created_by_name}</ReadOnlyValue>
            </div>
            <div className="space-y-1.5">
              <Label>Ngày lập</Label>
              <ReadOnlyValue>{formatDate(req.request_date)}</ReadOnlyValue>
            </div>
            <div className="space-y-1.5">
              <Label>Hình thức thanh toán</Label>
              {editable ? (
                <Select
                  value={paymentMethod}
                  onValueChange={(value) => setPaymentMethod(value as PaymentMethod)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(PAYMENT_METHOD_LABELS).map(([value, label]) => (
                      <SelectItem key={value} value={value}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <ReadOnlyValue>{PAYMENT_METHOD_LABELS[req.payment_method] ?? req.payment_method}</ReadOnlyValue>
              )}
              <p className="text-xs text-muted-foreground">
                {paymentMethodHint(editable ? paymentMethod : req.payment_method)}
                {editable && ' Nhớ bấm Lưu sau khi đổi.'}
              </p>
            </div>
            {/* CR-149 (thay CR-146): ô chọn prepay đã BỎ — câu chữ bản in sửa thẳng ở
                khối "Nội dung bản in" phía dưới cụm Chứng từ. */}
            <div className="space-y-1.5 sm:col-span-2 lg:col-span-3">
              <Label>Ghi chú</Label>
              {editable ? (
                <Textarea value={note} onChange={(event) => setNote(event.target.value)} />
              ) : (
                <ReadOnlyValue multiline>{req.note}</ReadOnlyValue>
              )}
            </div>
          </CardContent>
        </Card>

        {editable && unmatchedCount > 0 && (
          <p className="flex items-start gap-2 rounded-md border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
            <Info className="mt-0.5 size-4 shrink-0" />
            <span>
              {unmatchedCount} dòng chưa khớp khoản nợ: có thể in nháp để ký tay, cần điền đúng số hóa
              đơn trước khi gửi duyệt.
            </span>
          </p>
        )}

        {/* CR-260 — chỗ GHI NHẬN phần cấn trừ để cả người lập lẫn người duyệt cùng
            nhìn thấy: chưa duyệt là đề nghị, duyệt xong là số đã trừ thật. */}
        {showOffsetColumn && (
          <p className="flex items-start gap-2 rounded-md border border-info/30 bg-info/8 px-3 py-2 text-sm">
            <Info className="mt-0.5 size-4 shrink-0 text-info" />
            <span>
              {['approved', 'paid'].includes(req.status) ? (
                <>
                  Đã cấn trừ <b className="tabular-nums">{formatMoney(offsetTotal)}</b> tiền treo trả
                  trước vào công nợ lúc phiếu được duyệt.
                </>
              ) : offsetTotal > 0.01 ? (
                <>
                  Phiếu đề nghị cấn trừ <b className="tabular-nums">{formatMoney(offsetTotal)}</b>{' '}
                  tiền treo trả trước — bấm <b>Duyệt</b> mới cấn trừ thật vào công nợ (treo cấp NCC
                  còn lại: <b className="tabular-nums">{formatMoney(hangingAvailable)}</b>). Không đủ
                  treo hoặc nợ đã đổi thì hệ thống chặn duyệt, không tự đổi số.
                </>
              ) : (
                <>
                  Nhà cung cấp còn <b className="tabular-nums">{formatMoney(hangingAvailable)}</b>{' '}
                  tiền treo trả trước (không gắn đơn). Muốn dùng thì ghi số vào cột{' '}
                  <b>Cấn trừ trả trước</b> rồi Lưu — kế toán bấm Duyệt mới cấn trừ thật.
                </>
              )}
            </span>
          </p>
        )}

        <PaymentRequestLinesTable
          rows={lines}
          editable={editable}
          storageKey="finance.payment-request-view-lines"
          showSupplierColumns={false}
          lockLinkedPo={false}
          showOffsetColumn={showOffsetColumn}
          supplierDisplay={noop}
          sourceDisplay={noop}
          onPatch={patchLine}
          onRemove={removeLine}
        />

        <div className="flex flex-wrap items-center gap-3">
          {editable && (
            <Button variant="outline" size="sm" onClick={() => setLines((current) => [...current, blankLine()])}>
              <Plus />
              Thêm dòng
            </Button>
          )}
          <div className="min-w-4 flex-1" />
          <span className="text-base text-navy dark:text-foreground">
            {offsetTotal > 0.01 && (
              <>
                Cấn trừ trả trước: <b className="tabular-nums">{formatMoney(offsetTotal)}</b>
                <span className="mx-2 text-muted-foreground">·</span>
              </>
            )}
            Tổng đề nghị thanh toán: <b className="tabular-nums">{formatMoney(total)}</b>
          </span>
        </div>

        {/* CR-268 — sổ theo dõi tiền treo của phiếu trả trước đã chi: đã đối trừ
            bao nhiêu, NCC hoàn bao nhiêu, còn treo bao nhiêu. */}
        {showPrepayCard && (
          <Card className="gap-4 py-4">
            <CardHeader className="min-h-9 flex flex-row items-center justify-between gap-3 border-b px-4 pb-3!">
              <CardTitle className="text-base text-navy dark:text-foreground">
                Tiền treo trả trước
              </CardTitle>
              {canRefund && (
                <Button variant="outline" size="sm" onClick={() => setRefundOpen(true)}>
                  <Undo2 />
                  Ghi nhận NCC hoàn tiền
                </Button>
              )}
            </CardHeader>
            <CardContent className="space-y-3 px-4">
              <dl className="grid gap-3 sm:grid-cols-3">
                <div>
                  <dt className="text-xs text-muted-foreground">Đã đối trừ vào công nợ</dt>
                  <dd className="font-semibold text-success tabular-nums">
                    {formatMoney(allocatedTotal)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">NCC đã hoàn lại</dt>
                  <dd className="font-semibold text-info tabular-nums">
                    {formatMoney(refundedTotal)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Còn treo</dt>
                  <dd
                    className={cn(
                      'font-semibold tabular-nums',
                      hangingTotal > 0.01 ? 'text-warning' : 'text-muted-foreground',
                    )}
                  >
                    {formatMoney(hangingTotal)}
                  </dd>
                </div>
              </dl>
              <p className="flex items-start gap-2 text-xs text-muted-foreground">
                <Info className="mt-0.5 size-3.5 shrink-0" />
                <span>
                  Dòng gắn mã ĐMH tự đối trừ khi đơn đó nhận hàng sinh công nợ. Dòng không gắn đơn
                  thì kế toán cấn trừ tay ở màn Công nợ, hoặc bấm <b>Ghi nhận NCC hoàn tiền</b> khi
                  nhà cung cấp trả lại tiền cọc.
                </span>
              </p>
            </CardContent>
          </Card>
        )}

        <DocumentAttachmentsCard
          entity="payment_request"
          entityId={paymentRequestId}
          canManage={can('payment_request', 'write')}
          documentStatus={req.status}
        />

        {/* CR-149 (main, ticket #14): 3 câu chữ trên bản in, điền sẵn câu tự động. */}
        <Card className="gap-4 py-4">
          <CardHeader className="min-h-9 border-b px-4 pb-3!">
            <CardTitle className="text-base text-navy dark:text-foreground">Nội dung bản in</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 px-4">
            <p className="flex items-start gap-2 text-sm text-muted-foreground">
              <Info className="mt-0.5 size-4 shrink-0" />
              <span>
                Bản in in đúng nội dung trong 3 ô dưới (đã điền sẵn câu tự động, sửa thẳng được).
              </span>
            </p>
            <div className="grid gap-4 lg:grid-cols-3">
              {PRINT_TEXT_FIELDS.map((field) => (
                <div key={field.key} className="space-y-1.5">
                  <Label>{field.label}</Label>
                  {printTextsEditable ? (
                    <Textarea
                      rows={2}
                      maxLength={500}
                      value={printTexts[field.key] ?? ''}
                      onChange={(event) =>
                        setPrintTexts((current) => ({ ...current, [field.key]: event.target.value }))
                      }
                    />
                  ) : (
                    <ReadOnlyValue multiline>{printTexts[field.key]}</ReadOnlyValue>
                  )}
                  <p className="text-xs text-muted-foreground">{field.hint}</p>
                </div>
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-3">
              {printTextsEditable && req.status !== 'draft' && (
                <Button
                  size="sm"
                  onClick={() => void update.mutateAsync({ print_texts: printTexts })}
                  disabled={update.isPending}
                >
                  {update.isPending ? <Loader2 className="animate-spin" /> : <Save />}
                  Lưu nội dung in
                </Button>
              )}
              <p className="text-xs text-muted-foreground">
                {req.status === 'draft'
                  ? 'Bản nháp lưu chung bằng nút Lưu ở đầu trang.'
                  : printTextsEditable
                    ? 'Phiếu đã gửi duyệt / đã duyệt vẫn sửa được riêng 3 ô này — bấm Lưu nội dung in.'
                    : 'Phiếu Đã chi / Đã từ chối: khóa, không sửa được nữa.'}
              </p>
            </div>
          </CardContent>
        </Card>

        <AuditTimeline entity="payment_request" entityId={paymentRequestId} showMessage dense />
      </div>

      <ReasonConfirmDialog
        open={rejectOpen}
        onOpenChange={setRejectOpen}
        title="Từ chối phiếu yêu cầu thanh toán"
        description="Phiếu bị khóa, không sửa hay gửi lại được. Lý do được ghi vào nhật ký."
        placeholder="Lý do từ chối…"
        confirmText="Từ chối"
        destructive
        pending={runAction.isPending}
        onConfirm={async (reason) => {
          await runAction.mutateAsync({ action: 'reject', reason })
          setRejectOpen(false)
        }}
      />

      {/* CR-268 — NCC hoàn lại tiền treo (tiền VỀ công ty, khác cấn trừ là tiền ở
          lại thành tiền hàng). Để trống số tiền = hoàn toàn bộ phần còn treo. */}
      <Dialog open={refundOpen} onOpenChange={setRefundOpen}>
        <DialogContent className="sm:max-w-[480px]">
          <DialogHeader>
            <DialogTitle>Ghi nhận nhà cung cấp hoàn tiền</DialogTitle>
            <DialogDescription>
              Phiếu còn treo <b className="tabular-nums">{formatMoney(hangingTotal)}</b>. Ghi nhận
              phần NCC đã chuyển trả lại — không đụng tới công nợ.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="refund-amount">Số tiền hoàn</Label>
              <Input
                id="refund-amount"
                type="number"
                min={0}
                value={refundAmountText}
                placeholder={`Để trống = hoàn toàn bộ ${formatMoney(hangingTotal)}`}
                onChange={(event) => setRefundAmountText(event.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="refund-note">Ghi chú</Label>
              <Input
                id="refund-note"
                value={refundNote}
                placeholder="VD: NCC chuyển trả tiền cọc ngày…"
                onChange={(event) => setRefundNote(event.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRefundOpen(false)}>
              Đóng
            </Button>
            <Button
              disabled={refundPrepay.isPending}
              onClick={() => {
                const amount = Number(refundAmountText) || 0
                if (amount > hangingTotal + 0.01) {
                  toast.error(`Số hoàn vượt tiền treo còn lại (${formatMoney(hangingTotal)})`)
                  return
                }
                void refundPrepay
                  .mutateAsync({ amount, note: refundNote })
                  .then(() => {
                    setRefundOpen(false)
                    setRefundAmountText('')
                    setRefundNote('')
                  })
                  .catch(() => undefined) // httpClient đã tự toast lỗi non-GET.
              }}
            >
              {refundPrepay.isPending ? <Loader2 className="animate-spin" /> : <Undo2 />}
              Ghi nhận hoàn tiền
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={payOpen} onOpenChange={setPayOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Ghi nhận đã chi?</AlertDialogTitle>
            <AlertDialogDescription>
              Công nợ sẽ được trừ tương ứng với số tiền trên phiếu. Thao tác này không hoàn tác được.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Hủy</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                runAction.mutate({ action: 'pay' })
                setPayOpen(false)
              }}
            >
              Ghi nhận đã chi
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </PageContainer>
  )
}

/** Gợi ý ảnh hưởng của hình thức thanh toán lên bản in (CR-035). */
function paymentMethodHint(method: PaymentMethod): string {
  return method === 'cash'
    ? 'Bản in để trống cụm "Thông tin chuyển khoản".'
    : 'Bản in lấy số tài khoản / ngân hàng của nhà cung cấp.'
}

/** CR-149: 3 ô của khối "Nội dung bản in" — khóa khớp `PrintTexts` của backend. */
const PRINT_TEXT_FIELDS: { key: keyof PrintTexts; label: string; hint: string }[] = [
  { key: 'content', label: 'Nội dung thanh toán', hint: 'Dòng "Nội dung" trong khối NỘI DUNG THANH TOÁN.' },
  { key: 'line_desc', label: 'Diễn giải', hint: 'Cột "Diễn giải" của bảng Đề nghị thanh toán.' },
  {
    key: 'transfer',
    label: 'Nội dung chuyển khoản',
    hint: 'Dòng "Nội dung chuyển khoản" — phiếu Tiền mặt thì bản in vẫn để trống cụm này.',
  },
]
