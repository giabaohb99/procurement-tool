import { useState } from 'react'

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
import { PAGE_MARKERS } from '../helpers/page-marker'

export interface PageFrame {
  header_left: string
  header_right: string
  footer_left: string
  footer_right: string
}

interface DocumentPageFrameDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  value: PageFrame
  pending?: boolean
  onSubmit: (value: PageFrame) => void
}

const O_NHAP: { khoa: keyof PageFrame; nhan: string; goi_y: string }[] = [
  { khoa: 'header_left', nhan: 'Đầu trang — bên trái', goi_y: 'VD: CÔNG TY TNHH DEGO HOLDING' },
  { khoa: 'header_right', nhan: 'Đầu trang — bên phải', goi_y: 'VD: {{so_hieu}}' },
  { khoa: 'footer_left', nhan: 'Chân trang — bên trái', goi_y: 'VD: Lưu hành nội bộ' },
  { khoa: 'footer_right', nhan: 'Chân trang — bên phải', goi_y: 'VD: Trang {{trang}}/{{tong_trang}}' },
]

/**
 * Khai ĐẦU TRANG / CHÂN TRANG cho phiên bản đang soạn.
 *
 * Bốn ô chữ ngắn, không phải trình soạn thảo thu nhỏ: đây là dòng lặp lại ở MỌI
 * tờ giấy, cho định dạng tự do thì mỗi trang một kiểu và bản in vỡ bố cục.
 *
 * Nói thẳng trên hộp thoại rằng **số trang chỉ đúng ở bản in** — trong lúc soạn,
 * trình soạn thảo không biết tờ giấy này là tờ thứ mấy của bản in cuối cùng.
 */
export function DocumentPageFrameDialog({
  open,
  onOpenChange,
  value,
  pending = false,
  onSubmit,
}: DocumentPageFrameDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {/* `key` đổi theo lần mở: React dựng lại phần thân nên ô nhập tự mang giá
          trị đang có thật. Cách này thay cho việc đồng bộ bằng effect — đóng hộp
          mà không lưu thì lần sau không còn thấy thứ vừa gõ dở rồi bỏ. */}
      <DialogContent className="sm:max-w-2xl" key={open ? 'mo' : 'dong'}>
        <DialogHeader>
          <DialogTitle>Đầu trang · chân trang</DialogTitle>
          <DialogDescription>
            Bốn dòng này lặp lại ở mọi tờ giấy. Để trống thì tờ giấy không có dải đó.
          </DialogDescription>
        </DialogHeader>

        <ThanHopThoai value={value} pending={pending} onSubmit={onSubmit}
                      onCancel={() => onOpenChange(false)} />
      </DialogContent>
    </Dialog>
  )
}

interface ThanHopThoaiProps {
  value: PageFrame
  pending: boolean
  onSubmit: (value: PageFrame) => void
  onCancel: () => void
}

/** Phần nhập liệu — tách riêng để `key` ở trên dựng lại được cùng state. */
function ThanHopThoai({ value, pending, onSubmit, onCancel }: ThanHopThoaiProps) {
  const [form, setForm] = useState<PageFrame>(value)

  return (
    <>
        <div className="grid gap-4 sm:grid-cols-2">
          {O_NHAP.map((o) => (
            <div key={o.khoa} className="space-y-1.5">
              <Label htmlFor={o.khoa}>{o.nhan}</Label>
              <Input
                id={o.khoa}
                maxLength={200}
                placeholder={o.goi_y}
                value={form[o.khoa]}
                onChange={(event) =>
                  setForm((truoc) => ({ ...truoc, [o.khoa]: event.target.value }))
                }
              />
            </div>
          ))}
        </div>

        <div className="rounded-md border bg-muted/40 p-3 text-sm">
          <p className="mb-2 font-medium">Thẻ tự thay khi in</p>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-muted-foreground">
            {PAGE_MARKERS.map((m) => (
              <span key={m.the}>
                <code className="rounded bg-background px-1 py-0.5 text-foreground">{m.the}</code>{' '}
                {m.mo_ta}
              </span>
            ))}
          </div>
          <p className="mt-2 text-muted-foreground">
            Số trang chỉ hiện đúng ở <strong>bản in</strong> — trong lúc soạn, trang giấy chưa
            biết mình là tờ thứ mấy của bản in cuối cùng.
          </p>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onCancel}>
            Hủy
          </Button>
          <Button type="button" disabled={pending} onClick={() => onSubmit(form)}>
            Lưu
          </Button>
        </DialogFooter>
    </>
  )
}
