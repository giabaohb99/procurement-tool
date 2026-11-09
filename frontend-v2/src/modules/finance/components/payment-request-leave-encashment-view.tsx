import { ArrowLeft, Ban, Banknote, Check, Info, Loader2, Printer, Save, Send } from 'lucide-react'
import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { trackUiAction } from '@/core/telemetry/track-ui-action'
import { UI_ACTION_CODE } from '@/core/telemetry/ui-event-codes'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { DocumentAttachmentsCard } from '@/modules/procurement/components/document-attachments-card'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
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
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { ReasonConfirmDialog } from '@/shared/ui/reason-confirm-dialog'
import { useUpdatePaymentRequest, usePaymentRequestAction } from '../hooks/use-payment-requests'
import { PAYMENT_SOURCE_LABELS, type PaymentMethod, type PaymentRequest } from '../types/payment-request'
import { PaymentRequestLeaveEncashmentInfoCard } from './payment-request-leave-encashment-info-card'
import { PaymentRequestStatusBadge } from './payment-request-status-badge'

interface PaymentRequestLeaveEncashmentViewProps {
  req: PaymentRequest
}

/**
 * Khung RIÊNG cho YCTT THANH TOÁN NGHỈ PHÉP (duoc-CR-719). Trang chi tiết YCTT (~1450 dòng) xoay quanh NCC + công nợ;
 * rẽ sớm ở cấp component sang khung này thay vì chen nhánh giữa các hook của trang NCC.
 *
 * Khác YCTT thường (backend chặn lớp thứ hai, xem `leave_encashment_payout.py`):
 *  · không nút Xóa (hủy phiếu ở Nghỉ phép), không "Cập nhật theo công nợ", không hoàn tiền, không thêm dòng;
 *  · chỉ sửa được số tiền của DÒNG DUY NHẤT + hình thức + ghi chú, khi còn Nháp và có `payment_request.write`;
 *  · "Gửi duyệt" tắt khi số tiền = 0 (backend trả 400 "Nhập số tiền…").
 * Nút trạng thái giữ nguyên luật quyền của trang YCTT thường.
 */
