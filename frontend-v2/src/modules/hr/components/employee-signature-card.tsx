import { Info, Loader2, PenLine, Upload } from 'lucide-react'
import { useState, type ChangeEvent } from 'react'
import { toast } from 'sonner'

import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { Label } from '@/shared/ui/label'
import { SectionHeading } from '@/shared/ui/section-heading'
import { validateImageFile } from '@/shared/utils/image-file'
import { prepareSignatureImage } from '@/shared/utils/prepare-signature-image'
import { useRemoveEmployeeSignature, useUploadEmployeeSignature } from '../hooks/use-employees'

/** Nền ô carô để nhìn rõ chữ ký PNG nền trong. */
const CHECKER_STYLE = {
  backgroundImage:
    'linear-gradient(45deg, #eef2f7 25%, transparent 25%), linear-gradient(-45deg, #eef2f7 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #eef2f7 75%), linear-gradient(-45deg, transparent 75%, #eef2f7 75%)',
  backgroundSize: '14px 14px',
  backgroundPosition: '0 0, 0 7px, 7px -7px, -7px 0',
}

interface EmployeeSignatureCardProps {
  employeeId: number
  signature: string
  /** Có quyền `employee.write`. */
  canEdit: boolean
  /** Nhân sự đã có tài khoản đăng nhập chưa (chữ ký lưu ở tài khoản). */
  hasAccount: boolean
  className?: string
}

/**
 * CHỮ KÝ của nhân sự — HR đặt/gỡ hộ. Ảnh lưu vào TÀI KHOẢN đăng nhập của nhân sự
 * (`tab_user.signature`), cùng chỗ với chữ ký người dùng tự đặt ở Trang cá nhân.
 * Chưa có tài khoản thì chưa có chỗ lưu → khóa và nhắc tạo tài khoản trước.
 */
export function EmployeeSignatureCard({
  employeeId,
  signature,
  canEdit,
  hasAccount,
  className,
}: EmployeeSignatureCardProps) {
  const [autoRemoveBg, setAutoRemoveBg] = useState(true)
  const upload = useUploadEmployeeSignature(employeeId)
  const remove = useRemoveEmployeeSignature(employeeId)
  const busy = upload.isPending || remove.isPending
  const editable = canEdit && hasAccount

  async function onPick(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return

    const problem = validateImageFile(file)
    if (problem) {
      toast.error(problem)
      return
    }

    // Ảnh hỏng bước làm đẹp thì vẫn gửi ảnh gốc — không chặn chỉ vì tách nền lỗi.
    let toSend = file
    try {
      toSend = await prepareSignatureImage(file, { removeBg: autoRemoveBg })
    } catch {
      toast.warning('Không xử lý được ảnh — giữ nguyên ảnh gốc')
    }
    upload.mutate(toSend)
  }

  return (
    <Card className={className}>
      <CardHeader>
        <SectionHeading>Chữ ký</SectionHeading>
      </CardHeader>
      <CardContent>
        <div
          className="grid min-h-28 place-items-center rounded-lg border p-3"
          style={CHECKER_STYLE}
        >
          {signature ? (
            <img src={signature} alt="Chữ ký nhân sự" className="max-h-24 w-auto object-contain" />
          ) : (
            <span className="flex items-center gap-2 text-sm text-muted-foreground">
              <PenLine className="size-4" />
              Chưa có chữ ký
            </span>
          )}
        </div>

        {editable ? (
          <>
            <div className="mt-3 flex items-center gap-2">
              <Checkbox
                id="employee-signature-remove-bg"
                checked={autoRemoveBg}
                disabled={busy}
                onCheckedChange={(checked) => setAutoRemoveBg(checked === true)}
              />
              <Label
                htmlFor="employee-signature-remove-bg"
                className="text-[13px] text-muted-foreground"
              >
                Tự động xóa nền trắng của ảnh
              </Label>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Button asChild disabled={busy}>
                <label className={busy ? 'pointer-events-none opacity-60' : 'cursor-pointer'}>
                  {busy ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Upload className="size-4" />
                  )}
                  {busy ? 'Đang xử lý…' : signature ? 'Đổi chữ ký' : 'Tải chữ ký lên'}
                  <input type="file" hidden accept="image/*" disabled={busy} onChange={onPick} />
                </label>
              </Button>

              {signature && (
                <DeleteConfirmButton
                  recordName="ảnh chữ ký của nhân sự"
                  pending={busy}
                  warning="Phiếu đã in trước đó vẫn giữ nguyên chữ ký cũ; các phiếu in sau sẽ để trống chỗ ký."
                  onConfirm={() => remove.mutateAsync()}
                />
              )}
            </div>
          </>
        ) : (
          <p className="mt-3 flex gap-2 rounded-lg bg-accent px-3 py-2 text-xs text-muted-foreground">
            <Info className="mt-0.5 size-3.5 shrink-0" />
            <span>
              {!hasAccount
                ? 'Nhân sự chưa có tài khoản đăng nhập — hãy tạo tài khoản trước khi đặt chữ ký.'
                : 'Bạn không có quyền chỉnh chữ ký của nhân sự này.'}
            </span>
          </p>
        )}
      </CardContent>
    </Card>
  )
}
