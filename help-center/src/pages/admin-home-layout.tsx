import { useCallback, useEffect, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { ChevronDown, ChevronUp, Eye, EyeOff, LayoutTemplate } from 'lucide-react'
import { toast } from 'sonner'

import HelpHomeItemList from '@/components/help-home-item-list'
import HelpHomePreview from '@/components/help-home-preview'
import HelpHomeSourcePanel from '@/components/help-home-source-panel'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Switch } from '@/components/ui/switch'
import type { AdminOutletContext } from '@/layouts/admin-layout'
import { fetchFaqs, type Faq } from '@/lib/faq-api'
import {
  fetchHomeSections, HOME_SECTION, reorderHome, updateHomeSection,
  type HelpHomeSection,
} from '@/lib/help-home-api'
import { cn } from '@/lib/utils'

// /admin/trang-chu — sắp xếp và sửa 4 khung của trang chủ khu người dùng.
// 4 khung là CỐ ĐỊNH (backend seed sẵn), chỉ đổi tiêu đề / ẩn-hiện / thứ tự; hai khung
// "Bắt đầu ngay" và "Các Phân hệ" chọn thêm được bài viết hiển thị bên trong.
// Mọi thay đổi ghi NGAY xuống server — đây là cấu hình hiển thị, không phải nội dung soạn dở
// nên không cần nút Lưu.

/** Giải thích từng khung cho người soạn khỏi phải đoán khung nào ra chỗ nào. */
const SECTION_HINTS: Record<string, string> = {
  [HOME_SECTION.QUICK]: 'Tile lớn nền gradient ngay dưới ô tìm kiếm — mỗi hàng 3 tile, thừa thì tự xuống hàng.',
  [HOME_SECTION.CATEGORIES]: 'Lưới thẻ các nhóm nghiệp vụ, mỗi thẻ là một mục gốc.',
  [HOME_SECTION.FAQ]: 'Các câu hỏi thường gặp nổi bật. Bỏ trống thì chỉ hiện thẻ dẫn sang trang Câu hỏi thường gặp.',
  [HOME_SECTION.TIPS]: 'Các thẻ mẹo tra cứu, nội dung tự nhập. Bỏ trống thì dùng 3 mẹo mặc định.',
}

export default function AdminHomeLayout() {
  const { tree } = useOutletContext<AdminOutletContext>()
  const [sections, setSections] = useState<HelpHomeSection[] | null>(null)
  const [faqs, setFaqs] = useState<Faq[]>([])
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    try {
      setSections(await fetchHomeSections())
    } catch {
      setSections([]) // interceptor đã toast lỗi
    }
  }, [])

  useEffect(() => { load() }, [load])
  // Câu hỏi chỉ để kéo vào khung, không đổi trong lúc soạn -> nạp một lần
  useEffect(() => { fetchFaqs().then(setFaqs).catch(() => setFaqs([])) }, [])

  const run = async (fn: () => Promise<boolean>) => {
    setBusy(true)
    const ok = await fn()
    setBusy(false)
    if (ok) await load()
  }

  const move = (index: number, direction: -1 | 1) => run(() =>
    reorderHome(sections!, index, direction,
      (id, sortOrder) => updateHomeSection(id, { sort_order: sortOrder }, true)))

  return (
    <div className="w-full px-8 py-7 pb-16">
      <div className="mb-1 flex items-center gap-2">
        <LayoutTemplate className="size-5 text-primary" strokeWidth={1.75} />
        <h1 className="text-lg font-bold text-navy">Bố cục trang chủ</h1>
      </div>
      <p className="mb-5 text-sm text-muted-foreground">
        Sắp xếp thứ tự, đổi tiêu đề và ẩn/hiện 4 khung trên trang chủ khu người dùng.
        Thay đổi có hiệu lực ngay, không cần bấm lưu.
      </p>

      {!sections ? (
        <div className="max-w-3xl space-y-3">
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-28 w-full" />
        </div>
      ) : sections.length === 0 ? (
        <p className="rounded-md border border-dashed px-6 py-12 text-center text-sm text-muted-foreground">
          Chưa có cấu hình khung trang chủ. Chạy lại seed backend để tạo 4 khung mặc định.
        </p>
      ) : (
        // 3 cột: nguồn bài viết (kéo) · các khung (thả) · xem trước. Màn hẹp thì xếp chồng.
        <div className="flex flex-col gap-5 xl:flex-row xl:items-start">
          <aside className="h-96 w-full shrink-0 xl:sticky xl:top-4 xl:h-[calc(100vh-9rem)] xl:w-64">
            <HelpHomeSourcePanel tree={tree} faqs={faqs} />
          </aside>

          <div className="min-w-0 flex-1 space-y-4">
            {sections.map((section, index) => (
              <SectionCard
                key={section.id}
                section={section}
                busy={busy}
                isFirst={index === 0}
                isLast={index === sections.length - 1}
                onMove={(direction) => move(index, direction)}
                onChanged={load}
                onSave={(data) => run(() => updateHomeSection(section.id, data))}
              />
            ))}
          </div>

          <aside className="w-full shrink-0 xl:sticky xl:top-4 xl:w-80">
            <h2 className="mb-2 text-sm font-semibold text-navy">Xem trước trang chủ</h2>
            <HelpHomePreview sections={sections} tree={tree} />
          </aside>
        </div>
      )}
    </div>
  )
}

