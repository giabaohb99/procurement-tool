import { CalendarDays, KeyRound, Plug, Trash2 } from 'lucide-react'
import { useState } from 'react'

import {
  useAiKey,
  useCreateMcpKey,
  useDisconnectGoogle,
  useGoogleAuthorize,
  useGoogleLink,
  useMcpKeys,
  useRemoveAiKey,
  useRemoveMcpKey,
  useSetAiKey,
} from '@/modules/system/hooks/use-ai-key'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { SectionHeading } from '@/shared/ui/section-heading'
import { CopyButton } from '@/shared/ui/copy-button'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDateTime } from '@/shared/utils/format-date'

/**
 * Tab «Khóa AI» ở Trang cá nhân (ai-CR-053, D-01) — khóa Gemini CÁ NHÂN cho bot Telegram / Zalo.
 *
 * Dán ở đây, KHÔNG dán vào chat: Telegram giữ lịch sử vĩnh viễn, khóa nằm trong chat là khóa đã lộ.
 * Backend kiểm khóa với Gemini rồi lưu mã hóa; không cửa nào trả khóa ra, kể cả cho chính chủ —
 * chỉ 4 ký tự cuối. Ô nhập là `type="password"` và xóa trắng ngay sau khi lưu.
 * Khóa của Trợ lý trên web là khóa công ty, cấu hình ở Quản trị; hai khóa không dùng chung.
 */
