import { useEffect, useState } from 'react'
import { ChevronDown, ChevronUp, GripVertical, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import {
  readDragPayload, setDragPayload, type HomeDragPayload,
} from '@/components/help-home-source-panel'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { HELP_ICONS } from '@/lib/help-icons'
import {
  addHomeItem, deleteHomeItem, reorderHome, updateHomeItem,
  type HelpHomeItem, type HelpHomeSection,
} from '@/lib/help-home-api'
import { gradientCss, HOME_GRADIENTS, HOME_ILLUSTRATIONS, illustrationUrl } from '@/lib/help-home-skins'
import { cn } from '@/lib/utils'

// Danh sách bài viết gắn vào 1 khung trang chủ — vừa là VÙNG THẢ (kéo bài từ cột nguồn sang),
// vừa kéo-thả đổi thứ tự trong khung. Nút lên/xuống vẫn giữ để dùng bằng bàn phím.
// Mọi thao tác ghi NGAY xuống server: đây là cấu hình hiển thị, không phải nội dung soạn dở.

/** Chữ trong ô trống của từng loại khung. */
const EMPTY_HINT: Record<string, string> = {
  article: 'Kéo bài viết từ cột bên trái thả vào đây.',
  faq: 'Kéo câu hỏi thường gặp từ cột bên trái thả vào đây.',
  custom: 'Chưa có thẻ nào — bấm "Thêm thẻ" bên dưới.',
}

export default function HelpHomeItemList({
  section, withSkin, onChanged,
}: {
  section: HelpHomeSection
  /** Cho chọn nền + ảnh minh họa (chỉ khung "Bắt đầu ngay"). */
  withSkin: boolean
  onChanged: () => Promise<void> | void
}) {
  const [busy, setBusy] = useState(false)
  /** Vị trí sẽ chèn khi thả; null = không có gì đang rê qua khung này. */
  const [dropAt, setDropAt] = useState<number | null>(null)

  const items = section.items

  const run = async (fn: () => Promise<boolean>) => {
    setBusy(true)
    const ok = await fn()
    setBusy(false)
    if (ok) await onChanged()
  }

  const move = (index: number, direction: -1 | 1) => run(() =>
    reorderHome(items, index, direction,
      (id, sortOrder) => updateHomeItem(id, { sort_order: sortOrder }, true)))

  /** Ghi lại sort_order cho cả danh sách sau khi kéo-thả. */
  const persistOrder = async (next: HelpHomeItem[]) => {
    const changed = next
      .map((item, i) => ({ item, i }))
      .filter(({ item, i }) => item.sort_order !== i)
    if (changed.length === 0) return false
    const results = await Promise.all(
      changed.map(({ item, i }) => updateHomeItem(item.id, { sort_order: i }, true)))
    if (results.some((ok) => !ok)) {
      toast.error('Không đổi được thứ tự, vui lòng thử lại')
      return false
    }
    return true
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const payload = readDragPayload(e)
    const at = dropAt ?? items.length
    setDropAt(null)
    if (!payload) return

    if (payload.kind === 'article' || payload.kind === 'faq') {
      if (payload.kind !== section.item_kind) {
        toast.error(section.item_kind === 'faq'
          ? 'Khung này chỉ nhận câu hỏi thường gặp'
          : 'Khung này chỉ nhận bài viết')
        return
      }
      const duplicate = payload.kind === 'article'
        ? items.some((i) => i.article_id === payload.id)
        : items.some((i) => i.faq_id === payload.id)
      if (duplicate) {
        toast.error('Đã có trong khung này rồi')
        return
      }
      run(() => addHomeItem(section.id, payload.kind === 'article'
        ? { article_id: payload.id, sort_order: at }
        : { faq_id: payload.id, sort_order: at }))
      return
    }

    // Kéo đổi thứ tự — chỉ trong CÙNG khung (backend không có API chuyển item sang khung khác)
    if (payload.sectionId !== section.id) {
      toast.error('Chỉ đổi được thứ tự trong cùng một khung')
      return
    }
    const from = items.findIndex((i) => i.id === payload.id)
    if (from < 0) return
    const rest = items.filter((i) => i.id !== payload.id)
    const target = at > from ? at - 1 : at
    const next = [...rest.slice(0, target), items[from], ...rest.slice(target)]
    run(() => persistOrder(next))
  }

  /** Rê qua nửa trên dòng thì chèn TRƯỚC dòng đó, nửa dưới thì chèn SAU. */
  const handleRowDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault()
    e.stopPropagation()
    const rect = e.currentTarget.getBoundingClientRect()
    setDropAt(e.clientY < rect.top + rect.height / 2 ? index : index + 1)
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); if (dropAt === null) setDropAt(items.length) }}
      onDragLeave={(e) => { if (!e.currentTarget.contains(e.relatedTarget as Node)) setDropAt(null) }}
      onDrop={handleDrop}
      className={cn(
        'space-y-2 rounded-md transition-colors',
        dropAt !== null && 'bg-primary/5 outline-2 outline-dashed outline-primary/50',
      )}
    >
      {items.length === 0 ? (
        <p className="rounded-md border border-dashed px-4 py-6 text-center text-sm text-muted-foreground">
          {EMPTY_HINT[section.item_kind]}
          <br />
          <span className="text-xs">Để trống thì trang chủ dùng nội dung mặc định.</span>
        </p>
      ) : (
        <ul className="overflow-hidden rounded-md border bg-card">
          {items.map((item, index) => (
            <li
              key={item.id}
              draggable
              onDragStart={(e) => setDragPayload(e, {
                kind: 'item', id: item.id, sectionId: section.id,
              } satisfies HomeDragPayload)}
              onDragOver={(e) => handleRowDragOver(e, index)}
              className={cn(
                'relative border-b p-3 last:border-b-0 hover:bg-secondary/60',
                dropAt === index && 'before:absolute before:inset-x-0 before:top-0 before:h-0.5 before:bg-primary',
                dropAt === index + 1 && 'after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:bg-primary',
              )}
            >
              <div className="flex items-center gap-2">
                <GripVertical className="size-4 shrink-0 cursor-grab text-muted-foreground/60 active:cursor-grabbing" />
                <span
                  title={itemLabel(item)}
                  className="min-w-0 flex-1 truncate text-sm font-medium text-navy"
                >
                  {itemLabel(item)}
                </span>
                <Button variant="ghost" size="icon" className="size-7" title="Lên"
                        disabled={busy || index === 0} onClick={() => move(index, -1)}>
                  <ChevronUp className="size-4" />
                </Button>
                <Button variant="ghost" size="icon" className="size-7" title="Xuống"
                        disabled={busy || index === items.length - 1} onClick={() => move(index, 1)}>
                  <ChevronDown className="size-4" />
                </Button>
                <Button
                  variant="ghost" size="icon" title="Bỏ khỏi khung"
                  className="size-7 text-destructive hover:bg-destructive/10 hover:text-destructive"
                  disabled={busy}
                  onClick={() => run(() => deleteHomeItem(item.id))}
                >
                  <Trash2 className="size-4" />
                </Button>
              </div>

              {withSkin && <SkinPickers item={item} index={index} busy={busy} run={run} />}
              {section.item_kind === 'custom' && (
                <CustomCardFields item={item} busy={busy} run={run} />
              )}
            </li>
          ))}
        </ul>
      )}

      {section.item_kind === 'custom' && (
        <Button
          variant="outline" size="sm" className="w-full" disabled={busy}
          onClick={() => run(() => addHomeItem(section.id, {
            title: 'Thẻ mới', description: '', icon: HELP_ICONS[0].slug, sort_order: items.length,
          }))}
        >
          <Plus /> Thêm thẻ
        </Button>
      )}
    </div>
  )
}

