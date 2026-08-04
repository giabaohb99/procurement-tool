import { useEffect, useMemo, useState } from 'react'
import ReactQuill from 'react-quill'

import { Button } from '@/components/ui/button'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { createFaq, updateFaq, type Faq } from '@/lib/faq-api'

// Hộp thoại thêm / sửa câu hỏi thường gặp.
// Câu trả lời soạn bằng Quill (bộ nút rút gọn) vì nội dung ngắn, ít định dạng.

export default function FaqEditorDialog({
  faq, nextSortOrder, open, onOpenChange, onSaved,
}: {
  /** null = thêm mới. */
  faq: Faq | null
  nextSortOrder: number
  open: boolean
  onOpenChange: (open: boolean) => void
  onSaved: () => Promise<void> | void
}) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setQuestion(faq?.question || '')
    setAnswer(faq?.answer || '')
  }, [faq, open])

  const modules = useMemo(() => ({
    toolbar: [
      ['bold', 'italic', 'underline'],
      [{ list: 'ordered' }, { list: 'bullet' }],
      ['link'],
      ['clean'],
    ],
  }), [])

  const handleSave = async () => {
    if (!question.trim()) return
    setSaving(true)
    const ok = faq
      ? await updateFaq(faq.id, { question, answer })
      : await createFaq({ question, answer, sort_order: nextSortOrder })
    setSaving(false)
    if (ok) {
      await onSaved()
      onOpenChange(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{faq ? 'Sửa câu hỏi' : 'Thêm câu hỏi'}</DialogTitle>
          <DialogDescription>
            Câu hỏi sẽ hiển thị ở trang "Câu hỏi thường gặp" bên phía người dùng.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-navy">Câu hỏi</label>
            <Input
              autoFocus
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="VD: Quên mật khẩu thì làm thế nào?"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-navy">Câu trả lời</label>
            <div className="hc-editor hc-editor-sm">
              <ReactQuill theme="snow" value={answer} onChange={setAnswer} modules={modules} />
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Hủy</Button>
          <Button disabled={saving || !question.trim()} onClick={handleSave}>
            {saving ? 'Đang lưu…' : 'Lưu'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
