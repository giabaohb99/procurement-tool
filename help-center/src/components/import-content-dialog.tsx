import { useRef, useState } from 'react'
import { FileDown, Loader2, Upload } from 'lucide-react'
import { toast } from 'sonner'

import { api } from '@/api/client'
import { Button } from '@/components/ui/button'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger,
} from '@/components/ui/dialog'
import { Switch } from '@/components/ui/switch'

// Hộp thoại "Nhập từ file" TRONG trang soạn bài — đổ nội dung file vào trình soạn thảo
// của bài ĐANG MỞ, khác với hộp thoại ở /admin (tạo bài mới cho từng file).
// Chỉ ghi vào state, KHÔNG tự lưu: người dùng còn xem lại rồi mới bấm Lưu.

const ACCEPT = '.html,.htm,.md,.markdown'

type Parsed = { title: string; summary: string | null; content: string }

export default function ImportContentDialog({
  onApply,
}: {
  /** replace = thay toàn bộ nội dung hiện có; false = chèn vào cuối. title chỉ có khi người dùng chọn lấy. */
  onApply: (v: { content: string; replace: boolean; title?: string }) => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [fileName, setFileName] = useState('')
  const [parsed, setParsed] = useState<Parsed | null>(null)
  const [replace, setReplace] = useState(true)
  const [takeTitle, setTakeTitle] = useState(false)

  const reset = () => { setFileName(''); setParsed(null); setBusy(false); setTakeTitle(false) }

  const pick = async (list: FileList | null) => {
    const f = list?.[0]
    if (!f) return
    setFileName(f.name)
    setParsed(null)
    setBusy(true)
    const form = new FormData()
    form.append('file', f)
    try {
      const res = await api.post('/api/v1/help-center/import/parse', form)
      setParsed(res.data.data as Parsed)
    } catch {
      setFileName('')     // interceptor đã toast lỗi
    } finally {
      setBusy(false)
    }
  }

  const apply = () => {
    if (!parsed) return
    onApply({
      content: parsed.content,
      replace,
      title: takeTitle ? parsed.title : undefined,
    })
    toast.success('Đã đưa nội dung vào bài — bấm Lưu để ghi nhận')
    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { setOpen(v); if (!v) reset() }}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" title="Đổ nội dung từ file HTML/Markdown vào bài này">
          <FileDown /> Nhập từ file
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Nhập nội dung từ file</DialogTitle>
          <DialogDescription>
            Chọn 1 file <b>.html</b> hoặc <b>.md</b> để đổ vào bài đang mở. Nội dung chỉ nằm trong
            trình soạn thảo, <b>chưa lưu</b> — xem lại rồi bấm Lưu. Mã script trong file bị loại bỏ.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <input
            ref={inputRef} type="file" accept={ACCEPT} className="hidden"
            onChange={(e) => pick(e.target.files)}
          />
          <Button variant="outline" className="w-full" disabled={busy}
            onClick={() => inputRef.current?.click()}>
            {busy ? <Loader2 className="animate-spin" /> : <Upload />}
            {fileName || 'Chọn file…'}
          </Button>

          {parsed && (
            <div className="rounded-md border p-3 text-[0.8125rem]">
              <div><span className="text-muted-foreground">Tiêu đề trong file:</span> <b>{parsed.title}</b></div>
              <div className="mt-1 line-clamp-2 text-muted-foreground">{parsed.summary || '(không có nội dung chữ)'}</div>
            </div>
          )}

          <label className="flex items-start gap-3">
            <Switch checked={replace} onCheckedChange={setReplace} />
            <span className="text-sm">
              Thay toàn bộ nội dung hiện tại
              <span className="block text-[0.8125rem] text-muted-foreground">
                Tắt: nội dung file được <b>chèn vào cuối</b> bài, giữ nguyên phần đang có.
              </span>
            </span>
          </label>

          {parsed && (
            <label className="flex items-start gap-3">
              <Switch checked={takeTitle} onCheckedChange={setTakeTitle} />
              <span className="text-sm">
                Lấy luôn tiêu đề từ file
                <span className="block text-[0.8125rem] text-muted-foreground">
                  Đổi tiêu đề bài thành “{parsed.title}”.
                </span>
              </span>
            </label>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>Hủy</Button>
          <Button onClick={apply} disabled={!parsed || busy}>
            <FileDown /> Đưa vào bài viết
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
