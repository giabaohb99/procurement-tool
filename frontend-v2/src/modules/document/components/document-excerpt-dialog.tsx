import { AlertTriangle, Code2, ListTree } from 'lucide-react'
import { useMemo, useState } from 'react'

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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Checkbox } from '@/shared/ui/checkbox'
import { Textarea } from '@/shared/ui/textarea'
import {
  joinSections,
  splitHtmlSections,
  suggestExcerptTitle,
} from '../helpers/split-html-sections'
import { CONFIDENTIAL_LEVELS } from '../types/security-level'

interface DocumentExcerptDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Mức mật bản gốc — bản trích không được đặt cao hơn. */
  sourceSecrecy: number
  sourceTitle: string
  /**
   * Thân văn bản gốc — để bày MỤC LỤC cho người dùng tick thay vì dán tay.
   * Bỏ trống (hoặc bài chưa chia mục) thì hộp thoại lùi về ô dán như cũ.
   */
  sourceHtml?: string
  isPending?: boolean
  onSubmit: (values: { title: string; content_html: string; secrecy_level: number }) => void
}

/**
 * TẠO BẢN TRÍCH NỘI BỘ (C19).
 *
 * Dùng để chia một phần nội dung xuống nhà máy / lab / dây chuyền. Bản trích là
 * một văn bản thường mang **đúng loại của bản gốc**, KHÔNG có số hiệu riêng
 * (gọi theo số của gốc) và không có người ký — khác hẳn Trích lục chính thức
 * (C20) là thứ gửi ra ngoài tập đoàn.
 *
 * Ba ràng buộc của E11 nói thẳng trên màn hình, không giấu trong tài liệu: mức
 * mật ≤ gốc, gốc lên bản mới thì bản trích bị đánh dấu cần rà lại, gốc bãi bỏ
 * thì bản trích hết hiệu lực theo.
 */
