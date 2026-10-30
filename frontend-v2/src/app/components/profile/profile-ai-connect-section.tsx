import { CheckCircle2, CircleDashed, Copy, Eye, EyeOff, PlayCircle, Plug, RefreshCw, Trash2 } from 'lucide-react'
import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { ConnectGuide } from '@/modules/ai-skill/components/connect-guide'
import { CallStatusBadge, KeyStateBadge, SecurityLevelBadge } from '@/modules/ai-skill/config/ai-skill-meta'
import {
  KEY_KIND,
  KEY_STATE,
  LIVE_KEY_STATES,
  TOGGLEABLE_KEY_STATES,
  maskKey,
  upperFirst,
} from '@/modules/ai-skill/config/ai-skill-constants'
import {
  useClaimKey,
  useCreateMyKey,
  useLastCall,
  useMyKeys,
  useMyRecentCalls,
  usePendingKeys,
  useRemoveMyKey,
  useRevealKey,
  useSetKeyEnabled,
  useVisibleSkills,
} from '@/modules/ai-skill/hooks/use-my-ai'
import type { MyMcpKey } from '@/modules/ai-skill/types/ai-skill'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { ChapterDemo } from '@/shared/ui/chapter-demo/chapter-demo'
import { AI_SKILL_INTRO_CHAPTERS } from '@/shared/ui/chapter-demo/scripts/ai-skill-intro'
import { confirm } from '@/shared/ui/confirm-dialog'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { Switch } from '@/shared/ui/switch'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'

/**
 * Khóa thô đang nằm trong bộ nhớ của màn (vừa tạo / vừa nhận / vừa bấm Hiện) — tải lại trang là mất, muốn xem lại thì bấm
 * Hiện (mỗi lần máy chủ ghi một dòng nhật ký). KHÔNG đưa vào bộ đệm truy vấn.
 */
type RawKeys = Record<number, string>

/**
 * Mục "Kết nối AI riêng" = màn "AI của tôi" (G8, doc 21 §6.2; K6 bao-CR-624; bước 2 làm lại kiểu CoreSkill ở bao-CR-638).
 *
 * Đường chính từ 17/10/2026: nhân sự dùng gói AI của CHÍNH HỌ (Claude, ChatGPT, Cursor…) tra ERP đúng quyền của họ.
 * Ba bước: chọn ứng dụng (đoạn cấu hình điền khóa của dòng đang chọn ở bước 2) → khóa của bạn (bật / tắt, Hiện / Ẩn,
 * Sao chép, Gỡ) → kiểm tra kết nối. Dưới cùng: AI của bạn đang đọc được skill nào, 20 lượt gần nhất. Viết cho nhân viên
 * văn phòng — tiêu đề không dùng chữ MCP.
 *
 * Xem lại khóa (ai-CR-221) chỉ gọi khi người dùng BẤM Hiện / Sao chép — mở màn không bao giờ gọi.
 */
