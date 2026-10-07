import { ArrowUp, KeyRound, Trash2 } from 'lucide-react'
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

const MODEL_HINT: Record<string, string> = {
  gemini: 'gemini-flash-latest',
  claude: 'claude-haiku-4-5',
  openai: 'gpt-5-mini',
  openrouter: 'google/gemini-2.5-flash',
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
 * Bot dùng khóa ưu tiên 1; khóa đó hết tiền / hết hạn mức / sai thì tự nhảy sang khóa kế, không nhắn gì (đại ca chốt
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
  //  Chặn bấm đúp ngay trong tick (luật bốn bẫy biểu mẫu) — `saving` là state nên trễ một lượt render.
  const busy = useRef(false)
  const site = list.find((p) => p.name === provider)?.site ?? ''
  const label = list.find((p) => p.name === provider)?.label ?? provider

  async function handleSave() {
    const key = draft.trim()
    if (!key || busy.current) return
    busy.current = true
    try {
      await onAdd({ key, provider, model: model.trim(), priority: 0, daily_cap: 0 })
      setDraft('')
      setModel('')
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
      <CardContent className="space-y-3 text-sm">
        <div className="text-muted-foreground">{description}</div>
        {isLoading && <Skeleton className="h-10 w-full" />}
        {!isLoading && items.length === 0 && (
          <p className="rounded-md border border-dashed p-3 text-muted-foreground">{emptyText}</p>
        )}
        {!isLoading && items.length > 0 && (
          <ul className="divide-y rounded-md border">
            {items.map((item, index) => (
              <li key={item.id} className="flex flex-wrap items-center gap-2 px-3 py-2">
                <span className="w-6 text-center font-mono text-xs text-muted-foreground">{index + 1}</span>
                <span className="min-w-0 flex-1">
                  <span className="font-medium">{item.provider_label}</span>{' '}
                  <span className="font-mono text-xs text-muted-foreground">{item.hint}</span>
                  <span className="block text-xs text-muted-foreground">
                    hôm nay {item.used_today}
                    {item.daily_cap > 0 ? `/${item.daily_cap}` : ''} lượt
                  </span>
                </span>
                <Input
                  aria-label={`Model của khóa ${item.hint}`}
                  className="h-8 w-48 text-xs"
                  placeholder={MODEL_HINT[item.provider] ?? 'model mặc định'}
                  defaultValue={item.model}
                  disabled={!canWrite}
                  onBlur={(e) => {
                    if (e.target.value.trim() !== item.model) onPatch(item.id, { model: e.target.value.trim() })
                  }}
                />
                <Input
                  aria-label={`Trần lượt mỗi ngày của khóa ${item.hint}`}
                  className="h-8 w-24 text-xs"
                  type="number"
                  min={0}
                  placeholder="trần/ngày"
                  defaultValue={item.daily_cap || ''}
                  disabled={!canWrite}
                  onBlur={(e) => {
                    const v = Math.max(0, Number(e.target.value) || 0)
                    if (v !== item.daily_cap) onPatch(item.id, { daily_cap: v })
                  }}
                />
                {canWrite && index > 0 && (
                  <Button type="button" variant="ghost" size="sm" aria-label={`Đưa khóa ${item.hint} lên trước`}
                          onClick={() => moveUp(index)}>
                    <ArrowUp className="size-4" />
                  </Button>
                )}
                {canWrite && (
                  <Button type="button" variant="ghost" size="sm" onClick={() => void handleRemove(item)}>
                    <Trash2 className="mr-1 size-4" /> Gỡ khóa
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
        {canWrite && (
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-end gap-2">
              <div className="space-y-1">
                <Label htmlFor={`ai-key-provider-${title}`}>Hãng</Label>
                <select
                  id={`ai-key-provider-${title}`}
                  className="h-9 rounded-md border bg-background px-2 text-sm"
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                >
                  {list.map((p) => (
                    <option key={p.name} value={p.name}>{p.label}</option>
                  ))}
                </select>
              </div>
              <div className="min-w-56 flex-1 space-y-1">
                <Label htmlFor={`ai-key-input-${title}`}>Dán khóa {label}</Label>
                <Input
                  id={`ai-key-input-${title}`}
                  type="password"
                  autoComplete="off"
                  spellCheck={false}
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor={`ai-key-model-${title}`}>Model (tùy chọn)</Label>
                <Input
                  id={`ai-key-model-${title}`}
                  className="w-52"
                  placeholder={MODEL_HINT[provider] ?? ''}
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                />
              </div>
              <Button type="button" size="sm" onClick={() => void handleSave()} disabled={!draft.trim() || saving}>
                <KeyRound className="mr-1.5 size-4" /> {saving ? 'Đang kiểm…' : 'Lưu khóa'}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Lấy khóa ở{' '}
              <a className="font-medium text-primary hover:underline" href={site} target="_blank" rel="noreferrer">{site}</a>.
              Hệ thống gọi thử hãng một lượt không tốn token rồi mới lưu (đã mã hóa). Cùng hãng thì khóa mới thay khóa cũ.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
