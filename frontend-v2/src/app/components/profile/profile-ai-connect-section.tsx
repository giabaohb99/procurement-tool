import { CheckCircle2, CircleDashed, Download, Globe, MonitorSmartphone, PlayCircle, Plug, RefreshCw, SquareTerminal, Trash2 } from 'lucide-react'
import { useState } from 'react'

import { CallStatusBadge, KeyStateBadge, SecurityLevelBadge } from '@/modules/ai-skill/config/ai-skill-meta'
import { KEY_STATE } from '@/modules/ai-skill/config/ai-skill-constants'
import {
  useClaimKey,
  useCreateMyKey,
  useLastCall,
  useMyKeys,
  useMyRecentCalls,
  usePendingKeys,
  useRemoveMyKey,
  useSetup,
  useSetupClients,
  useVisibleSkills,
} from '@/modules/ai-skill/hooks/use-my-ai'
import type { McpSetupDetail, MyMcpKey } from '@/modules/ai-skill/types/ai-skill'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { ChapterDemo } from '@/shared/ui/chapter-demo/chapter-demo'
import { AI_SKILL_INTRO_CHAPTERS } from '@/shared/ui/chapter-demo/scripts/ai-skill-intro'
import { confirm } from '@/shared/ui/confirm-dialog'
import { CopyButton } from '@/shared/ui/copy-button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'

/** Khóa thô vừa tạo / vừa nhận — chỉ sống trong bộ nhớ của màn, tải lại trang là mất (máy chủ không trả lại lần hai). */
interface RevealedKey {
  id: number
  key: string
  label: string
}

const CLIENT_ICONS: Record<string, typeof Plug> = {
  claude_desktop: MonitorSmartphone,
  claude_code: SquareTerminal,
  cursor: SquareTerminal,
  gemini_cli: SquareTerminal,
  claude_ai: Globe,
  chatgpt: Globe,
}

const LIVE_STATES: number[] = [KEY_STATE.pending, KEY_STATE.active]

/**
 * Mục «Kết nối AI riêng» = màn «AI của tôi» (G8, doc 21 §6.2, K6 bao-CR-624 — hoàn thiện bản tách ở P0 bao-CR-620).
 *
 * Đường chính từ 17/10/2026: nhân sự dùng gói AI của CHÍNH HỌ (Claude, ChatGPT, Cursor…) tra ERP đúng quyền của họ.
 * Ba bước theo đúng thứ tự làm: chọn ứng dụng → có khóa (tự tạo hoặc nhận khóa quản trị phát hộ) → kiểm tra kết nối.
 * Người chưa nối mở ra là vào thẳng bước 1 (doc 21 §6.3). Dưới cùng: AI của bạn đang đọc được skill nào, 20 lượt gần
 * nhất. Viết cho nhân viên văn phòng — tiêu đề không dùng chữ MCP.
 *
 * Khóa thô chỉ hiện một lần (lúc tạo / nhận); đoạn cấu hình ở bước 1 tự điền khóa đó vào chỗ giữ `<KHÓA_CỦA_BẠN>`.
 */
