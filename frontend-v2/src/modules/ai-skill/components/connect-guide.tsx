import { Copy, Download, Globe, MonitorSmartphone, Plug, SquareTerminal } from 'lucide-react'
import { useRef, useState, type ReactNode } from 'react'
import { toast } from 'sonner'

import { Button } from '@/shared/ui/button'
import { CopyButton } from '@/shared/ui/copy-button'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { fillKeyInSnippet } from '../config/ai-skill-constants'
import { usePublicSetup, usePublicSetupClients, useSetup, useSetupClients } from '../hooks/use-my-ai'
import type { McpSetupDetail } from '../types/ai-skill'

const CLIENT_ICONS: Record<string, typeof Plug> = {
  claude_desktop: MonitorSmartphone,
  claude_code: SquareTerminal,
  cursor: SquareTerminal,
  gemini_cli: SquareTerminal,
  claude_ai: Globe,
  chatgpt: Globe,
}

/** Khóa sẽ điền vào đoạn cấu hình (chỉ màn AI của tôi có). */
export interface ConnectKeySlot {
  /** Tên khóa đang chọn; rỗng = chưa chọn khóa nào. */
  label: string
  /** Khóa thô đã có trong bộ nhớ của màn (vừa tạo / vừa nhận / vừa bấm Hiện); null = chưa có. */
  value: string | null
  /** Lấy khóa thô lúc bấm Sao chép (gọi xem lại khóa); không có, hoặc trả null, thì chép đoạn còn chỗ giữ khóa. */
  obtain?: () => Promise<string | null>
}

interface ConnectGuideProps {
  /** `private` = đã đăng nhập (`mcp-setup`), `public` = trang /connect-ai (`mcp-setup/public`). */
  source: 'private' | 'public'
  keySlot?: ConnectKeySlot | null
  initialClient?: string
  footer?: ReactNode
  className?: string
}

/**
 * Hướng dẫn nối AI riêng theo từng ứng dụng (bao-CR-638) — DÙNG CHUNG cho ba chỗ: bước 1 màn AI của tôi (có khóa thật của
 * dòng đang chọn), cột phải màn Khóa nhân sự và trang công khai /connect-ai (hai chỗ sau KHÔNG BAO GIỜ có khóa: đoạn cấu
 * hình giữ nguyên chỗ giữ `<KHÓA_CỦA_BẠN>`). Ứng dụng nối bằng OAuth (ChatGPT, claude.ai) chỉ cần địa chỉ cổng.
 */
