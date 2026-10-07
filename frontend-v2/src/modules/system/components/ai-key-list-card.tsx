import { ArrowUp, ExternalLink, KeyRound, Pencil, Trash2 } from 'lucide-react'
import { useRef, useState, type ReactNode } from 'react'

import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'

import type { AiKeyInput, AiKeyItem, AiKeyPatch, AiProviderInfo } from '../api/agent-hub-api'

const FALLBACK_PROVIDERS: AiProviderInfo[] = [
  { name: 'gemini', label: 'Gemini', site: 'https://aistudio.google.com/apikey' },
  { name: 'claude', label: 'Claude', site: 'https://console.anthropic.com/' },
  { name: 'openai', label: 'OpenAI', site: 'https://platform.openai.com/api-keys' },
  { name: 'openrouter', label: 'OpenRouter', site: 'https://openrouter.ai/keys' },
]

/** Gợi ý model hay dùng của từng hãng — chỉ là gợi ý, gõ tên khác vẫn được. */
const MODEL_SUGGESTIONS: Record<string, string[]> = {
  gemini: ['gemini-flash-latest', 'gemini-flash-lite-latest', 'gemini-pro-latest'],
  claude: ['claude-haiku-4-5', 'claude-sonnet-4-5'],
  openai: ['gpt-5-mini', 'gpt-5'],
  openrouter: ['google/gemini-2.5-flash', 'anthropic/claude-sonnet-4.5', 'openai/gpt-5-mini', 'deepseek/deepseek-chat'],
}

interface AiKeyListCardProps {
  title: string
  description: ReactNode
  items: AiKeyItem[]
  providers?: AiProviderInfo[]
  isLoading: boolean
  canWrite: boolean
  emptyText: string
  removeMessage: string
  saving: boolean
  onAdd: (body: AiKeyInput) => Promise<unknown>
  onPatch: (id: number, body: AiKeyPatch) => void
  onRemove: (id: number) => void
}

/**
 * Danh sách khóa AI theo ƯU TIÊN (ai-CR-098, nhóm C-04) — dùng chung cho khóa CÁ NHÂN (Trang cá nhân → Khóa AI) và
 * khóa CÔNG TY (Cấu hình hệ thống → Trợ lý AI). Một bảng `tab_ai_key` ở backend, khác nhau ở chủ khóa.
 *
 * ai-CR-101 (đại ca 07/10: «cấu hình phải dễ sử dụng»): thêm khóa chỉ còn ba bước — chọn hãng, bấm «Lấy khóa» mở
 * trang của hãng, dán rồi Lưu; model và trần lượt gập vào «Tùy chọn». Mỗi dòng đọc thành một câu (model gì, trần bao
 * nhiêu, hôm nay dùng mấy lượt), sửa bằng nút «Sửa» chứ không bày ô nhập sẵn.
 *
 * Bot dùng khóa số 1; khóa đó hết tiền / hết hạn mức / sai thì tự nhảy sang khóa kế, không nhắn gì (đại ca chốt
 * 07/10/2026). Khóa thô chỉ đi VÀO (ô `password`, xóa trắng sau khi lưu); màn chỉ thấy 4 ký tự cuối.
 */
