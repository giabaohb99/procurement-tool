import { Info, Loader2, PenLine, Upload } from 'lucide-react'
import { useState, type ChangeEvent } from 'react'
import { toast } from 'sonner'

import { apiDelete, apiPost } from '@/core/api'
import { useAuth } from '@/core/auth/use-auth'
import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { FormCard } from '@/shared/ui/form-card'
import { Label } from '@/shared/ui/label'
import { validateImageFile } from '@/shared/utils/image-file'
import { prepareSignatureImage } from '@/shared/utils/prepare-signature-image'

/** Nền ô carô để nhìn rõ chữ ký PNG nền trong. */
const CHECKER_STYLE = {
  backgroundImage:
    'linear-gradient(45deg, #eef2f7 25%, transparent 25%), linear-gradient(-45deg, #eef2f7 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #eef2f7 75%), linear-gradient(-45deg, transparent 75%, #eef2f7 75%)',
  backgroundSize: '14px 14px',
  backgroundPosition: '0 0, 0 7px, 7px -7px, -7px 0',
}

/**
 * CHỮ KÝ CÁ NHÂN dạng ảnh — người dùng tự tải lên, thay, gỡ.
 *
 * Ảnh được thu nhỏ (và tách nền nếu bật) ngay ở trình duyệt trước khi gửi: ảnh
 * chụp từ điện thoại thường 4000px nặng vài MB, trong khi phiếu in chỉ dùng
 * khung ~400px.
 *
 * Gỡ chữ ký chỉ xóa liên kết, tệp trên lưu trữ giữ nguyên — phiếu đã in trước
 * đó không bị hỏng ảnh.
 */
export function SignatureCard({ signature }: { signature?: string }) {
  const { user, setUser } = useAuth()
  const [busy, setBusy] = useState(false)
  // Mặc định bật: đa số người dùng chụp/scan chữ ký trên giấy trắng. Tắt khi ảnh
  // đã là PNG nền trong sẵn (xử lý lại chỉ làm nét mực mỏng đi).
  const [autoRemoveBg, setAutoRemoveBg] = useState(true)

  const src = user?.signature ?? signature ?? ''

  function applySignature(url: string) {
    if (user) setUser({ ...user, signature: url })
  }

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return

    const problem = validateImageFile(file)
    if (problem) {
      toast.error(problem)
      return
    }

    setBusy(true)
    try {
      // Xử lý ảnh hỏng (canvas bị chặn, ảnh lỗi) thì vẫn gửi ảnh gốc — không
      // chặn người dùng chỉ vì bước làm đẹp không chạy được.
      let toSend = file
      try {
        toSend = await prepareSignatureImage(file, { removeBg: autoRemoveBg })
      } catch {
        toast.warning('Không xử lý được ảnh — giữ nguyên ảnh gốc')
      }
      const formData = new FormData()
      formData.append('file', toSend)
      const result = await apiPost<{ signature: string }>('/api/auth/signature', formData)
      applySignature(result.signature)
      toast.success('Đã cập nhật chữ ký')
    } catch {
      // HTTP client đã hiện thông báo lỗi cho thao tác POST.
    } finally {
      setBusy(false)
    }
  }

  async function remove() {
    setBusy(true)
    try {
      await apiDelete<{ signature: string }>('/api/auth/signature')
      applySignature('')
      toast.success('Đã gỡ chữ ký')
    } finally {
      setBusy(false)
    }
  }

  return (
    <FormCard title="Chữ ký cá nhân" icon={PenLine} iconClassName="text-muted-foreground">
      <div
        className="grid min-h-28 place-items-center rounded-lg border p-3"
        style={CHECKER_STYLE}
      >
        {src ? (
          <img src={src} alt="Chữ ký cá nhân" className="max-h-24 w-auto object-contain" />
        ) : (
          <span className="flex items-center gap-2 text-sm text-muted-foreground">
            <PenLine className="size-4" />
            Chưa có chữ ký
          </span>
        )}
      </div>

      <div className="mt-3 flex items-center gap-2">
        <Checkbox
          id="signature-remove-bg"
          checked={autoRemoveBg}
          disabled={busy}
          onCheckedChange={(checked) => setAutoRemoveBg(checked === true)}
        />
        <Label htmlFor="signature-remove-bg" className="text-[13px] text-muted-foreground">
          Tự động xóa nền trắng của ảnh
        </Label>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Button asChild disabled={busy}>
          <label className={busy ? 'pointer-events-none opacity-60' : 'cursor-pointer'}>
            {busy ? <Loader2 className="size-4 animate-spin" /> : <Upload className="size-4" />}
            {busy ? 'Đang xử lý…' : src ? 'Đổi chữ ký' : 'Tải chữ ký lên'}
            <input type="file" hidden accept="image/*" disabled={busy} onChange={upload} />
          </label>
        </Button>

        {src && (
          <DeleteConfirmButton
            recordName="ảnh chữ ký cá nhân"
            pending={busy}
            warning="Phiếu đã in trước đó vẫn giữ nguyên chữ ký cũ; các phiếu in sau sẽ để trống chỗ ký."
            onConfirm={remove}
          />
        )}
      </div>

      <p className="mt-3 flex gap-2 rounded-lg bg-accent px-3 py-2 text-xs text-muted-foreground">
        <Info className="mt-0.5 size-3.5 shrink-0" />
        <span>
          Chụp hoặc quét chữ ký viết bằng bút đậm trên giấy trắng — hệ thống tự tách nền
          thành ảnh trong suốt. Nếu ảnh đã là PNG nền trong sẵn thì bỏ chọn "Tự động xóa
          nền". Ảnh lớn được thu nhỏ về tối đa 800×400 điểm ảnh trước khi tải lên.
        </span>
      </p>
    </FormCard>
  )
}