export function DocumentExcerptDialog({
  open,
  onOpenChange,
  sourceSecrecy,
  sourceTitle,
  sourceHtml = '',
  isPending = false,
  onSubmit,
}: DocumentExcerptDialogProps) {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [dangTick, setDangTick] = useState<string[]>([])
  //  Chọn theo mục lục thì bày XEM TRƯỚC; ai cần cắt tay từng đoạn mới bung mã ra.
  const [suaTay, setSuaTay] = useState(false)

  //  Cắt bài gốc thành mục MỘT LẦN mỗi lần nội dung đổi — bài dài vài trăm KB,
  //  cắt lại ở mỗi lần gõ tên bản trích là phí.
  const cacMuc = useMemo(() => splitHtmlSections(sourceHtml), [sourceHtml])

  /**
   * Tick một mục: đổ luôn HTML của các mục đang tick xuống ô nội dung.
   *
   * Vẫn ĐỔ XUỐNG Ô chứ không giấu đi: người dùng phải nhìn thấy đúng thứ sắp
   * chia ra ngoài, và sửa tiếp được nếu cần cắt bớt một đoạn.
   */
  function doiTick(id: string, bat: boolean) {
    const moi = bat ? [...dangTick, id] : dangTick.filter((x) => x !== id)
    setDangTick(moi)
    setContent(joinSections(cacMuc, moi))
    //  Chỉ gợi ý tên khi người dùng CHƯA tự đặt — đặt rồi mà bị đè là mất công gõ.
    if (!title.trim() || title.startsWith('Trích ')) {
      setTitle(suggestExcerptTitle(cacMuc, moi))
    }
  }
  const [secrecy, setSecrecy] = useState(String(Math.max(1, sourceSecrecy - 1)))

  //  Chỉ hiện mức ≤ gốc. Backend chặn lần nữa, nhưng bày ra một lựa chọn không
  //  bao giờ lưu được thì người dùng bấm rồi mới biết là sai.
  const chonDuoc = CONFIDENTIAL_LEVELS.filter((level) => level.id <= sourceSecrecy)

  function handleSubmit() {
    onSubmit({
      title: title.trim(),
      content_html: content.trim(),
      secrecy_level: Number(secrecy),
    })
    setTitle('')
    setContent('')
    setDangTick([])
    setSuaTay(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Tạo bản trích nội bộ</DialogTitle>
          <DialogDescription>
            Tách một phần nội dung của «{sourceTitle}» thành văn bản riêng để chia
            xuống nhà máy, lab hoặc dây chuyền.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="excerpt-title">
              Tên bản trích<span className="text-destructive"> *</span>
            </Label>
            <Input
              id="excerpt-title"
              placeholder="VD: Trích Điều 5 — phụ cấp ca đêm, gửi Nhà máy 2"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
          </div>

          {cacMuc.length > 0 && (
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <ListTree className="size-4" />
                Chọn mục cần trích
              </Label>
              {/*  Tick theo mục lục thay vì bôi đen rồi dán: chọn "Chương II" là
                   lấy trọn các Điều bên trong, khỏi sót đoạn nào. */}
              <div className="max-h-56 space-y-1 overflow-y-auto rounded-md border p-2">
                {cacMuc.map((muc) => (
                  <label
                    key={muc.id}
                    className="flex cursor-pointer items-start gap-2 rounded px-2 py-1 text-sm hover:bg-accent"
                    style={{ paddingLeft: `${(muc.level - 1) * 16 + 8}px` }}
                  >
                    <Checkbox
                      className="mt-0.5"
                      checked={dangTick.includes(muc.id)}
                      onCheckedChange={(bat) => doiTick(muc.id, bat === true)}
                    />
                    <span className={muc.level === 1 ? 'font-medium' : ''}>{muc.title}</span>
                  </label>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">
                Tick một chương là lấy trọn các điều bên trong. Sửa thêm ở ô bên dưới nếu cần.
              </p>
            </div>
          )}

          <div className="space-y-2">
            <div className="flex items-center justify-between gap-2">
              <Label htmlFor="excerpt-content">
                Phần nội dung được trích<span className="text-destructive"> *</span>
              </Label>
              {/*  Bày mã HTML ra cho người làm văn thư là bắt họ đọc thứ không
                   phải việc của họ. Mặc định xem trước; ai cần cắt tay từng đoạn
                   thì bấm để bung mã. */}
              {content && cacMuc.length > 0 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setSuaTay((truoc) => !truoc)}
                >
                  <Code2 className="size-4" />
                  {suaTay ? 'Xem trước' : 'Sửa mã'}
                </Button>
              )}
            </div>

            {content && cacMuc.length > 0 && !suaTay ? (
              <div
                className="doc-excerpt-preview max-h-64 overflow-y-auto rounded-md border px-4 py-3 text-sm"
                dangerouslySetInnerHTML={{ __html: content }}
              />
            ) : (
            <Textarea
              id="excerpt-content"
              rows={8}
              placeholder={
                cacMuc.length
                  ? 'Tick mục ở trên, hoặc dán tay phần cần chia vào đây.'
                  : 'Văn bản gốc chưa chia mục — dán đúng phần nội dung cần chia vào đây.'
              }
              value={content}
              onChange={(event) => setContent(event.target.value)}
            />
            )}
          </div>

          <div className="space-y-2">
            <Label>Mức mật của bản trích</Label>
            <Select value={secrecy} onValueChange={setSecrecy}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {chonDuoc.map((level) => (
                  <SelectItem key={level.id} value={String(level.id)}>
                    {level.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex gap-3 rounded-md border border-amber-300 bg-amber-50 px-4 py-3">
            <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
            <ul className="space-y-1 text-sm text-amber-900">
              <li>Bản trích không có số hiệu riêng — nó gọi theo số của bản gốc.</li>
              <li>Bản gốc lên phiên bản mới thì bản trích bị đánh dấu cần rà lại.</li>
              <li>Bản gốc bị bãi bỏ thì bản trích hết hiệu lực theo.</li>
            </ul>
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={!title.trim() || !content.trim() || isPending}
          >
            Tạo bản trích
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