/** Tên hiển thị của một phần tử, chung cho cả 3 loại khung. */
function itemLabel(item: HelpHomeItem): string {
  return item.article_title || item.faq_question || item.title || `#${item.id}`
}

/** Thẻ tự do (khung "Mẹo tra cứu"): sửa icon + tiêu đề + mô tả ngay tại chỗ. */
function CustomCardFields({
  item, busy, run,
}: {
  item: HelpHomeItem
  busy: boolean
  run: (fn: () => Promise<boolean>) => Promise<void>
}) {
  const [title, setTitle] = useState(item.title ?? '')
  const [description, setDescription] = useState(item.description ?? '')
  useEffect(() => { setTitle(item.title ?? '') }, [item.title])
  useEffect(() => { setDescription(item.description ?? '') }, [item.description])

  /** Chỉ ghi khi rời ô và có thay đổi thật — gõ tới đâu gọi API tới đó thì spam request. */
  const commit = (field: 'title' | 'description', value: string) => {
    const next = value.trim()
    if (next === (item[field] ?? '')) return
    if (field === 'title' && !next) {
      toast.error('Tiêu đề thẻ không được để trống')
      setTitle(item.title ?? '')
      return
    }
    run(() => updateHomeItem(item.id, { [field]: next || null }, true))
  }

  return (
    <div className="mt-2 space-y-2 pl-6">
      <div className="flex items-center gap-2">
        <Select
          value={item.icon ?? ''}
          disabled={busy}
          onValueChange={(value) => run(() => updateHomeItem(item.id, { icon: value }, true))}
        >
          <SelectTrigger className="h-8 w-40 text-xs"><SelectValue placeholder="Chọn icon" /></SelectTrigger>
          <SelectContent>
            {HELP_ICONS.map((opt) => (
              <SelectItem key={opt.slug} value={opt.slug}>{opt.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Input
          value={title}
          disabled={busy}
          placeholder="Tiêu đề thẻ"
          onChange={(e) => setTitle(e.target.value)}
          onBlur={() => commit('title', title)}
          onKeyDown={(e) => { if (e.key === 'Enter') e.currentTarget.blur() }}
          className="h-8 flex-1 text-sm"
        />
      </div>
      <Input
        value={description}
        disabled={busy}
        placeholder="Mô tả ngắn hiện dưới tiêu đề"
        onChange={(e) => setDescription(e.target.value)}
        onBlur={() => commit('description', description)}
        onKeyDown={(e) => { if (e.key === 'Enter') e.currentTarget.blur() }}
        className="h-8 text-sm"
      />
    </div>
  )
}

/** Ô chọn nền gradient + ảnh minh họa của một tile. */
function SkinPickers({
  item, index, busy, run,
}: {
  item: HelpHomeItem
  index: number
  busy: boolean
  run: (fn: () => Promise<boolean>) => Promise<void>
}) {
  return (
    <div className="mt-2 flex flex-wrap items-center gap-2 pl-6">
      <span
        aria-hidden
        className="size-7 shrink-0 rounded-md border"
        style={{ background: gradientCss(item.gradient, index) }}
      />
      <Select
        value={item.gradient ?? ''}
        disabled={busy}
        onValueChange={(value) => run(() => updateHomeItem(item.id, { gradient: value }))}
      >
        <SelectTrigger className="h-8 w-32 text-xs"><SelectValue placeholder="Nền mặc định" /></SelectTrigger>
        <SelectContent>
          {HOME_GRADIENTS.map((g) => (
            <SelectItem key={g.slug} value={g.slug}>{g.label}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <img
        src={illustrationUrl(item.background_image, index)}
        alt="" aria-hidden
        className="size-7 shrink-0 rounded-md border object-contain"
      />
      <Select
        value={item.background_image ?? ''}
        disabled={busy}
        onValueChange={(value) => run(() => updateHomeItem(item.id, { background_image: value }))}
      >
        <SelectTrigger className="h-8 w-36 text-xs"><SelectValue placeholder="Ảnh mặc định" /></SelectTrigger>
        <SelectContent>
          {HOME_ILLUSTRATIONS.map((img) => (
            <SelectItem key={img.url} value={img.url}>{img.label}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
