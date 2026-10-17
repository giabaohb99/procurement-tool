import { Plug, Trash2 } from 'lucide-react'
import { useState } from 'react'

import { useCreateMcpKey, useMcpKeys, useRemoveMcpKey } from '@/modules/system/hooks/use-ai-key'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { CopyButton } from '@/shared/ui/copy-button'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDateTime } from '@/shared/utils/format-date'

/**
 * Mục «Kết nối AI riêng» ở Trang cá nhân (P0 doc 21 §6.5 + §7.1) — tách từ khối «Nâng cao: dùng Claude Desktop /
 * Cursor… (MCP)» từng giấu cuối tab Khóa AI (ai-CR-063, ai-CR-101).
 *
 * Từ 17/10/2026 đây là ĐƯỜNG CHÍNH để nhân sự dùng AI với dữ liệu ERP: dùng gói AI của chính họ (Claude, ChatGPT,
 * Cursor…), tiền model do gói của họ trả. Viết cho nhân viên văn phòng — tiêu đề không dùng chữ MCP; tên kỹ thuật
 * chỉ xuất hiện ở dòng nhỏ cho người cài đặt. API giữ nguyên `/api/agent-hub/mcp-keys`.
 *
 * Khóa chỉ hiện MỘT lần lúc tạo; mặc định «chỉ đọc», hạn 90 ngày. Ứng dụng AI dùng khóa này tra ERP đúng quyền
 * của chủ khóa (cổng kiểm theo người, ai-CR-207).
 */
export function ProfileAiConnectSection() {
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
  const items = data?.items ?? []

  async function handleRemove(id: number, label: string) {
    const ok = await confirm({
      title: 'Gỡ khóa kết nối',
      message: `Gỡ khóa "${label}"? Ứng dụng AI đang dùng khóa này sẽ không tra được ERP nữa.`,
      confirmLabel: 'Gỡ khóa',
    })
    if (ok) remove.mutate(id)
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <SectionHeading>Dùng AI của chính bạn với dữ liệu ERP</SectionHeading>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p className="text-muted-foreground">
            Bạn đang dùng Claude, ChatGPT, Cursor hay một ứng dụng AI khác trên máy? Tạo một khóa ở đây rồi dán vào ứng
            dụng đó: AI của bạn sẽ tra cứu được phiếu, đơn hàng, công việc trong ERP, <b>đúng phạm vi quyền của bạn</b>.
            Tiền dùng AI tính vào gói của bạn, không tính vào ví của công ty.
          </p>
          <ol className="list-decimal space-y-1 pl-5 text-muted-foreground">
            <li>Đặt tên khóa theo máy hoặc ứng dụng (ví dụ Claude máy công ty) rồi bấm Tạo khóa.</li>
            <li>Chép ngay khóa và đoạn cấu hình hiện ra — khóa chỉ hiện một lần.</li>
            <li>Dán đoạn cấu hình vào phần cài đặt kết nối của ứng dụng AI, khởi động lại ứng dụng là dùng được.</li>
          </ol>
          <p className="text-muted-foreground">
            Mức <b>Chỉ đọc</b> là đủ cho tra cứu. Mức <b>Được ghi</b> cho AI soạn nháp và tạo phiếu (luôn hỏi bạn xác nhận
            bản nháp trước); đề nghị thanh toán vẫn chỉ tạo trên web.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <SectionHeading>Khóa kết nối của bạn</SectionHeading>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex flex-wrap items-end gap-2">
            <div className="space-y-1">
              <Label htmlFor="ai-connect-key-name">Tên khóa</Label>
              <Input
                id="ai-connect-key-name"
                className="w-56"
                placeholder="Claude máy công ty"
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
            <Button type="button" size="sm" onClick={() => create.mutate({ name, scope, days: 90 })} disabled={create.isPending}>
              <Plug className="mr-1.5 size-4" /> Tạo khóa
            </Button>
          </div>

          {issued?.key && (
            <div className="space-y-2 rounded-md border p-3">
              <p className="font-medium">Khóa mới — chỉ hiện một lần, chép ngay:</p>
              <div className="flex items-center gap-2">
                <code className="break-all rounded bg-muted px-1.5 py-0.5 text-xs">{issued.key}</code>
                <CopyButton value={issued.key} label="khóa kết nối" />
              </div>
              <p className="text-muted-foreground">Đoạn cấu hình dán vào ứng dụng AI (Claude Desktop, Cursor…):</p>
              <div className="flex items-start gap-2">
                <pre className="max-h-40 flex-1 overflow-auto rounded bg-muted p-2 text-xs">{snippet}</pre>
                <CopyButton value={snippet} label="đoạn cấu hình" />
              </div>
            </div>
          )}

          {isLoading && <Skeleton className="h-10 w-full" />}
          {!isLoading && items.length > 0 && (
            <ul className="divide-y rounded-md border">
              {items.map((k) => (
                <li key={k.id} className="flex flex-wrap items-center gap-3 px-3 py-2">
                  <span className="min-w-0 flex-1 font-medium">
                    {k.name} <span className="font-mono text-xs text-muted-foreground">{k.hint}</span>
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {k.scope_label} · hết hạn {formatDateTime(k.expires_at)}
                    {k.last_used_at ? ` · dùng lần cuối ${formatDateTime(k.last_used_at)}` : ' · chưa dùng'}
                  </span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    aria-label={`Gỡ khóa ${k.name}`}
                    onClick={() => void handleRemove(k.id, k.name)}
                    disabled={remove.isPending}
                  >
                    <Trash2 className="mr-1 size-4" /> Gỡ
                  </Button>
                </li>
              ))}
            </ul>
          )}
          {!isLoading && items.length === 0 && (
            <p className="text-muted-foreground">Chưa có khóa nào. Chưa dùng AI riêng thì không cần tạo.</p>
          )}
          <p className="text-xs text-muted-foreground">
            Cho người cài đặt: chuẩn kết nối MCP, đường kết nối <code>{endpoint}</code>. Hướng dẫn chi tiết: Trung tâm
            HDSD, mục Kết nối MCP.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
