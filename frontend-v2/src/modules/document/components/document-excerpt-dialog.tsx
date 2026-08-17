import { AlertTriangle } from 'lucide-react'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { CONFIDENTIAL_LEVELS } from '../types/security-level'

interface DocumentExcerptDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Mức mật bản gốc — bản trích không được đặt cao hơn. */
  sourceSecrecy: number
  sourceTitle: string
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
  isPending = false,
  onSubmit,
}: DocumentExcerptDialogProps) {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
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

          <div className="space-y-2">
            <Label htmlFor="excerpt-content">
              Phần nội dung được trích<span className="text-destructive"> *</span>
            </Label>
            <Textarea
              id="excerpt-content"
              rows={8}
              placeholder="Dán đúng phần nội dung cần chia. Chỉ phần dán vào đây mới nằm trong bản trích."
              value={content}
              onChange={(event) => setContent(event.target.value)}
            />
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
