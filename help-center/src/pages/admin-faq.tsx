import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronDown, ChevronUp, Eye, MessageCircleQuestion, Pencil, Plus, Trash2 } from 'lucide-react'

import FaqEditorDialog from '@/components/faq-editor-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Switch } from '@/components/ui/switch'
import { deleteFaq, fetchFaqs, reorderFaq, updateFaq, type Faq } from '@/lib/faq-api'

// /admin/faq — quản lý câu hỏi thường gặp: thêm/sửa/xóa, bật-tắt hiển thị, đổi thứ tự.

export default function AdminFaq() {
  const [faqs, setFaqs] = useState<Faq[] | null>(null)
  const [editing, setEditing] = useState<Faq | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)

  const load = useCallback(async () => {
    try {
      setFaqs(await fetchFaqs())
    } catch {
      setFaqs([])
    }
  }, [])

  useEffect(() => { load() }, [load])

  const run = async (fn: () => Promise<boolean>) => {
    if (await fn()) await load()
  }

  const openEditor = (faq: Faq | null) => {
    setEditing(faq)
    setDialogOpen(true)
  }

  const list = faqs || []
  const activeCount = list.filter((f) => f.is_active).length

  return (
    <div className="mx-auto max-w-4xl px-8 py-7 pb-16">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-navy">Câu hỏi thường gặp</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {list.length > 0
              ? `${list.length} câu hỏi · ${activeCount} đang hiển thị ở trang người dùng.`
              : 'Quản lý các câu hỏi hiển thị ở trang người dùng.'}
          </p>
        </div>
        <div className="flex shrink-0 gap-2">
          <Button variant="outline" asChild>
            <Link to="/cau-hoi-thuong-gap"><Eye /> Xem trang người dùng</Link>
          </Button>
          <Button onClick={() => openEditor(null)}><Plus /> Thêm câu hỏi</Button>
        </div>
      </div>

      {!faqs ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }, (_, i) => <Skeleton key={i} className="h-14 w-full" />)}
        </div>
      ) : list.length === 0 ? (
        <div className="rounded-md border border-dashed px-6 py-12 text-center">
          <MessageCircleQuestion className="mx-auto mb-2 size-8 text-muted-foreground" strokeWidth={1.5} />
          <strong className="block text-navy">Chưa có câu hỏi nào</strong>
          <span className="text-sm text-muted-foreground">
            Bấm "Thêm câu hỏi" để tạo câu hỏi đầu tiên.
          </span>
        </div>
      ) : (
        <ul className="overflow-hidden rounded-md border">
          {list.map((faq, index) => (
            <li key={faq.id} className="flex items-center gap-3 border-b px-4 py-3 last:border-b-0 hover:bg-secondary/60">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="truncate text-sm font-semibold text-navy">{faq.question}</span>
                  {!faq.is_active && (
                    <Badge variant="outline" className="shrink-0 font-normal text-muted-foreground">
                      Đang ẩn
                    </Badge>
                  )}
                </div>
                {faq.answer && (
                  <p className="mt-0.5 truncate text-xs text-muted-foreground">
                    {faq.answer.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()}
                  </p>
                )}
              </div>

              <div className="flex shrink-0 items-center gap-1">
                <Switch
                  checked={faq.is_active}
                  title={faq.is_active ? 'Đang hiển thị — bấm để ẩn' : 'Đang ẩn — bấm để hiển thị'}
                  onCheckedChange={(checked) =>
                    run(() => updateFaq(faq.id, { is_active: checked }))}
                />
                <Button variant="ghost" size="icon" className="size-7" title="Lên"
                        disabled={index === 0}
                        onClick={() => run(() => reorderFaq(list, index, -1))}>
                  <ChevronUp className="size-4" />
                </Button>
                <Button variant="ghost" size="icon" className="size-7" title="Xuống"
                        disabled={index === list.length - 1}
                        onClick={() => run(() => reorderFaq(list, index, 1))}>
                  <ChevronDown className="size-4" />
                </Button>
                <Button variant="ghost" size="icon" className="size-7" title="Sửa"
                        onClick={() => openEditor(faq)}>
                  <Pencil className="size-4" />
                </Button>
                <Button variant="ghost" size="icon" title="Xóa"
                        className="size-7 text-destructive hover:bg-destructive/10 hover:text-destructive"
                        onClick={() => run(() => deleteFaq(faq))}>
                  <Trash2 className="size-4" />
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <FaqEditorDialog
        faq={editing}
        nextSortOrder={list.length}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSaved={load}
      />
    </div>
  )
}
