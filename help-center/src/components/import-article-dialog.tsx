import { useRef, useState } from 'react'
import { CheckCircle2, FileUp, Loader2, TriangleAlert, Upload } from 'lucide-react'
import { toast } from 'sonner'

import { api } from '@/api/client'
import { Button } from '@/components/ui/button'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger,
} from '@/components/ui/dialog'
import { Switch } from '@/components/ui/switch'
import { flattenTree, type HelpNode } from '@/lib/help-tree'

// Hộp thoại "Nhập từ file" — mỗi file .html/.md thành 1 bài viết.
// Backend lo phần bóc tiêu đề + lọc HTML (xem help_center/import_service.py), ở đây chỉ chọn
// file, chọn mục đích và hiện kết quả TỪNG FILE để người dùng biết cái nào lỗi.

const ACCEPT = '.html,.htm,.md,.markdown'
const MAX_FILES = 30

type Result = { file: string; action: 'created' | 'updated' | 'error'; title?: string; message?: string }

export default function ImportArticleDialog({
  tree, defaultParentId = null, onImported,
}: {
  tree: HelpNode[]
  defaultParentId?: number | null
  onImported: () => void            // nạp lại cây sau khi nhập xong
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [open, setOpen] = useState(false)
  const [files, setFiles] = useState<File[]>([])
  const [parentId, setParentId] = useState<string>(defaultParentId ? String(defaultParentId) : '')
  const [overwrite, setOverwrite] = useState(false)
  const [busy, setBusy] = useState(false)
  const [results, setResults] = useState<Result[] | null>(null)

  const reset = () => { setFiles([]); setResults(null); setBusy(false) }

  const pick = (list: FileList | null) => {
    const arr = Array.from(list || [])
    if (arr.length > MAX_FILES) {
      toast.error(`Chọn tối đa ${MAX_FILES} file mỗi lần`)
      return
    }
    setFiles(arr)
    setResults(null)
  }

  const submit = async () => {
    if (!files.length) return
    setBusy(true)
    const form = new FormData()
    files.forEach((f) => form.append('files', f))
    if (parentId) form.append('parent_id', parentId)
    form.append('overwrite', String(overwrite))
    try {
      const res = await api.post('/api/v1/help-center/import', form)
      const rs: Result[] = res.data.data.results || []
      setResults(rs)
      const ok = rs.filter((r) => r.action !== 'error').length
      if (ok) {
        toast.success(`Đã nhập ${ok}/${rs.length} file`)
        onImported()
      } else {
        toast.error('Không nhập được file nào')
      }
    } catch {
      // interceptor đã toast lỗi
    } finally {
      setBusy(false)
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => { setOpen(v); if (!v) reset() }}
    >
      <DialogTrigger asChild>
        <Button variant="outline"><FileUp /> Nhập từ file</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Nhập bài viết từ file</DialogTitle>
          <DialogDescription>
            Mỗi file <b>.html</b> hoặc <b>.md</b> thành 1 bài viết. Tiêu đề lấy từ thẻ H1 (hoặc
            dòng <code># …</code> với Markdown), không có thì lấy tên file. Mã script trong file
            bị loại bỏ khi lưu.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <input
              ref={inputRef} type="file" accept={ACCEPT} multiple className="hidden"
              onChange={(e) => pick(e.target.files)}
            />
            <Button variant="outline" className="w-full" onClick={() => inputRef.current?.click()}>
              <Upload /> {files.length ? `Đã chọn ${files.length} file — chọn lại` : 'Chọn file…'}
            </Button>
            {files.length > 0 && (
              <ul className="mt-2 max-h-28 space-y-0.5 overflow-auto text-[0.8125rem] text-muted-foreground">
                {files.map((f) => <li key={f.name}>• {f.name}</li>)}
              </ul>
            )}
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium">Thêm vào mục</label>
            <select
              value={parentId} onChange={(e) => setParentId(e.target.value)}
              className="h-9 w-full rounded-md border bg-transparent px-3 text-sm"
            >
              <option value="">— Mục gốc —</option>
              {flattenTree(tree).map(({ node, depth }) => (
                <option key={node.id} value={node.id}>
                  {' '.repeat(depth * 4)}{node.title}
                </option>
              ))}
            </select>
          </div>

          <label className="flex items-start gap-3">
            <Switch checked={overwrite} onCheckedChange={setOverwrite} />
            <span className="text-sm">
              Cập nhật bài trùng tiêu đề
              <span className="block text-[0.8125rem] text-muted-foreground">
                Bật: bài đã có sẽ bị ghi đè nội dung (giữ nguyên vị trí trong cây).
                Tắt: luôn tạo bài mới, có thể trùng tên.
              </span>
            </span>
          </label>

          {results && (
            <div className="max-h-44 space-y-1 overflow-auto rounded-md border p-3 text-[0.8125rem]">
              {results.map((r) => (
                <div key={r.file} className="flex items-start gap-2">
                  {r.action === 'error'
                    ? <TriangleAlert className="mt-0.5 size-4 shrink-0 text-destructive" />
                    : <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-600" />}
                  <span>
                    <b>{r.file}</b> — {r.action === 'error'
                      ? r.message
                      : `${r.action === 'updated' ? 'đã cập nhật' : 'đã tạo'} "${r.title}"`}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>Đóng</Button>
          <Button onClick={submit} disabled={!files.length || busy}>
            {busy ? <Loader2 className="animate-spin" /> : <FileUp />}
            Nhập {files.length ? `${files.length} file` : ''}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