export function ProfileAiConnectSection() {
  const [revealed, setRevealed] = useState<RevealedKey | null>(null)
  const [demoOpen, setDemoOpen] = useState(false)

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
      <SetupStep revealed={revealed} />
      <KeysStep revealed={revealed} onReveal={setRevealed} />
      <CheckStep preferredKeyId={revealed?.id ?? 0} />
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
// Bước 1 — chọn ứng dụng AI, hiện đúng đoạn cấu hình
// ---------------------------------------------------------------------------------------------------------------------

function SetupStep({ revealed }: { revealed: RevealedKey | null }) {
  const { data, isLoading } = useSetupClients()
  const clients = data?.clients ?? []
  const [chosen, setChosen] = useState('')
  const client = chosen || clients.find((c) => c.supported)?.client || clients[0]?.client || ''
  const setup = useSetup(client)

  return (
    <Card>
      <CardHeader>
        <StepHeading step={1} title="Chọn ứng dụng AI bạn đang dùng" />
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {isLoading ? (
          <Skeleton className="h-10 w-full" />
        ) : (
          <div className="flex flex-wrap gap-2" role="group" aria-label="Ứng dụng AI">
            {clients.map((c) => {
              const Icon = CLIENT_ICONS[c.client] ?? Plug
              const active = c.client === client
              return (
                <button
                  key={c.client}
                  type="button"
                  aria-pressed={active}
                  onClick={() => setChosen(c.client)}
                  className={cn(
                    'flex items-center gap-2 rounded-md border px-3 py-2 text-sm hover:bg-accent',
                    active && 'border-primary bg-accent font-medium',
                    !c.supported && 'text-muted-foreground',
                  )}
                >
                  <Icon className="size-4" />
                  {c.label}
                </button>
              )
            })}
          </div>
        )}

        {setup.isLoading && client && <Skeleton className="h-32 w-full" />}
        {setup.data && <SetupDetail detail={setup.data} revealed={revealed} />}
      </CardContent>
    </Card>
  )
}

function SetupDetail({ detail, revealed }: { detail: McpSetupDetail; revealed: RevealedKey | null }) {
  if (!detail.supported) {
    return (
      <p className="rounded-md border border-dashed p-3 text-muted-foreground">
        {detail.note || `${detail.label} chưa nối được với ERP. Hãy dùng một ứng dụng khác trong danh sách.`}
      </p>
    )
  }
  const filled = revealed && detail.placeholder ? detail.snippet.replaceAll(detail.placeholder, revealed.key) : detail.snippet
  const files = detail.files ?? {}
  return (
    <div className="space-y-3">
      {(detail.requires ?? []).length > 0 && (
        <p className="flex items-start gap-2 text-muted-foreground">
          <Download className="mt-0.5 size-4 shrink-0" />
          <span>Cần cài trước: {(detail.requires ?? []).join(', ')}</span>
        </p>
      )}
      {detail.steps.length > 0 && (
        <ol className="list-decimal space-y-1 pl-5">
          {detail.steps.map((step, i) => (
            <li key={i}>{step}</li>
          ))}
        </ol>
      )}
      {(files.windows || files.macos || files.all) && (
        <div className="space-y-1 text-xs text-muted-foreground">
          {files.all && <p>Tệp cấu hình: <code className="break-all">{files.all}</code></p>}
          {files.windows && <p>Windows: <code className="break-all">{files.windows}</code></p>}
          {files.macos && <p>macOS: <code className="break-all">{files.macos}</code></p>}
        </div>
      )}
      <div className="space-y-1">
        <p className="font-medium">{detail.format === 'shell' ? 'Câu lệnh chạy trong cửa sổ dòng lệnh' : 'Đoạn cấu hình dán vào tệp'}</p>
        <div className="flex items-start gap-2">
          <pre className="max-h-56 min-w-0 flex-1 overflow-auto rounded bg-muted p-2 text-xs">{filled}</pre>
          <CopyButton value={filled} label="đoạn cấu hình" />
        </div>
        <p className="text-xs text-muted-foreground">
          {revealed
            ? `Đã điền sẵn khóa ${revealed.label} bạn vừa lấy ở bước 2.`
            : `Thay ${detail.placeholder || 'chỗ giữ khóa'} bằng khóa của bạn ở bước 2 — hoặc lấy khóa trước, đoạn này tự điền.`}
        </p>
      </div>
      {detail.note && <p className="text-xs text-muted-foreground">{detail.note}</p>}
    </div>
  )
}

// ---------------------------------------------------------------------------------------------------------------------
// Bước 2 — khóa của tôi: khóa chờ nhận (quản trị phát hộ), khóa đang có, tạo khóa mới
// ---------------------------------------------------------------------------------------------------------------------

function KeysStep({ revealed, onReveal }: { revealed: RevealedKey | null; onReveal: (key: RevealedKey) => void }) {
  const mine = useMyKeys()
  const pending = usePendingKeys()
  const create = useCreateMyKey()
  const claim = useClaimKey()
  const remove = useRemoveMyKey()
  const [name, setName] = useState('')
  const [scope, setScope] = useState(0)

  const pendingItems = pending.data?.items ?? []
  //  Khóa chờ nhận đã có ở khối riêng phía trên — danh sách «khóa của bạn» chỉ bày khóa đã nhận / tự tạo.
  const myItems = (mine.data?.items ?? []).filter((k) => k.state !== KEY_STATE.pending)

  async function handleCreate() {
    try {
      const created = await create.mutateAsync({ name: name.trim(), scope, days: 90 })
      if (created.key) onReveal({ id: created.id, key: created.key, label: created.name || created.hint })
      setName('')
    } catch {
      //  Toast lỗi tự động (vd đã đủ số khóa tối đa).
    }
  }

  async function handleClaim(key: MyMcpKey) {
    try {
      const claimed = await claim.mutateAsync(key.id)
      if (claimed.key) onReveal({ id: claimed.id, key: claimed.key, label: claimed.name || claimed.hint })
    } catch {
      //  404: đã nhận rồi / bị thu hồi / hết hạn — toast tự động.
    }
  }

  async function handleRemove(key: MyMcpKey) {
    const ok = await confirm({
      title: 'Gỡ khóa kết nối',
      message: `Gỡ khóa "${key.name || key.hint}"? Ứng dụng AI đang dùng khóa này sẽ không tra được ERP nữa.`,
      confirmLabel: 'Gỡ khóa',
    })
    if (ok) remove.mutate(key.id)
  }

  return (
    <Card>
      <CardHeader>
        <StepHeading step={2} title="Khóa của bạn" />
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {revealed && (
          <div className="space-y-2 rounded-md border border-primary/40 p-3">
            <p className="font-medium">Khóa {revealed.label} — chỉ hiện một lần, chép ngay:</p>
            <div className="flex items-center gap-2">
              <code className="break-all rounded bg-muted px-1.5 py-0.5 text-xs">{revealed.key}</code>
              <CopyButton value={revealed.key} label="khóa kết nối" />
            </div>
            <p className="text-xs text-muted-foreground">Đoạn cấu hình ở bước 1 đã điền sẵn khóa này.</p>
          </div>
        )}

        {pendingItems.length > 0 && (
          <div className="space-y-2">
            <p className="font-medium">Khóa quản trị phát cho bạn, chờ nhận</p>
            <ul className="divide-y rounded-md border">
              {pendingItems.map((k) => (
                <li key={k.id} className="flex flex-wrap items-center gap-3 px-3 py-2">
                  <span className="min-w-0 flex-1">
                    {k.name || 'Khóa kết nối'} <span className="text-xs text-muted-foreground">· {k.scope_label} · hết hạn {formatDateTime(k.expires_at)}</span>
                  </span>
                  <Button type="button" size="sm" onClick={() => void handleClaim(k)} disabled={claim.isPending}>
                    Nhận khóa
                  </Button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {mine.isLoading ? (
          <Skeleton className="h-10 w-full" />
        ) : myItems.length > 0 ? (
          <ul className="divide-y rounded-md border">
            {myItems.map((k) => (
              <li key={k.id} className="flex flex-wrap items-center gap-3 px-3 py-2">
                <span className="min-w-0 flex-1 font-medium">
                  {k.name || 'Khóa kết nối'} <span className="font-mono text-xs text-muted-foreground">{k.hint}</span>
                </span>
                <KeyStateBadge state={k.state} label={k.state_label} />
                <span className="text-xs text-muted-foreground">
                  {k.scope_label} · hết hạn {formatDateTime(k.expires_at)}
                  {k.last_used_at ? ` · dùng lần cuối ${formatDateTime(k.last_used_at)}` : ' · chưa dùng'}
                </span>
                {LIVE_STATES.includes(k.state) && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    aria-label={`Gỡ khóa ${k.name || k.hint}`}
                    onClick={() => void handleRemove(k)}
                    disabled={remove.isPending}
                  >
                    <Trash2 className="mr-1 size-4" /> Gỡ
                  </Button>
                )}
              </li>
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
          thanh toán vẫn chỉ tạo trên web. Khóa hạn 90 ngày.
        </p>
      </CardContent>
    </Card>
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
