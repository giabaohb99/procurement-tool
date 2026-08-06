import { useEffect, useState } from 'react'
import { Code2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { embedSrcDoc, parseEmbedCode, type ParsedEmbed } from '@/lib/quill-html-embed'
import { releaseBodyLock } from '@/lib/release-body-lock'

// Hộp thoại dán mã nhúng (Guideflow, YouTube, Google Sheets, Canva...).
// Dán được CẢ đoạn <div>+<iframe>+<script> nhà cung cấp đưa, không chỉ mỗi URL như nút "video".
// Xem trước ngay trong hộp thoại để biết mã có chạy hay không trước khi chèn vào bài.

const PLACEHOLDER = `Dán mã nhúng hoặc URL nhúng, ví dụ:

<div class="gf-embed-wrapper">
  <iframe src="https://app.guideflow.com/embed/abc123"></iframe>
</div>`

export interface EmbedDraft {
  parsed: ParsedEmbed
  /** Chiều cao cố định (px); null = khung 16:9 co theo bề ngang cột nội dung. */
  height: number | null
}

export default function EmbedCodeDialog({
  open, onOpenChange, onInsert,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onInsert: (draft: EmbedDraft) => void
}) {
  const [code, setCode] = useState('')
  const [height, setHeight] = useState('')
  const [preview, setPreview] = useState(false)

  // Hộp thoại không unmount khi đóng -> tự dọn nội dung mỗi lần mở lại
  useEffect(() => {
    if (open) {
      setCode('')
      setHeight('')
      setPreview(false)
    }
  }, [open])

  const parsed = parseEmbedCode(code)
  const heightNum = parseInt(height, 10)
  const validHeight = Number.isFinite(heightNum) && heightNum > 0 ? heightNum : null

  const handleInsert = () => {
    if (!parsed) return
    onInsert({ parsed, height: validHeight })
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={(next) => { onOpenChange(next); if (!next) releaseBodyLock() }}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Code2 className="size-4 text-primary" /> Nhúng nội dung ngoài
          </DialogTitle>
          <DialogDescription>
            Dán mã nhúng nhà cung cấp đưa (kể cả đoạn có <code>&lt;script&gt;</code>) hoặc chỉ URL
            nhúng. Mã phức tạp sẽ được chạy trong khung cách ly để không ảnh hưởng trang.
          </DialogDescription>
        </DialogHeader>

        <Textarea
          autoFocus
          value={code}
          onChange={(e) => { setCode(e.target.value); setPreview(false) }}
          placeholder={PLACEHOLDER}
          className="h-40 font-mono text-xs"
        />

        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-navy">
            Chiều cao
            <Input
              type="number"
              min={100}
              value={height}
              onChange={(e) => setHeight(e.target.value)}
              placeholder="tự động"
              className="h-8 w-28"
            />
            px
          </label>
          <span className="text-xs text-muted-foreground">
            Bỏ trống thì khung giữ tỉ lệ 16:9 theo bề ngang bài viết.
          </span>
        </div>

        {code.trim() && !parsed && (
          <p className="text-sm text-destructive">
            Không nhận ra nội dung nhúng. Kiểm tra lại mã, hoặc dán URL nhúng bắt đầu bằng
            {' '}<code>https://</code>.
          </p>
        )}

        {parsed && (
          <div className="space-y-2">
            <button
              type="button"
              onClick={() => setPreview((p) => !p)}
              className="text-sm font-medium text-primary hover:underline"
            >
              {preview ? 'Ẩn xem trước' : 'Xem trước'}
            </button>
            {preview && (
              <iframe
                title="Xem trước nội dung nhúng"
                sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-presentation"
                srcDoc={embedSrcDoc(parsed.kind === 'iframe'
                  ? `<iframe src="${parsed.src}" allowfullscreen></iframe>`
                  : parsed.code)}
                style={validHeight ? { height: validHeight } : undefined}
                className="w-full rounded-md border bg-secondary aspect-video"
              />
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Hủy</Button>
          <Button disabled={!parsed} onClick={handleInsert}>Chèn vào bài</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