export function ProfileAiConnectSection() {
  const [rawKeys, setRawKeys] = useState<RawKeys>({})
  const [selectedId, setSelectedId] = useState(0)
  const [demoOpen, setDemoOpen] = useState(false)
  const mine = useMyKeys()
  const reveal = useRevealKey()

  const items = mine.data?.items ?? []
  const usable = items.filter((k) => k.kind !== KEY_KIND.oauth && TOGGLEABLE_KEY_STATES.includes(k.state))
  const selected = usable.find((k) => k.id === selectedId) ?? usable[0] ?? null

  function remember(id: number, raw: string) {
    setRawKeys((prev) => ({ ...prev, [id]: raw }))
  }

  /** Khóa thô của một dòng: có trong bộ nhớ thì dùng, không thì xin máy chủ (một lượt xem lại, có ghi nhật ký). */
  async function obtainKey(key: MyMcpKey): Promise<string | null> {
    if (rawKeys[key.id]) return rawKeys[key.id]
    if (!key.revealable) return null
    try {
      const out = await reveal.mutateAsync(key.id)
      if (!out.key) return null
      remember(key.id, out.key)
      return out.key
    } catch {
      return null //  409 kèm câu cho người dùng — toast tự động.
    }
  }

  const canObtain = Boolean(selected && (rawKeys[selected.id] || selected.revealable))

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <p className="max-w-2xl text-sm text-muted-foreground">
          Dùng Claude, ChatGPT, Cursor… của chính bạn để tra cứu phiếu, đơn hàng, công việc trong ERP —{' '}
          <b className="text-foreground">đúng phạm vi quyền của bạn</b>. Tiền dùng AI tính vào gói của bạn, không tính
          vào ví công ty.
        </p>
        <Button type="button" variant="outline" size="sm" onClick={() => setDemoOpen(true)}>
          <PlayCircle className="size-4" />
          Xem cách hoạt động
        </Button>
      </div>
      <Card>
        <CardHeader>
          <StepHeading step={1} title="Chọn ứng dụng AI bạn đang dùng" />
        </CardHeader>
        <CardContent>
          <ConnectGuide
            source="private"
            keySlot={{
              label: selected ? selected.name || selected.hint : '',
              value: selected ? (rawKeys[selected.id] ?? null) : null,
              obtain: selected && canObtain ? () => obtainKey(selected) : undefined,
            }}
          />
        </CardContent>
      </Card>
      <KeysStep
        items={items}
        loading={mine.isLoading}
        rawKeys={rawKeys}
        selectedId={selected?.id ?? 0}
        onSelect={setSelectedId}
        onRemember={remember}
        obtainKey={obtainKey}
      />
      <CheckStep preferredKeyId={selected?.id ?? 0} />
      <VisibleSkillsCard />
      <RecentCallsCard />

      {/*  Demo mở trong hộp, không dẫn sang `/ai-skill/intro`: nhân viên thường không vào được phân hệ Kho skill AI. */}
      <Dialog open={demoOpen} onOpenChange={setDemoOpen}>
        <DialogContent className="max-h-[92dvh] overflow-y-auto sm:max-w-4xl">
          <DialogHeader>
            <DialogTitle>Kho skill AI chạy thế nào</DialogTitle>
            <DialogDescription>Dữ liệu trong demo là giả, chỉ để minh họa.</DialogDescription>
          </DialogHeader>
          {demoOpen && <ChapterDemo chapters={AI_SKILL_INTRO_CHAPTERS} />}
        </DialogContent>
      </Dialog>
    </div>
  )
}

function StepHeading({ step, title }: { step: number; title: string }) {
  return (
    <SectionHeading>
      Bước {step} · {title}
    </SectionHeading>
  )
}

// ---------------------------------------------------------------------------------------------------------------------
// Bước 2 — khóa của bạn: khóa chờ nhận, mỗi khóa một dòng (bật / tắt, Hiện / Ẩn, Sao chép, Gỡ), tạo khóa mới
// ---------------------------------------------------------------------------------------------------------------------

interface KeysStepProps {
  items: MyMcpKey[]
  loading: boolean
  rawKeys: RawKeys
  selectedId: number
  onSelect: (id: number) => void
  onRemember: (id: number, raw: string) => void
  obtainKey: (key: MyMcpKey) => Promise<string | null>
}

