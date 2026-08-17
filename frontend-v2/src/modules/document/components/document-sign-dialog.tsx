import { AlertTriangle } from 'lucide-react'
import { useState } from 'react'

import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { useSignDocument, useSignKinds } from '../hooks/use-document-signatures'
import { SIGN_KIND } from '../types/document-signature'

interface DocumentSignDialogProps {
  documentId: number
  versionId: number
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * GHI NHẬN CHỮ KÝ (J02, J03).
 *
 * Mỗi loại chữ ký hiện kèm **câu giá trị pháp lý của chính nó**, lấy từ backend.
 * Người ký phải đọc được sự khác nhau ngay tại lúc chọn — chứ không phải sau khi
 * đã gửi văn bản ra ngoài mới biết chữ ký nội bộ không có giá trị.
 */
export function DocumentSignDialog({
  documentId,
  versionId,
  open,
  onOpenChange,
}: DocumentSignDialogProps) {
  const { data: kinds = [] } = useSignKinds()
  const { data: employeePage } = useEmployees({ page_size: 1000, is_active: true })
  const sign = useSignDocument(documentId)

  const [signKind, setSignKind] = useState(String(SIGN_KIND.internal))
  const [signerId, setSignerId] = useState('')
  const [certSerial, setCertSerial] = useState('')
  const [certIssuer, setCertIssuer] = useState('')

  const isCertified = Number(signKind) === SIGN_KIND.certified
  //  Ký số mà thiếu chứng thư thì backend từ chối — không bày ra nút bấm sẽ hỏng.
  const canSign = signerId && (!isCertified || (certSerial.trim() && certIssuer.trim()))

  function handleSign() {
    sign.mutate(
      {
        version_id: versionId,
        signer_employee_id: Number(signerId),
        sign_kind: Number(signKind),
        cert_serial: certSerial.trim(),
        cert_issuer: certIssuer.trim(),
      },
      {
        onSuccess: () => {
          onOpenChange(false)
          setSignerId('')
          setCertSerial('')
          setCertIssuer('')
        },
      },
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Ký văn bản</DialogTitle>
          <DialogDescription>
            Chữ ký gắn với phiên bản đang mở và mã băm nội dung của nó. Ghi rồi thì
            không gỡ được — ký nhầm thì phải mở phiên bản mới.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Loại chữ ký</Label>
            <RadioGroup value={signKind} onValueChange={setSignKind} className="gap-2">
              {kinds.map((kind) => (
                <label
                  key={kind.value}
                  className={cn(
                    'flex cursor-pointer items-start gap-3 rounded-md border p-3 text-sm transition-colors',
                    Number(signKind) === kind.value
                      ? 'border-primary bg-accent/40'
                      : 'hover:bg-muted/50',
                  )}
                >
                  <RadioGroupItem value={String(kind.value)} className="mt-0.5" />
                  <span>
                    <span className="font-medium">{kind.label}</span>
                    {/*  Câu này là toàn bộ lý do J03 tồn tại. */}
                    <span className="block text-muted-foreground">{kind.legal_note}</span>
                  </span>
                </label>
              ))}
            </RadioGroup>
          </div>

          <div className="space-y-2">
            <Label>
              Người ký<span className="text-destructive"> *</span>
            </Label>
            <Select value={signerId} onValueChange={setSignerId}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Chọn người ký…" />
              </SelectTrigger>
              <SelectContent>
                {(employeePage?.items ?? []).map((employee) => (
                  <SelectItem key={employee.id} value={String(employee.id)}>
                    {employee.full_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {isCertified && (
            <>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="cert-serial">
                    Số hiệu chứng thư<span className="text-destructive"> *</span>
                  </Label>
                  <Input
                    id="cert-serial"
                    value={certSerial}
                    onChange={(event) => setCertSerial(event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cert-issuer">
                    Đơn vị cấp<span className="text-destructive"> *</span>
                  </Label>
                  <Input
                    id="cert-issuer"
                    placeholder="VD: VNPT-CA"
                    value={certIssuer}
                    onChange={(event) => setCertIssuer(event.target.value)}
                  />
                </div>
              </div>

              <p className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
                <span>
                  Hệ thống <b>chưa tự ký số</b> — phần đó cần thiết bị USB và một
                  dịch vụ riêng (J08, chưa làm). Chọn loại này nghĩa là bạn đã ký ở
                  nơi khác và đang <b>ghi nhận lại</b> vào hồ sơ.
                </span>
              </p>
            </>
          )}
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button type="button" disabled={!canSign || sign.isPending} onClick={handleSign}>
            Ghi nhận chữ ký
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