function SectionCard({
  section, busy, isFirst, isLast, onMove, onChanged, onSave,
}: {
  section: HelpHomeSection
  busy: boolean
  isFirst: boolean
  isLast: boolean
  onMove: (direction: -1 | 1) => void
  onChanged: () => Promise<void> | void
  onSave: (data: { title?: string; is_visible?: boolean }) => void
}) {
  const [title, setTitle] = useState(section.title)
  useEffect(() => { setTitle(section.title) }, [section.title])


  const commitTitle = () => {
    const next = title.trim()
    if (!next) {
      toast.error('Tiêu đề khung không được để trống')
      setTitle(section.title)
      return
    }
    if (next !== section.title) onSave({ title: next })
  }

  return (
    <section className={cn('overflow-hidden rounded-md border bg-card', !section.is_visible && 'opacity-60')}>
      <header className="flex flex-wrap items-center gap-2 border-b bg-secondary px-4 py-2.5">
        <div className="flex shrink-0 items-center gap-0.5">
          <Button variant="ghost" size="icon" className="size-7" title="Lên"
                  disabled={busy || isFirst} onClick={() => onMove(-1)}>
            <ChevronUp className="size-4" />
          </Button>
          <Button variant="ghost" size="icon" className="size-7" title="Xuống"
                  disabled={busy || isLast} onClick={() => onMove(1)}>
            <ChevronDown className="size-4" />
          </Button>
        </div>

        <Input
          value={title}
          disabled={busy}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={commitTitle}
          onKeyDown={(e) => { if (e.key === 'Enter') e.currentTarget.blur() }}
          className="h-8 min-w-[12rem] flex-1 bg-background text-sm font-semibold text-navy"
        />

        <label className="flex shrink-0 items-center gap-2 text-xs text-muted-foreground">
          {section.is_visible ? <Eye className="size-4" /> : <EyeOff className="size-4" />}
          <Switch
            checked={section.is_visible}
            disabled={busy}
            onCheckedChange={(checked) => onSave({ is_visible: checked })}
          />
        </label>
      </header>

      <div className="space-y-3 p-4">
        <p className="text-xs text-muted-foreground">{SECTION_HINTS[section.key]}</p>
        <HelpHomeItemList
          section={section}
          withSkin={section.key === HOME_SECTION.QUICK}
          onChanged={onChanged}
        />
      </div>
    </section>
  )
}
