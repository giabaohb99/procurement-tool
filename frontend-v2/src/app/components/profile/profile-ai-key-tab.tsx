import { KeyRound, Trash2 } from 'lucide-react'
import { useState } from 'react'

import { useAiKey, useRemoveAiKey, useSetAiKey } from '@/modules/system/hooks/use-ai-key'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { SectionHeading } from '@/shared/ui/section-heading'
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
      <Card>
        <CardHeader>
          <SectionHeading>Khóa Gemini của bạn cho bot Telegram</SectionHeading>
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