export function AiKeyListCard({
  title, description, items, providers, isLoading, canWrite, emptyText, removeMessage, saving, onAdd, onPatch,
  onRemove,
}: AiKeyListCardProps) {
  const list = providers?.length ? providers : FALLBACK_PROVIDERS
  const [provider, setProvider] = useState(list[0].name)
  const [draft, setDraft] = useState('')
  const [model, setModel] = useState('')
  const [cap, setCap] = useState('')
  const [showOptions, setShowOptions] = useState(false)
  const [editing, setEditing] = useState<number | null>(null)
  //  Chặn bấm đúp ngay trong tick (luật bốn bẫy biểu mẫu) — `saving` là state nên trễ một lượt render.
  const busy = useRef(false)
  const current = list.find((p) => p.name === provider) ?? list[0]
  const idPrefix = title.replace(/\W+/g, '-')

  async function handleSave() {
    const key = draft.trim()
    if (!key || busy.current) return
    busy.current = true
    try {
      await onAdd({ key, provider, model: model.trim(), priority: 0, daily_cap: Math.max(0, Number(cap) || 0) })
      setDraft('')
      setModel('')
      setCap('')
    } catch {
      //  Lỗi kiểm khóa đã có toast của lớp gọi API; giữ nguyên ô nhập để sửa.
    } finally {
      busy.current = false
    }
  }

  async function handleRemove(item: AiKeyItem) {
    const ok = await confirm({
      title: 'Gỡ khóa AI',
      message: `Gỡ khóa ${item.provider_label} ${item.hint}? ${removeMessage}`,
      confirmLabel: 'Gỡ khóa',
    })
    if (ok) onRemove(item.id)
  }

  function moveUp(index: number) {
    const cur = items[index]
    const prev = items[index - 1]
    if (!cur || !prev) return
    onPatch(cur.id, { priority: prev.priority })
    onPatch(prev.id, { priority: cur.priority === prev.priority ? cur.priority + 1 : cur.priority })
  }

  return (
    <Card>
      <CardHeader>
        <SectionHeading>{title}</SectionHeading>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <div className="text-muted-foreground">{description}</div>

        {isLoading && <Skeleton className="h-10 w-full" />}
        {!isLoading && items.length === 0 && (
          <p className="rounded-md border border-dashed p-3 text-muted-foreground">{emptyText}</p>
        )}
        {!isLoading && items.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">
              Bot dùng khóa số 1; khóa đó hết tiền, hết hạn mức hay sai thì tự chuyển sang số 2, số 3…
            </p>
            <ul className="divide-y rounded-md border">
              {items.map((item, index) => (
                <li key={item.id} className="space-y-2 px-3 py-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="flex size-6 items-center justify-center rounded-full bg-muted text-xs font-medium">
                      {index + 1}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="font-medium">{item.provider_label}</span>{' '}
                      <span className="font-mono text-xs text-muted-foreground">{item.hint}</span>
                      <span className="block text-xs text-muted-foreground">
                        Model: {item.model || 'mặc định'} · Trần: {item.daily_cap > 0 ? `${item.daily_cap} lượt/ngày` : 'không'} ·
                        Hôm nay {item.used_today} lượt
                      </span>
                    </span>
                    {canWrite && index > 0 && (
                      <Button type="button" variant="ghost" size="sm" aria-label={`Đưa khóa ${item.hint} lên trước`}
                              onClick={() => moveUp(index)}>
                        <ArrowUp className="size-4" />
                      </Button>
                    )}
                    {canWrite && (
                      <Button type="button" variant="ghost" size="sm" aria-label={`Sửa khóa ${item.hint}`}
                              onClick={() => setEditing(editing === item.id ? null : item.id)}>
                        <Pencil className="size-4" />
                      </Button>
                    )}
                    {canWrite && (
                      <Button type="button" variant="ghost" size="sm" onClick={() => void handleRemove(item)}>
                        <Trash2 className="mr-1 size-4" /> Gỡ khóa
                      </Button>
                    )}
                  </div>
                  {editing === item.id && (
                    <KeyEditRow item={item} onSave={(body) => { onPatch(item.id, body); setEditing(null) }} />
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {canWrite && (
          <div className="space-y-3 rounded-md border bg-muted/30 p-3">
            <p className="font-medium">Thêm khóa</p>
            <div className="flex flex-wrap items-end gap-2">
              <div className="space-y-1">
                <Label htmlFor={`${idPrefix}-provider`}>1. Hãng</Label>
                <select
                  id={`${idPrefix}-provider`}
                  className="h-9 rounded-md border bg-background px-2 text-sm"
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                >
                  {list.map((p) => (
                    <option key={p.name} value={p.name}>{p.label}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <span className="block text-sm font-medium">2. Lấy khóa</span>
                <Button asChild type="button" variant="outline" size="sm" className="h-9">
                  <a href={current.site} target="_blank" rel="noreferrer">
                    <ExternalLink className="mr-1.5 size-4" /> Mở trang {current.label}
                  </a>
                </Button>
              </div>
              <div className="min-w-56 flex-1 space-y-1">
                <Label htmlFor={`${idPrefix}-key`}>3. Dán khóa {current.label}</Label>
                <Input
                  id={`${idPrefix}-key`}
                  type="password"
                  autoComplete="off"
                  spellCheck={false}
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      void handleSave()
                    }
                  }}
                />
              </div>
              <Button type="button" size="sm" className="h-9" onClick={() => void handleSave()}
                      disabled={!draft.trim() || saving}>
                <KeyRound className="mr-1.5 size-4" /> {saving ? 'Đang kiểm…' : 'Lưu khóa'}
              </Button>
            </div>
            <button type="button" className="text-xs font-medium text-primary hover:underline"
                    onClick={() => setShowOptions((v) => !v)}>
              {showOptions ? 'Ẩn tùy chọn' : 'Tùy chọn: chọn model, đặt trần lượt mỗi ngày'}
            </button>
            {showOptions && (
              <div className="flex flex-wrap items-end gap-2">
                <div className="space-y-1">
                  <Label htmlFor={`${idPrefix}-model`}>Model (để trống = mặc định)</Label>
                  <Input id={`${idPrefix}-model`} className="w-64" list={`${idPrefix}-models`}
                         placeholder={MODEL_SUGGESTIONS[provider]?.[0] ?? ''} value={model}
                         onChange={(e) => setModel(e.target.value)} />
                  <datalist id={`${idPrefix}-models`}>
                    {(MODEL_SUGGESTIONS[provider] ?? []).map((m) => <option key={m} value={m} />)}
                  </datalist>
                </div>
                <div className="space-y-1">
                  <Label htmlFor={`${idPrefix}-cap`}>Trần lượt/ngày (0 = không giới hạn)</Label>
                  <Input id={`${idPrefix}-cap`} className="w-40" type="number" min={0} value={cap}
                         onChange={(e) => setCap(e.target.value)} />
                </div>
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              Hệ thống gọi thử hãng một lượt không tốn token rồi mới lưu (đã mã hóa). Cùng hãng thì khóa mới thay khóa cũ.
              Không bao giờ dán khóa vào khung chat.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function KeyEditRow({ item, onSave }: { item: AiKeyItem; onSave: (body: AiKeyPatch) => void }) {
  const [model, setModel] = useState(item.model)
  const [cap, setCap] = useState(item.daily_cap ? String(item.daily_cap) : '')
  const listId = `edit-models-${item.id}`
  return (
    <div className="flex flex-wrap items-end gap-2 pl-8">
      <div className="space-y-1">
        <Label htmlFor={`edit-model-${item.id}`}>Model (để trống = mặc định)</Label>
        <Input id={`edit-model-${item.id}`} className="h-8 w-64 text-xs" list={listId} value={model}
               onChange={(e) => setModel(e.target.value)} />
        <datalist id={listId}>
          {(MODEL_SUGGESTIONS[item.provider] ?? []).map((m) => <option key={m} value={m} />)}
        </datalist>
      </div>
      <div className="space-y-1">
        <Label htmlFor={`edit-cap-${item.id}`}>Trần lượt/ngày</Label>
        <Input id={`edit-cap-${item.id}`} className="h-8 w-32 text-xs" type="number" min={0} value={cap}
               onChange={(e) => setCap(e.target.value)} />
      </div>
      <Button type="button" size="sm" className="h-8"
              onClick={() => onSave({ model: model.trim(), daily_cap: Math.max(0, Number(cap) || 0) })}>
        Lưu
      </Button>
    </div>
  )
}
