import { Check, Eye, Pencil, Plus, Trash2, X } from 'lucide-react'
import { useRef, useState } from 'react'

import {
  botMemoryApi,
  type MemoryLine,
  type MemorySection,
} from '@/modules/system/api/bot-memory-api'
import { useBotMemory, useBotMemoryAction } from '@/modules/system/hooks/use-bot-memory'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { Input } from '@/shared/ui/input'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDate } from '@/shared/utils/format-date'

/**
 * Tab «Bot nhớ gì về tôi» ở Trang cá nhân (ai-CR-138, phase 13.4).
 *
 * Bot tự nhớ thì người dùng phải THẤY được và XÓA được: sổ lõi bốn mục (dòng bot tự rút có nhãn «tự rút» + hạn), các
 * điều bot đang để ý (chưa ghi), thói quen đếm từ sổ ý định, kho ghi chú. Chỉ chủ sổ thấy — cửa API lấy người dùng từ
 * phiên, quản trị cũng không có đường xem sổ người khác. Sửa / xóa gửi kèm NGUYÊN VĂN dòng cũ: dòng đã đổi ở tab khác thì
 * backend trả 409 thay vì sửa nhầm dòng bên cạnh.
 */
export function ProfileMemoryTab() {
  const { data, isLoading } = useBotMemory()
  const busy = useRef(false)
  const addLine = useBotMemoryAction(botMemoryApi.addLine, 'Đã ghi vào sổ.')
  const editLine = useBotMemoryAction(botMemoryApi.editLine, 'Đã sửa.')
  const deleteLine = useBotMemoryAction(botMemoryApi.deleteLine, 'Đã xóa dòng.')
  const dropWatching = useBotMemoryAction(botMemoryApi.dropWatching, 'Em sẽ không để ý điều này nữa.')
  const deleteNote = useBotMemoryAction(botMemoryApi.deleteNote, 'Đã xóa ghi chú.')
  const wipe = useBotMemoryAction(() => botMemoryApi.wipe(), 'Đã xóa toàn bộ trí nhớ.')

  /** `disabled={isPending}` không chặn bấm đúp (state chỉ đổi ở lượt render sau) — chặn bằng ref đổi ngay trong tick. */
  async function once(run: () => Promise<unknown>): Promise<boolean> {
    if (busy.current) return false
    busy.current = true
    try {
      await run()
      return true
    } catch {
      //  Lỗi đã hiện toast ở tầng API; ô nhập giữ nguyên chữ để sửa lại.
      return false
    } finally {
      busy.current = false
    }
  }

  if (isLoading || !data) {
    return <Skeleton className="h-64" />
  }

  const empty = data.sections.every((s) => s.lines.length === 0)

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-2">
          <SectionHeading>Sổ nhớ của bot về tôi</SectionHeading>
          <span className="text-xs text-muted-foreground">
            {data.chars}/{data.max} ký tự
          </span>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <p className="flex items-start gap-1.5 text-muted-foreground">
            <Eye className="mt-0.5 size-4 shrink-0" />
            Chỉ mình bạn xem được trang này, kể cả quản trị cũng không có đường xem. Dòng gắn nhãn «tự rút» là bot tự ghi
            sau khi bạn nhắc lại nhiều lần; không nhắc lại thì dòng tự hết hạn.
            {!data.auto_enabled && ' Tự rút ghi nhớ đang tắt trên hệ thống.'}
          </p>
          {empty && <p className="text-muted-foreground">Bot chưa nhớ gì về bạn.</p>}
          {data.sections.map((section) => (
            <MemorySectionBlock
              key={section.key}
              section={section}
              onAdd={(text) => once(() => addLine.mutateAsync({ section: section.key, text }))}
              onEdit={(line, text) => once(() => editLine.mutateAsync({ section: section.key, old: line.text, text }))}
              onDelete={async (line) => {
                const ok = await confirm({
                  title: 'Xóa dòng nhớ',
                  message: `Xóa «${line.fact}»? Bot sẽ không tự rút lại điều này trong một thời gian.`,
                  confirmLabel: 'Xóa',
                })
                if (ok) await once(() => deleteLine.mutateAsync({ section: section.key, old: line.text }))
              }}
            />
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <SectionHeading>Bot đang để ý</SectionHeading>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {data.watching.length === 0 ? (
            <p className="text-muted-foreground">Chưa có điều nào đang chờ đủ lần nhắc.</p>
          ) : (
            <>
              <p className="text-muted-foreground">
                Điều bot thấy bạn nhắc nhưng CHƯA ghi vào sổ — cần nhắc lại đủ số lần trên đủ số ngày khác nhau.
              </p>
              <ul className="divide-y rounded-md border">
                {data.watching.map((w) => (
                  <li key={w.id} className="flex items-center justify-between gap-2 px-3 py-2">
                    <div>
                      <div>{w.fact}</div>
                      <div className="text-xs text-muted-foreground">
                        {w.hits}/{w.need_hits} lần · {w.days}/{w.need_days} ngày
                      </div>
                    </div>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      aria-label={`Bỏ để ý: ${w.fact}`}
                      onClick={() => once(() => dropWatching.mutateAsync(w.id))}
                    >
                      <X className="size-4" />
                    </Button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </CardContent>
      </Card>

      {(data.habits.length > 0 || data.suggestions.length > 0) && (
        <Card>
          <CardHeader>
            <SectionHeading>Thói quen bot thấy</SectionHeading>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {data.habits.map((h) => (
              <div key={h.type}>
                {h.label.charAt(0).toUpperCase() + h.label.slice(1)} hay hỏi: <strong>{h.value}</strong>{' '}
                <span className="text-muted-foreground">
                  ({h.count}/{h.total} lần)
                </span>
              </div>
            ))}
            {data.habits.length > 0 && (
              <p className="text-muted-foreground">
                Hỏi tắt mà thiếu đối tượng thì bot dùng giá trị trên và nói rõ «em hiểu là … như mọi lần».
              </p>
            )}
            {data.suggestions.map((s) => (
              <div key={`${s.sub}-${s.weekday}`} className="rounded-md border border-dashed px-3 py-2">
                {s.text}
              </div>
            ))}
            {data.suggestions.length > 0 && (
              <p className="text-muted-foreground">Chỉ là đề xuất — bot không tự gửi gì khi bạn chưa bật.</p>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <SectionHeading>Kho ghi chú</SectionHeading>
        </CardHeader>
        <CardContent className="text-sm">
          {data.notes.length === 0 ? (
            <p className="text-muted-foreground">Chưa có ghi chú. Bot tự tóm tắt mỗi buổi chat riêng vào đây.</p>
          ) : (
            <ul className="divide-y rounded-md border">
              {data.notes.map((n) => (
                <li key={n.id} className="flex items-center justify-between gap-2 px-3 py-2">
                  <div>
                    <div>{n.title || `Ghi chú #${n.id}`}</div>
                    <div className="text-xs text-muted-foreground">
                      {n.chars} ký tự · {formatDate(n.created_at)}
                    </div>
                  </div>
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    aria-label={`Xóa ghi chú ${n.title}`}
                    onClick={async () => {
                      const ok = await confirm({ title: 'Xóa ghi chú', message: `Xóa ghi chú «${n.title}»?`, confirmLabel: 'Xóa' })
                      if (ok) await once(() => deleteNote.mutateAsync(n.id))
                    }}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button
          type="button"
          variant="destructive"
          size="sm"
          onClick={async () => {
            const ok = await confirm({
              title: 'Xóa toàn bộ trí nhớ',
              message:
                'Xóa hết sổ nhớ, kho ghi chú, các điều bot đang để ý và thói quen đã đếm về bạn? Không lấy lại được.',
              confirmLabel: 'Xóa toàn bộ',
            })
            if (ok) await once(() => wipe.mutateAsync(undefined))
          }}
        >
          <Trash2 className="mr-1.5 size-4" /> Xóa toàn bộ trí nhớ
        </Button>
      </div>
    </div>
  )
}

interface MemorySectionBlockProps {
  section: MemorySection
  onAdd: (text: string) => Promise<boolean>
  onEdit: (line: MemoryLine, text: string) => Promise<boolean>
  onDelete: (line: MemoryLine) => Promise<void>
}

function MemorySectionBlock({ section, onAdd, onEdit, onDelete }: MemorySectionBlockProps) {
  const [draft, setDraft] = useState('')
  return (
    <div className="space-y-1.5">
      <div className="font-medium">{section.label}</div>
      {section.lines.length > 0 && (
        <ul className="divide-y rounded-md border">
          {section.lines.map((line) => (
            <MemoryLineRow key={line.text} line={line} onEdit={onEdit} onDelete={onDelete} />
          ))}
        </ul>
      )}
      <div className="flex gap-2">
        <Input
          value={draft}
          maxLength={300}
          placeholder={`Thêm vào «${section.label}»…`}
          aria-label={`Thêm dòng vào ${section.label}`}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.nativeEvent.isComposing && draft.trim()) {
              e.preventDefault()
              void onAdd(draft.trim()).then((ok) => ok && setDraft(''))
            }
          }}
        />
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={!draft.trim()}
          aria-label={`Thêm vào ${section.label}`}
          onClick={() => void onAdd(draft.trim()).then((ok) => ok && setDraft(''))}
        >
          <Plus className="size-4" />
        </Button>
      </div>
    </div>
  )
}

interface MemoryLineRowProps {
  line: MemoryLine
  onEdit: (line: MemoryLine, text: string) => Promise<boolean>
  onDelete: (line: MemoryLine) => Promise<void>
}

function MemoryLineRow({ line, onEdit, onDelete }: MemoryLineRowProps) {
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState(line.fact)

  if (editing) {
    return (
      <li className="flex items-center gap-2 px-3 py-2">
        <Input
          value={value}
          maxLength={300}
          autoFocus
          aria-label="Sửa dòng nhớ"
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Escape') setEditing(false)
            if (e.key === 'Enter' && !e.nativeEvent.isComposing && value.trim()) {
              e.preventDefault()
              void onEdit(line, value.trim()).then((ok) => ok && setEditing(false))
            }
          }}
        />
        <Button
          type="button"
          size="sm"
          variant="ghost"
          aria-label="Lưu"
          disabled={!value.trim()}
          onClick={() => void onEdit(line, value.trim()).then((ok) => ok && setEditing(false))}
        >
          <Check className="size-4" />
        </Button>
        <Button type="button" size="sm" variant="ghost" aria-label="Bỏ sửa" onClick={() => setEditing(false)}>
          <X className="size-4" />
        </Button>
      </li>
    )
  }

  return (
    <li className="flex items-center justify-between gap-2 px-3 py-2">
      <div className="flex flex-wrap items-center gap-1.5">
        <span>{line.fact}</span>
        {line.auto && <Badge variant="secondary">tự rút</Badge>}
        {line.until && <span className="text-xs text-muted-foreground">đến {formatDate(line.until)}</span>}
      </div>
      <div className="flex shrink-0 gap-1">
        <Button
          type="button"
          size="sm"
          variant="ghost"
          aria-label={`Sửa: ${line.fact}`}
          onClick={() => {
            setValue(line.fact)
            setEditing(true)
          }}
        >
          <Pencil className="size-4" />
        </Button>
        <Button type="button" size="sm" variant="ghost" aria-label={`Xóa: ${line.fact}`} onClick={() => void onDelete(line)}>
          <Trash2 className="size-4" />
        </Button>
      </div>
    </li>
  )
}