function KeysStep({ items, loading, rawKeys, selectedId, onSelect, onRemember, obtainKey }: KeysStepProps) {
  const pending = usePendingKeys()
  const create = useCreateMyKey()
  const claim = useClaimKey()
  const [name, setName] = useState('')
  const [scope, setScope] = useState(0)
  const creating = useRef(false)

  const pendingItems = pending.data?.items ?? []
  //  Khóa chờ nhận đã có ở khối riêng phía trên — danh sách bên dưới chỉ bày khóa đã nhận / tự tạo / kết nối OAuth.
  const myItems = items.filter((k) => k.state !== KEY_STATE.pending)

  async function handleCreate() {
    if (creating.current) return
    creating.current = true
    try {
      const created = await create.mutateAsync({ name: name.trim(), scope, days: 90 })
      if (created.key) onRemember(created.id, created.key)
      onSelect(created.id)
      setName('')
    } catch {
      //  Toast lỗi tự động (vd đã đủ số khóa tối đa).
    } finally {
      creating.current = false
    }
  }

  async function handleClaim(key: MyMcpKey) {
    try {
      const claimed = await claim.mutateAsync(key.id)
      if (claimed.key) onRemember(claimed.id, claimed.key)
      onSelect(claimed.id)
    } catch {
      //  404: đã nhận rồi / bị thu hồi / hết hạn — toast tự động.
    }
  }

  return (
    <Card>
      <CardHeader>
        <StepHeading step={2} title="Khóa của bạn" />
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {pendingItems.length > 0 && (
          <div className="space-y-2">
            <p className="font-medium">Khóa quản trị phát cho bạn, chờ nhận</p>
            <ul className="divide-y rounded-md border">
              {pendingItems.map((k) => (
                <li key={k.id} className="flex flex-wrap items-center gap-3 px-3 py-2">
                  <span className="min-w-0 flex-1">
                    {k.name || 'Khóa kết nối'}{' '}
                    <span className="text-xs text-muted-foreground">
                      · {k.scope_label} · hết hạn {formatDateTime(k.expires_at)}
                    </span>
                  </span>
                  <Button type="button" size="sm" onClick={() => void handleClaim(k)} disabled={claim.isPending}>
                    Nhận khóa
                  </Button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {loading ? (
          <Skeleton className="h-10 w-full" />
        ) : myItems.length > 0 ? (
          <ul className="divide-y rounded-md border" aria-label="Khóa của bạn">
            {myItems.map((k) => (
              <KeyRow
                key={k.id}
                item={k}
                raw={rawKeys[k.id] ?? null}
                selected={k.id === selectedId}
                onSelect={() => onSelect(k.id)}
                obtainKey={() => obtainKey(k)}
              />
            ))}
          </ul>
        ) : (
          pendingItems.length === 0 && <p className="text-muted-foreground">Chưa có khóa nào. Tạo một khóa bên dưới.</p>
        )}

        <div className="flex flex-wrap items-end gap-2 border-t pt-4">
          <div className="space-y-1">
            <Label htmlFor="ai-connect-key-name">Tên khóa</Label>
            <Input
              id="ai-connect-key-name"
              className="w-56"
              placeholder="Claude máy công ty"
              maxLength={80}
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="ai-connect-key-scope">Mức</Label>
            <select
              id="ai-connect-key-scope"
              className="h-9 rounded-md border bg-background px-2 text-sm"
              value={scope}
              onChange={(e) => setScope(Number(e.target.value))}
            >
              <option value={0}>Chỉ đọc</option>
              <option value={1}>Được ghi</option>
            </select>
          </div>
          <Button type="button" size="sm" onClick={() => void handleCreate()} disabled={create.isPending}>
            <Plug className="mr-1.5 size-4" /> Tạo khóa
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          Mức Chỉ đọc là đủ cho tra cứu. Được ghi cho AI soạn nháp và tạo phiếu (luôn hỏi bạn xác nhận trước); đề nghị
          thanh toán vẫn chỉ tạo trên web. Khóa hạn 90 ngày. Tắt khóa khi tạm không dùng, bật lại là chạy ngay; Gỡ là bỏ
          hẳn.
        </p>
      </CardContent>
    </Card>
  )
}

interface KeyRowProps {
  item: MyMcpKey
  raw: string | null
  selected: boolean
  onSelect: () => void
  obtainKey: () => Promise<string | null>
}

/** Một khóa: chọn để điền ở bước 1 · bật / tắt · khóa đầy đủ (ẩn mặc định, Hiện / Ẩn, Sao chép) · mức, hạn, lần dùng · Gỡ. */
function KeyRow({ item: k, raw, selected, onSelect, obtainKey }: KeyRowProps) {
  const remove = useRemoveMyKey()
  const setEnabled = useSetKeyEnabled()
  const [visible, setVisible] = useState(false)
  const [loadingKey, setLoadingKey] = useState(false)
  const busy = useRef(false)
  const oauth = k.kind === KEY_KIND.oauth
  const toggleable = TOGGLEABLE_KEY_STATES.includes(k.state)
  const enabled = k.enabled ?? k.state !== KEY_STATE.disabled
  const label = k.name || k.hint
  const canSeeKey = !oauth && (Boolean(raw) || Boolean(k.revealable))

  /** Hiện / Sao chép cần khóa thô — xin máy chủ ĐÚNG lúc bấm; chặn bấm đúp kẻo ghi hai dòng nhật ký. */
  async function withKey(then: (value: string) => void | Promise<void>) {
    if (busy.current) return
    busy.current = true
    setLoadingKey(true)
    try {
      const value = raw ?? (await obtainKey())
      if (value) await then(value)
    } finally {
      busy.current = false
      setLoadingKey(false)
    }
  }

  async function copyKey(value: string) {
    try {
      if (!navigator.clipboard) throw new Error('clipboard unavailable')
      await navigator.clipboard.writeText(value)
      toast.success('Đã chép khóa.')
    } catch {
      toast.error('Không chép được — bấm Hiện rồi bôi đen khóa để chép tay.')
    }
  }

  async function handleRemove() {
    const ok = await confirm({
      title: oauth ? 'Gỡ kết nối' : 'Gỡ khóa kết nối',
      message: `Gỡ "${label}"? Ứng dụng AI đang dùng ${oauth ? 'kết nối' : 'khóa'} này sẽ không tra được ERP nữa.`,
      confirmLabel: 'Gỡ',
    })
    if (ok) remove.mutate(k.id)
  }

  return (
    <li className={cn('space-y-2 px-3 py-2', selected && 'bg-accent/40')}>
      <div className="flex flex-wrap items-center gap-3">
        {!oauth && toggleable && (
          <input
            type="radio"
            name="ai-connect-selected-key"
            className="size-4 accent-primary"
            checked={selected}
            onChange={onSelect}
            aria-label={`Dùng khóa ${label} cho bước 1`}
          />
        )}
        <span className="min-w-0 flex-1 font-medium">{k.name || 'Khóa kết nối'}</span>
        <KeyStateBadge state={k.state} label={k.state_label} />
        {toggleable && (
          <Switch
            checked={enabled}
            disabled={setEnabled.isPending}
            onCheckedChange={(checked) => setEnabled.mutate({ id: k.id, enabled: checked })}
            aria-label={`${enabled ? 'Tắt' : 'Bật'} khóa ${label}`}
          />
        )}
        {LIVE_KEY_STATES.includes(k.state) && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            aria-label={`Gỡ khóa ${label}`}
            onClick={() => void handleRemove()}
            disabled={remove.isPending}
          >
            <Trash2 className="mr-1 size-4" /> Gỡ
          </Button>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <div className="min-w-0 flex-1 rounded bg-muted px-2 py-1">
          {oauth ? (
            <span className="text-xs text-muted-foreground">{k.kind_label || 'Kết nối OAuth'} · ứng dụng tự giữ mã</span>
          ) : visible && raw ? (
            <code className="text-xs break-all">{raw}</code>
          ) : (
            <code className="text-xs text-muted-foreground">{maskKey(k.hint)}</code>
          )}
        </div>
        {canSeeKey ? (
          <>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={loadingKey}
              onClick={() => (visible ? setVisible(false) : void withKey(() => setVisible(true)))}
            >
              {visible ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
              {visible ? 'Ẩn' : 'Hiện'}
            </Button>
            <Button type="button" variant="outline" size="sm" disabled={loadingKey} onClick={() => void withKey(copyKey)}>
              <Copy className="size-4" />
              Sao chép
            </Button>
          </>
        ) : (
          !oauth && <span className="text-xs text-muted-foreground">Không xem lại được — tạo lại để xem.</span>
        )}
      </div>
      <p className="text-xs text-muted-foreground">
        {upperFirst(k.scope_label)} · hết hạn {formatDateTime(k.expires_at)}
        {k.last_used_at ? ` · dùng lần cuối ${formatDateTime(k.last_used_at)}` : ' · chưa dùng'}
      </p>
    </li>
  )
}

// ---------------------------------------------------------------------------------------------------------------------
// Bước 3 — kiểm tra kết nối: lượt gọi gần nhất của khóa
// ---------------------------------------------------------------------------------------------------------------------

function CheckStep({ preferredKeyId }: { preferredKeyId: number }) {
  const mine = useMyKeys()
  const live = (mine.data?.items ?? []).filter((k) => k.state === KEY_STATE.active)
  const [picked, setPicked] = useState(0)
  const keyId =
    [picked, preferredKeyId].find((id) => id > 0 && live.some((k) => k.id === id)) ?? live[0]?.id ?? 0
  const last = useLastCall(keyId)

  return (
    <Card>
      <CardHeader>
        <StepHeading step={3} title="Kiểm tra kết nối" />
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {live.length === 0 ? (
          <p className="text-muted-foreground">Có khóa ở bước 2 rồi quay lại đây kiểm tra.</p>
        ) : (
          <>
            {live.length > 1 && (
              <div className="space-y-1">
                <Label htmlFor="ai-connect-check-key">Khóa cần kiểm tra</Label>
                <select
                  id="ai-connect-check-key"
                  className="h-9 rounded-md border bg-background px-2 text-sm"
                  value={keyId}
                  onChange={(e) => setPicked(Number(e.target.value))}
                >
                  {live.map((k) => (
                    <option key={k.id} value={k.id}>
                      {k.name || 'Khóa'} {k.hint}
                    </option>
                  ))}
                </select>
              </div>
            )}
            {last.isLoading ? (
              <Skeleton className="h-10 w-full" />
            ) : last.data?.connected ? (
              <p className="flex items-start gap-2 text-success">
                <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
                <span>
                  Đã nối. Lượt thành công gần nhất {formatDateTime(last.data.last_ok_call?.created_at ?? null)}
                  {last.data.last_ok_call?.client_name ? ` từ ${last.data.last_ok_call.client_name}` : ''}
                  {last.data.last_ok_call?.tool ? ` (công cụ ${last.data.last_ok_call.tool})` : ''}.
                </span>
              </p>
            ) : (
              <div className="flex items-start gap-2 text-muted-foreground">
                <CircleDashed className="mt-0.5 size-4 shrink-0" />
                <span>
                  Chưa thấy lượt thành công nào từ khóa này. Làm xong bước 1, khởi động lại ứng dụng AI, hỏi nó một câu
                  về ERP (ví dụ: việc của tôi hôm nay), rồi bấm Kiểm tra lại.
                  {last.data?.last_call && (
                    <span className="mt-1 block">
                      Lượt gần nhất {formatDateTime(last.data.last_call.created_at)}:{' '}
                      <CallStatusBadge status={last.data.last_call.status} label={last.data.last_call.status_label} />
                      {last.data.last_call.deny_reason && ` ${last.data.last_call.deny_reason}`}
                    </span>
                  )}
                </span>
              </div>
            )}
            <Button type="button" variant="outline" size="sm" onClick={() => void last.refetch()} disabled={last.isFetching}>
              <RefreshCw className={cn('size-4', last.isFetching && 'animate-spin')} />
              Kiểm tra lại
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  )
}

// ---------------------------------------------------------------------------------------------------------------------
// AI của bạn đang đọc được + lịch sử 20 lượt
// ---------------------------------------------------------------------------------------------------------------------

function VisibleSkillsCard() {
  const { data, isLoading } = useVisibleSkills()
  const items = data?.items ?? []
  return (
    <Card>
      <CardHeader>
        <SectionHeading>AI của bạn đang đọc được ({items.length})</SectionHeading>
      </CardHeader>
      <CardContent className="text-sm">
        {isLoading ? (
          <Skeleton className="h-16 w-full" />
        ) : items.length === 0 ? (
          <p className="text-muted-foreground">
            Chưa có cẩm nang nào được gán cho bạn. AI vẫn tra được dữ liệu ERP theo quyền của bạn.
          </p>
        ) : (
          <ul className="divide-y rounded-md border">
            {items.map((s) => (
              <li key={s.skill_id} className="space-y-0.5 px-3 py-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium">{s.title || s.slug}</span>
                  <SecurityLevelBadge level={s.security_level} label={s.security_level_label} />
                  <span className="text-xs text-muted-foreground">
                    {s.skill_set} · v{s.version_no}
                  </span>
                </div>
                {s.summary && <p className="text-xs text-muted-foreground">{s.summary}</p>}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}

function RecentCallsCard() {
  const { data, isLoading } = useMyRecentCalls()
  const items = data?.items ?? []
  return (
    <Card>
      <CardHeader>
        <SectionHeading>20 lượt gần nhất của bạn</SectionHeading>
      </CardHeader>
      <CardContent className="text-sm">
        {isLoading ? (
          <Skeleton className="h-16 w-full" />
        ) : items.length === 0 ? (
          <p className="text-muted-foreground">Chưa có lượt nào.</p>
        ) : (
          <ul className="divide-y rounded-md border">
            {items.map((c) => (
              <li key={c.id} className="flex flex-wrap items-center gap-x-3 gap-y-1 px-3 py-2">
                <span className="text-xs whitespace-nowrap text-muted-foreground">{formatDateTime(c.created_at)}</span>
                <span className="min-w-0 flex-1 truncate">
                  {c.client_name || 'Ứng dụng AI'} · <span className="font-mono text-xs">{c.tool || c.method}</span>
                </span>
                <CallStatusBadge status={c.status} label={c.status_label} />
                {c.deny_reason && <span className="w-full text-xs text-muted-foreground">{c.deny_reason}</span>}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