export function ProfileAiKeyTab() {
  const { data, isLoading } = useAiKey()
  const setKey = useSetAiKey()
  const remove = useRemoveAiKey()
  const [draft, setDraft] = useState('')

  async function handleSave() {
    const key = draft.trim()
    if (!key) return
    await setKey.mutateAsync(key).then(() => setDraft(''), () => undefined)
  }

  async function handleRemove() {
    const ok = await confirm({
      title: 'Gỡ khóa Gemini',
      message: 'Gỡ khóa này? Bot Telegram sẽ không trả lời câu hỏi AI cho bạn nữa cho tới khi dán khóa khác.',
      confirmLabel: 'Gỡ khóa',
    })
    if (ok) remove.mutate()
  }

  return (
    <div className="space-y-4">
      <GoogleCard />
      <McpKeysCard />
      <Card>
        <CardHeader>
          <SectionHeading>Khóa AI của bạn cho bot Telegram</SectionHeading>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p className="text-muted-foreground">
            Mọi câu hỏi bạn gửi bot Telegram (và Zalo sau này) chạy bằng khóa Gemini của chính bạn, chi phí tính
            theo khóa đó. Lấy khóa ở{' '}
            <a className="font-medium text-primary hover:underline" href="https://aistudio.google.com/apikey" target="_blank" rel="noreferrer">
              Google AI Studio
            </a>
            . Chỉ dán ở đây, không bao giờ gửi khóa vào khung chat. Khóa của Trợ lý trên web là khóa công ty, không dùng chung.
          </p>
          {isLoading && <Skeleton className="h-10 w-full" />}
          {!isLoading && data?.has_key && (
            <div className="flex flex-wrap items-center gap-3 rounded-md border p-3">
              <span className="min-w-0 flex-1">
                Đang dùng khóa <span className="font-mono">{data.hint}</span>
                {data.verified_at && <span className="text-muted-foreground"> · kiểm lúc {formatDateTime(data.verified_at)}</span>}
              </span>
              <Button type="button" variant="ghost" size="sm" onClick={() => void handleRemove()} disabled={remove.isPending}>
                <Trash2 className="mr-1 size-4" /> Gỡ khóa
              </Button>
            </div>
          )}
          {!isLoading && data && !data.has_key && (
            <p className="rounded-md border border-dashed p-3 text-muted-foreground">
              Chưa có khóa. Bot vẫn cho đăng nhập, xem tình trạng việc, nhưng chưa trả lời câu hỏi AI.
            </p>
          )}
          <div className="space-y-1.5">
            <Label htmlFor="ai-key-input">{data?.has_key ? 'Dán khóa mới để thay' : 'Dán khóa Gemini'}</Label>
            <div className="flex gap-2">
              <Input
                id="ai-key-input"
                type="password"
                autoComplete="off"
                spellCheck={false}
                placeholder="AIza…"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
              />
              <Button type="button" size="sm" onClick={() => void handleSave()} disabled={!draft.trim() || setKey.isPending}>
                <KeyRound className="mr-1.5 size-4" /> {setKey.isPending ? 'Đang kiểm…' : 'Lưu khóa'}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">Hệ thống gọi thử Gemini một lượt không tốn token để chắc khóa dùng được rồi mới lưu (đã mã hóa).</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}


/**
 * Kết nối MCP (ai-CR-063, M-01/M-02): mỗi người tự tạo khóa để ứng dụng AI của mình (Claude Desktop, Cursor…)
 * gọi bộ tool ERP dưới đúng quyền của mình. Khóa chỉ hiện MỘT lần lúc tạo; mặc định «chỉ đọc», 90 ngày.
 */
function McpKeysCard() {
  const { data, isLoading } = useMcpKeys()
  const create = useCreateMcpKey()
  const remove = useRemoveMcpKey()
  const [name, setName] = useState('')
  const [scope, setScope] = useState(0)
  const issued = create.data
  const endpoint = data?.endpoint || `${window.location.origin}/api/mcp`
  const snippet = issued
    ? JSON.stringify({ mcpServers: { 'dego-erp': { url: endpoint, headers: { Authorization: `Bearer ${issued.key}` } } } }, null, 2)
    : ''

  async function handleRemove(id: number, label: string) {
    const ok = await confirm({
      title: 'Gỡ khóa MCP',
      message: `Gỡ khóa «${label}»? Ứng dụng đang dùng khóa này sẽ không gọi được ERP nữa.`,
      confirmLabel: 'Gỡ khóa',
    })
    if (ok) remove.mutate(id)
  }

  return (
    <Card>
      <CardHeader>
        <SectionHeading>Kết nối MCP: dùng AI của bạn với dữ liệu ERP</SectionHeading>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <p className="text-muted-foreground">
          Tạo một khóa, dán vào Claude Desktop / Cursor / ứng dụng hỗ trợ MCP. Ứng dụng đó sẽ tra cứu ERP <b>đúng quyền của bạn</b>.
          Khóa «được ghi» thêm khả năng soạn nháp và tạo phiếu (luôn hỏi bạn xác nhận bản nháp trước). Đề nghị thanh toán chỉ tạo trên web.
        </p>
        <div className="flex flex-wrap items-end gap-2">
          <div className="space-y-1">
            <Label htmlFor="mcp-key-name">Tên khóa</Label>
            <Input id="mcp-key-name" className="w-48" placeholder="Claude Desktop máy công ty" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="mcp-key-scope">Mức</Label>
            <select id="mcp-key-scope" className="h-9 rounded-md border bg-background px-2 text-sm" value={scope} onChange={(e) => setScope(Number(e.target.value))}>
              <option value={0}>Chỉ đọc</option>
              <option value={1}>Được ghi</option>
            </select>
          </div>
          <Button type="button" size="sm" onClick={() => create.mutate({ name, scope, days: 90 })} disabled={create.isPending}>
            <Plug className="mr-1.5 size-4" /> Tạo khóa MCP
          </Button>
        </div>
        {issued?.key && (
          <div className="space-y-2 rounded-md border p-3">
            <p className="font-medium">Khóa mới (chỉ hiện một lần, chép ngay):</p>
            <div className="flex items-center gap-2">
              <code className="break-all rounded bg-muted px-1.5 py-0.5 text-xs">{issued.key}</code>
              <CopyButton value={issued.key} label="khóa MCP" />
            </div>
            <p className="text-muted-foreground">Cấu hình cho Claude Desktop / Cursor (mục mcpServers):</p>
            <div className="flex items-start gap-2">
              <pre className="max-h-40 flex-1 overflow-auto rounded bg-muted p-2 text-xs">{snippet}</pre>
              <CopyButton value={snippet} label="cấu hình MCP" />
            </div>
          </div>
        )}
        {isLoading && <Skeleton className="h-10 w-full" />}
        {!isLoading && (data?.items.length ?? 0) > 0 && (
          <ul className="divide-y rounded-md border">
            {data!.items.map((k) => (
              <li key={k.id} className="flex flex-wrap items-center gap-3 px-3 py-2">
                <span className="min-w-0 flex-1 font-medium">{k.name} <span className="font-mono text-xs text-muted-foreground">{k.hint}</span></span>
                <span className="text-xs text-muted-foreground">{k.scope_label} · hết hạn {formatDateTime(k.expires_at)}{k.last_used_at ? ` · dùng lần cuối ${formatDateTime(k.last_used_at)}` : ' · chưa dùng'}</span>
                <Button type="button" variant="ghost" size="sm" onClick={() => void handleRemove(k.id, k.name)} disabled={remove.isPending}>
                  <Trash2 className="mr-1 size-4" /> Gỡ
                </Button>
              </li>
            ))}
          </ul>
        )}
        {!isLoading && (data?.items.length ?? 0) === 0 && <p className="text-muted-foreground">Chưa có khóa MCP nào.</p>}
        <p className="text-xs text-muted-foreground">Đường kết nối: <code>{endpoint}</code>. Hướng dẫn: Trung tâm HDSD → «Kết nối MCP».</p>
      </CardContent>
    </Card>
  )
}


/**
 * Google CÁ NHÂN (ai-CR-064, M-06): nối một lần qua màn đồng ý của Google; ERP giữ token mã hóa. Bot / Trợ lý / MCP
 * đọc lịch và Drive của CHÍNH bạn (tool my_calendar_events, create_calendar_event, drive_search, drive_read),
 * bản tin sáng 7h30 và nhắc trước họp 15 phút về Telegram.
 */
function GoogleCard() {
  const { data, isLoading } = useGoogleLink()
  const authorize = useGoogleAuthorize()
  const disconnect = useDisconnectGoogle()

  async function handleDisconnect() {
    const ok = await confirm({
      title: 'Gỡ kết nối Google',
      message: 'Bot sẽ không đọc được lịch và Drive của bạn nữa; nối lại bất cứ lúc nào.',
      confirmLabel: 'Gỡ kết nối',
    })
    if (ok) disconnect.mutate()
  }

  return (
    <Card>
      <CardHeader>
        <SectionHeading>Google của bạn: Lịch và Drive</SectionHeading>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <p className="text-muted-foreground">
          Nối tài khoản Google cá nhân để hỏi bot «hôm nay tôi họp gì», «đặt lịch họp NCC X 14h mai», «tìm trên Drive hợp đồng ABC»,
          nhận bản tin sáng 7h30 và nhắc trước họp 15 phút qua Telegram. Bot chỉ thấy lịch và tệp của chính bạn.
        </p>
        {isLoading && <Skeleton className="h-10 w-full" />}
        {!isLoading && data && !data.configured && (
          <p className="rounded-md border border-dashed p-3 text-muted-foreground">Hệ thống chưa cấu hình kết nối Google (quản trị khai GOOGLE_CLIENT_SECRET).</p>
        )}
        {!isLoading && data?.configured && data.linked && (
          <div className="flex flex-wrap items-center gap-3 rounded-md border p-3">
            <span className="min-w-0 flex-1">
              Đang nối <span className="font-medium">{data.email || 'Google'}</span>
              {data.linked_at && <span className="text-muted-foreground"> · từ {formatDateTime(data.linked_at)}</span>}
            </span>
            <Button type="button" variant="ghost" size="sm" onClick={() => void handleDisconnect()} disabled={disconnect.isPending}>
              <Trash2 className="mr-1 size-4" /> Gỡ kết nối
            </Button>
          </div>
        )}
        {!isLoading && data?.configured && !data.linked && (
          <Button type="button" size="sm" onClick={() => authorize.mutate()} disabled={authorize.isPending}>
            <CalendarDays className="mr-1.5 size-4" /> Nối Google
          </Button>
        )}
        <p className="text-xs text-muted-foreground">
          Google có thể hiện màn «ứng dụng chưa được xác minh»: bấm Nâng cao → Tiếp tục. Đây là ứng dụng nội bộ của công ty.
        </p>
      </CardContent>
    </Card>
  )
}
