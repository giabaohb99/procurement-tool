import { useEffect, useState } from 'react'

import HelpIconPicker from '@/components/help-icon-picker'
import { Button } from '@/components/ui/button'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { releaseBodyLock } from '@/lib/release-body-lock'

// Hộp thoại "Thêm bài viết" — tiêu đề + mô tả ngắn + icon.
// Cùng kiểu singleton promise-based như confirm-dialog: gắn <NewArticleHost /> một lần ở main.tsx,
// nơi gọi chỉ cần `await askNewArticle({...})`.

export interface NewArticleDraft {
  title: string
  summary: string | null
  icon: string | null
}

type Req = {
  id: number
  title: string
  description: string
  placeholder: string
  resolve: (v: NewArticleDraft | null) => void
}

let current: Req | null = null
let seq = 1
const listeners = new Set<(x: Req | null) => void>()

/** Mở hộp thoại tạo bài viết → Promise<NewArticleDraft|null> (null = bấm Hủy). */
export function askNewArticle(opts: {
  title: string
  description: string
  placeholder?: string
}): Promise<NewArticleDraft | null> {
  return new Promise((resolve) => {
    current = {
      id: seq++,
      title: opts.title,
      description: opts.description,
      placeholder: opts.placeholder || 'VD: Hướng dẫn tạo Yêu cầu mua hàng',
      resolve,
    }
    listeners.forEach((l) => l(current))
  })
}

export function NewArticleHost() {
  const [req, setReq] = useState<Req | null>(null)
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [summary, setSummary] = useState('')
  const [icon, setIcon] = useState<string | null>(null)

  // Giữ req sau khi đóng (không unmount đột ngột) — xem chú thích ở confirm-dialog.tsx:
  // Radix khóa pointer-events trên <body> và chỉ gỡ khi đóng đúng quy trình.
  useEffect(() => {
    const onReq = (r: Req | null) => {
      if (!r) return
      setReq(r)
      setOpen(true)
    }
    listeners.add(onReq)
    return () => { listeners.delete(onReq) }
  }, [])

  // Reset form mỗi lần mở một yêu cầu mới
  useEffect(() => {
    if (!req) return
    setTitle('')
    setSummary('')
    setIcon(null)
  }, [req?.id])

  const close = (result: NewArticleDraft | null) => {
    if (!req) return
    const resolve = req.resolve
    current = null
    setOpen(false)
    releaseBodyLock()
    resolve(result)
  }

  const submit = () => {
    const name = title.trim()
    if (!name) return
    close({ title: name, summary: summary.trim() || null, icon })
  }

  if (!req) return null

  return (
    <Dialog open={open} onOpenChange={(next) => { if (!next) close(null) }}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{req.title}</DialogTitle>
          <DialogDescription>{req.description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <Field label="Tiêu đề" required>
            <Input
              autoFocus
              value={title}
              placeholder={req.placeholder}
              onChange={(e) => setTitle(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') submit() }}
            />
          </Field>

          <Field label="Mô tả ngắn" hint="Hiện dưới tiêu đề ở thẻ ngoài trang chủ. Có thể bỏ trống.">
            <Input
              value={summary}
              maxLength={255}
              placeholder="VD: Cách lập và gửi duyệt phiếu yêu cầu mua hàng."
              onChange={(e) => setSummary(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') submit() }}
            />
          </Field>

          <Field label="Icon">
            <HelpIconPicker value={icon} onChange={setIcon} />
          </Field>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => close(null)}>Hủy</Button>
          <Button disabled={!title.trim()} onClick={submit}>Tạo bài viết</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function Field({
  label, hint, required, children,
}: {
  label: string
  hint?: string
  required?: boolean
  children: React.ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <label className="block text-sm font-medium text-navy">
        {label} {required && <span className="text-destructive">*</span>}
      </label>
      {children}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  )
}