export function ConnectGuide({ source, keySlot = null, initialClient = '', footer, className }: ConnectGuideProps) {
  const isPublic = source === 'public'
  const privateClients = useSetupClients(!isPublic)
  const publicClients = usePublicSetupClients(isPublic)
  const list = isPublic ? publicClients : privateClients
  const clients = list.data?.clients ?? []
  const [chosen, setChosen] = useState(initialClient)
  const client =
    (clients.some((c) => c.client === chosen) ? chosen : '') ||
    clients.find((c) => c.supported)?.client ||
    clients[0]?.client ||
    ''
  const privateDetail = useSetup(client, !isPublic)
  const publicDetail = usePublicSetup(client, isPublic)
  const detail = isPublic ? publicDetail : privateDetail

  return (
    <div className={cn('space-y-4 text-sm', className)}>
      {list.isLoading ? (
        <Skeleton className="h-10 w-full" />
      ) : list.isError ? (
        <p className="text-muted-foreground">Chưa tải được danh sách ứng dụng AI. Thử lại sau ít phút.</p>
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
      {detail.isLoading && client && <Skeleton className="h-32 w-full" />}
      {detail.data && <GuideDetail detail={detail.data} keySlot={keySlot} />}
      {footer}
    </div>
  )
}

function GuideDetail({ detail, keySlot }: { detail: McpSetupDetail; keySlot: ConnectKeySlot | null }) {
  if (!detail.supported) {
    return (
      <p className="rounded-md border border-dashed p-3 text-muted-foreground">
        {detail.note || `${detail.label} chưa nối được với ERP. Hãy dùng một ứng dụng khác trong danh sách.`}
      </p>
    )
  }
  if (detail.auth === 'oauth' || detail.format === 'url') return <OAuthGuide detail={detail} />
  const files = detail.files ?? {}
  return (
    <div className="space-y-3">
      {(detail.requires ?? []).length > 0 && (
        <p className="flex items-start gap-2 text-muted-foreground">
          <Download className="mt-0.5 size-4 shrink-0" />
          <span>Cần cài trước: {(detail.requires ?? []).join(', ')}</span>
        </p>
      )}
      <Steps steps={detail.steps} />
      {(files.windows || files.macos || files.all) && (
        <div className="space-y-1 text-xs text-muted-foreground">
          {files.all && (
            <p>
              Tệp cấu hình: <code className="break-all">{files.all}</code>
            </p>
          )}
          {files.windows && (
            <p>
              Windows: <code className="break-all">{files.windows}</code>
            </p>
          )}
          {files.macos && (
            <p>
              macOS: <code className="break-all">{files.macos}</code>
            </p>
          )}
        </div>
      )}
      <SnippetBlock detail={detail} keySlot={keySlot} />
      {detail.note && <p className="text-xs text-muted-foreground">{detail.note}</p>}
    </div>
  )
}

function Steps({ steps }: { steps: string[] }) {
  if (steps.length === 0) return null
  return (
    <ol className="list-decimal space-y-1 pl-5">
      {steps.map((step, i) => (
        <li key={i}>{step}</li>
      ))}
    </ol>
  )
}

/**
 * Đoạn cấu hình + nút Sao chép. Khóa thật chỉ HIỆN trong đoạn khi màn đã có nó trong bộ nhớ (người dùng vừa tạo / nhận /
 * bấm Hiện); chưa có thì đoạn hiện chỗ giữ khóa, và bấm Sao chép mới xin khóa (một lượt xem lại) rồi chép bản đã điền.
 */
function SnippetBlock({ detail, keySlot }: { detail: McpSetupDetail; keySlot: ConnectKeySlot | null }) {
  const busy = useRef(false)
  const [copying, setCopying] = useState(false)
  const shown = fillKeyInSnippet(detail.snippet, detail.placeholder, keySlot?.value)
  const placeholder = detail.placeholder || 'chỗ giữ khóa'

  async function copySnippet() {
    if (busy.current) return
    busy.current = true
    setCopying(true)
    try {
      let key = keySlot?.value ?? null
      if (!key && keySlot?.label && keySlot.obtain) key = await keySlot.obtain()
      if (!navigator.clipboard) throw new Error('clipboard unavailable')
      await navigator.clipboard.writeText(fillKeyInSnippet(detail.snippet, detail.placeholder, key))
      toast.success(key ? `Đã chép đoạn cấu hình, đã điền khóa ${keySlot?.label}.` : 'Đã chép đoạn cấu hình.')
    } catch {
      toast.error('Không chép được — bôi đen đoạn cấu hình rồi chép tay.')
    } finally {
      busy.current = false
      setCopying(false)
    }
  }

  let hint: string
  if (!keySlot) hint = `Thay ${placeholder} bằng khóa lấy ở Trang cá nhân → AI của tôi (đăng nhập ERP).`
  else if (!keySlot.label) hint = `Chọn một khóa ở bước 2, nút Sao chép sẽ điền khóa đó thay ${placeholder}.`
  else if (keySlot.value) hint = `Đã điền khóa ${keySlot.label}.`
  else if (keySlot.obtain) hint = `Bấm Sao chép đoạn cấu hình: khóa ${keySlot.label} được điền vào bản chép.`
  else hint = `Khóa ${keySlot.label} không xem lại được — tạo khóa mới ở bước 2 để điền tự động.`

  return (
    <div className="space-y-1">
      <p className="font-medium">
        {detail.format === 'shell' ? 'Câu lệnh chạy trong cửa sổ dòng lệnh' : 'Đoạn cấu hình dán vào tệp'}
      </p>
      <pre className="max-h-56 overflow-auto rounded bg-muted p-2 text-xs">{shown}</pre>
      <div className="flex flex-wrap items-center gap-2">
        <Button type="button" size="sm" variant="outline" onClick={() => void copySnippet()} disabled={copying}>
          <Copy className="size-4" />
          Sao chép đoạn cấu hình
        </Button>
        <span className="text-xs text-muted-foreground">{hint}</span>
      </div>
    </div>
  )
}

/** Ứng dụng nối bằng OAuth (ai-CR-218): chỉ cần địa chỉ cổng, ứng dụng tự mở trang ERP xin phép — không có khóa. */
function OAuthGuide({ detail }: { detail: McpSetupDetail }) {
  const url = detail.snippet || detail.endpoint
  return (
    <div className="space-y-3">
      <Steps steps={detail.steps} />
      <div className="space-y-1">
        <p className="font-medium">Địa chỉ kết nối</p>
        <div className="flex items-center gap-2">
          <code className="min-w-0 flex-1 rounded bg-muted p-2 text-xs break-all">{url}</code>
          <CopyButton value={url} label="địa chỉ kết nối" />
        </div>
        <p className="text-xs text-muted-foreground">
          Không cần khóa: {detail.label} sẽ mở trang ERP để bạn đăng nhập và bấm Cho phép. Kết nối hiện trong danh sách khóa
          với nhãn Kết nối OAuth, tắt hoặc gỡ ở đó khi không dùng nữa.
        </p>
      </div>
      {detail.note && <p className="text-xs text-muted-foreground">{detail.note}</p>}
    </div>
  )
}