export function PaymentRequestLeaveEncashmentView({ req }: PaymentRequestLeaveEncashmentViewProps) {
  const { can } = usePermission()
  const update = useUpdatePaymentRequest(req.id)
  const runAction = usePaymentRequestAction(req.id, { payToast: 'Đã ghi nhận chi tiền nghỉ phép' })
  const { data: companiesData } = useCompanies({ page_size: 500, is_active: true })

  const line = req.lines?.[0]
  //  ⚠️ Khởi tạo LẤY LUÔN dữ liệu đang có rồi đổ lại khi phiếu đổi (bẫy bao-CR-492 của trang YCTT thường).
  const [amount, setAmount] = useState(() => Number(line?.amount) || 0)
  const [note, setNote] = useState(() => req.note ?? '')
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>(() => req.payment_method ?? 'transfer')
  const [rejectOpen, setRejectOpen] = useState(false)
  const [payOpen, setPayOpen] = useState(false)
  /** Chặn bấm đúp Lưu / Gửi duyệt / Duyệt ngay trong tick — `isPending` chỉ đổi ở lượt vẽ sau. */
  const busyRef = useRef(false)

  const reqChanged = useHasChanged(req)
  if (reqChanged) {
    setAmount(Number(req.lines?.[0]?.amount) || 0)
    setNote(req.note ?? '')
    setPaymentMethod(req.payment_method ?? 'transfer')
  }

  const editable = req.status === 'draft' && can('payment_request', 'write') && req.lines?.length === 1
  const companyName = (companiesData?.items ?? []).find((c) => c.id === req.company_id)?.name ?? '—'
  const pending = update.isPending || runAction.isPending

  async function once(work: () => Promise<unknown>) {
    if (busyRef.current) return
    busyRef.current = true
    try {
      await work()
    } catch {
      //  http client đã bật toast lỗi cho POST/PATCH.
    } finally {
      busyRef.current = false
    }
  }

  const save = () =>
    update.mutateAsync({
      request_date: req.request_date,
      note,
      payment_method: paymentMethod,
      lines: [
        {
          payable_id: 0,
          po_code: line?.po_code ?? '',
          invoice_no: '',
          invoice_date: '',
          amount,
          offset_amount: 0,
        },
      ],
    })

  return (
    <PageContainer className="bg-slate-50/70 lg:p-4">
      <PageHeader
        sticky
        actionsClassName="max-md:[&>*]:flex-1"
        leading={
          <Button variant="outline" size="icon" asChild aria-label="Về danh sách yêu cầu thanh toán">
            <Link to={appRoutes.finance.paymentRequests}>
              <ArrowLeft />
            </Link>
          </Button>
        }
        title={
          <span className="flex flex-wrap items-center gap-2">
            <span className="max-md:hidden">Yêu cầu thanh toán </span>
            {req.code || ''}
            <PaymentRequestStatusBadge status={req.status} />
            <Badge variant="secondary" className="border-0 bg-info/10 text-info">
              {PAYMENT_SOURCE_LABELS[req.source_type]}
            </Badge>
          </span>
        }
        actions={
          <>
            {can('payment_request', 'print') && (
              <Button variant="outline" asChild title="In phiếu" aria-label="In phiếu" className="max-md:size-9 max-md:px-0">
                <Link
                  to={appRoutes.finance.paymentRequestPrint(req.id)}
                  onClick={() => trackUiAction(UI_ACTION_CODE.PRINT)}
                  target="_blank"
                  rel="noreferrer"
                >
                  <Printer />
                  <span className="max-md:hidden">In phiếu</span>
                </Link>
              </Button>
            )}
            {editable && (
              <Button type="button" onClick={() => void once(save)} disabled={pending}>
                {update.isPending ? <Loader2 className="animate-spin" /> : <Save />}
                Lưu
              </Button>
            )}
            {editable && (
              <Button
                type="button"
                variant="outline"
                disabled={pending || amount <= 0}
                title={amount <= 0 ? 'Nhập số tiền thanh toán trước khi gửi duyệt' : undefined}
                onClick={() =>
                  void once(async () => {
                    //  LƯU rồi mới gửi (bao-CR-590): gửi thẳng thì máy chủ gửi bản tiền 0 cũ.
                    await save()
                    await runAction.mutateAsync({ action: 'submit' })
                  })
                }
              >
                <Send />
                Gửi duyệt
              </Button>
            )}
            {req.status === 'submitted' && can('payment_request', 'approve') && (
              <>
                <Button
                  type="button"
                  disabled={pending}
                  onClick={() => void once(() => runAction.mutateAsync({ action: 'approve' }))}
                >
                  <Check />
                  Duyệt
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="text-destructive hover:text-destructive"
                  disabled={pending}
                  onClick={() => setRejectOpen(true)}
                >
                  <Ban />
                  Từ chối
                </Button>
              </>
            )}
            {req.status === 'approved' && can('payment_request', 'write') && (
              <Button type="button" onClick={() => setPayOpen(true)} disabled={pending}>
                <Banknote />
                Ghi nhận đã chi
              </Button>
            )}
          </>
        }
      />

      {req.status === 'cancelled' && req.reject_reason && (
        <p className="mb-4 flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/8 px-3 py-2 text-sm text-destructive">
          <Info className="mt-0.5 size-4 shrink-0" />
          <span>
            <b>Lý do từ chối:</b> {req.reject_reason}. Phiếu thanh toán nghỉ phép vẫn giữ Đã duyệt; Nhân sự hủy phiếu đó
            để trả lại ngày phép.
          </span>
        </p>
      )}

      <div className="min-w-0 space-y-4">
        <p className="flex items-start gap-2 rounded-md border border-info/30 bg-info/8 px-3 py-2 text-sm">
          <Info className="mt-0.5 size-4 shrink-0 text-info" />
          <span>
            Phiếu do hệ thống sinh khi phiếu thanh toán nghỉ phép được duyệt. Không gắn công nợ, không xóa ở đây. Còn
            Nháp thì nhờ Nhân sự hủy phiếu thanh toán nghỉ phép; đã gửi duyệt thì người duyệt bấm Từ chối.
          </span>
        </p>

        <PaymentRequestLeaveEncashmentInfoCard
          req={req}
          companyName={companyName}
          editable={editable}
          amount={amount}
          onAmountChange={setAmount}
          paymentMethod={paymentMethod}
          onPaymentMethodChange={setPaymentMethod}
          note={note}
          onNoteChange={setNote}
        />

        <DocumentAttachmentsCard
          entity="payment_request"
          entityId={req.id}
          canManage={can('payment_request', 'write')}
          documentStatus={req.status}
        />

        <AuditTimeline entity="payment_request" entityId={req.id} showMessage dense />
      </div>

      <ReasonConfirmDialog
        open={rejectOpen}
        onOpenChange={setRejectOpen}
        title="Từ chối yêu cầu thanh toán nghỉ phép"
        description="Phiếu bị khóa. Phiếu thanh toán nghỉ phép bên Nhân sự hiện cảnh báo kế toán từ chối chi để Nhân sự hủy và trả lại ngày phép."
        placeholder="Lý do từ chối…"
        confirmText="Từ chối"
        destructive
        pending={runAction.isPending}
        onConfirm={(reason) =>
          void once(async () => {
            await runAction.mutateAsync({ action: 'reject', reason })
            setRejectOpen(false)
          })
        }
      />

      <AlertDialog open={payOpen} onOpenChange={setPayOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Ghi nhận đã chi?</AlertDialogTitle>
            <AlertDialogDescription>
              Ghi nhận đã chi tiền nghỉ phép cho nhân sự. Phiếu này không gắn công nợ. Thao tác này không hoàn tác được.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Hủy</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                setPayOpen(false)
                void once(() => runAction.mutateAsync({ action: 'pay' }))
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
