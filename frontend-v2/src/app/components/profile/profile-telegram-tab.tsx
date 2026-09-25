import { KeyRound, RotateCw, Send, Unlink } from 'lucide-react'

import type { TelegramLink } from '@/modules/system/api/agent-hub-api'
import {
  useCreateTelegramLinkCode,
  useRemoveTelegramLink,
  useTelegramLinks,
} from '@/modules/system/hooks/use-telegram-links'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { CopyButton } from '@/shared/ui/copy-button'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDateTime } from '@/shared/utils/format-date'

/**
 * Tab «Telegram» ở Trang cá nhân (ai-CR-038) — tự đăng nhập tài khoản ERP trong bot Telegram.
 *
 * Lấy mã 6 số dùng một lần (sống vài phút) rồi nhắn `/dangnhap <mã>` cho bot. KHÔNG bao giờ gõ
 * mật khẩu vào khung chat: Telegram giữ lịch sử vĩnh viễn. Trong Telegram chỉ hỏi được Trợ lý AI,
 * theo đúng quyền của tài khoản này. Cửa API chỉ đòi đăng nhập — ai cũng tự nối được Telegram
 * của chính mình, như tự đá thiết bị lạ ở «Thiết bị của tôi».
 */
export function ProfileTelegramTab() {
  const { data, isLoading, refetch } = useTelegramLinks()
  const createCode = useCreateTelegramLinkCode()
  const remove = useRemoveTelegramLink()
  const issued = createCode.data
  const links = data?.items ?? []

  async function handleRemove(link: TelegramLink) {
    const ok = await confirm({
      title: 'Gỡ liên kết Telegram',
      message: `Gỡ liên kết với chat ${link.tg_name || link.chat}? Chat đó sẽ không hỏi được Trợ lý dưới tài khoản này nữa.`,
      confirmLabel: 'Gỡ liên kết',
    })
    if (ok) remove.mutate(link.id)
  }

  if (!isLoading && data && !data.enabled) {
    return (
      <Card>
        <CardContent className="py-8 text-sm text-muted-foreground">Liên kết Telegram đang tắt trên hệ thống này.</CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <SectionHeading>Đăng nhập ERP trong bot Telegram</SectionHeading>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p className="text-muted-foreground">
            Lấy mã rồi nhắn <code className="rounded bg-muted px-1">/dangnhap &lt;mã&gt;</code> cho bot trong chat riêng.
            Mã dùng một lần, hết hạn sau vài phút. Không bao giờ gõ mật khẩu vào Telegram.
          </p>
          <Button type="button" size="sm" onClick={() => createCode.mutate()} disabled={createCode.isPending}>
            <KeyRound className="mr-1.5 size-4" /> {issued ? 'Lấy mã khác' : 'Lấy mã liên kết'}
          </Button>
          {issued && (
            <div className="space-y-2 rounded-md border p-3">
              <div className="flex items-center gap-2">
                <span className="font-mono text-2xl font-semibold tracking-widest">{issued.code}</span>
                <CopyButton value={`/dangnhap ${issued.code}`} label="lệnh đăng nhập" />
              </div>
              <p className="text-muted-foreground">Hết hạn lúc {formatDateTime(issued.expires_at)}.</p>
              {issued.deep_link && (
                <a
                  className="inline-flex items-center gap-1.5 font-medium text-primary hover:underline"
                  href={issued.deep_link}
                  target="_blank"
                  rel="noreferrer"
                >
                  <Send className="size-4" /> Mở bot và đăng nhập luôn
                </a>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <SectionHeading>Chat đang đăng nhập tài khoản này</SectionHeading>
            <Button type="button" variant="outline" size="sm" onClick={() => refetch()} title="Làm mới">
              <RotateCw className="size-4" />
              <span className="sr-only">Làm mới</span>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading && <Skeleton className="h-12 w-full" />}
          {!isLoading && links.length === 0 && (
            <p className="py-4 text-sm text-muted-foreground">Chưa có chat Telegram nào đăng nhập tài khoản này.</p>
          )}
          {links.length > 0 && (
            <ul className="divide-y rounded-md border text-sm">
              {links.map((link) => (
                <li key={link.id} className="flex flex-wrap items-center gap-3 px-3 py-2.5">
                  <span className="min-w-0 flex-1 font-medium">{link.tg_name || 'Telegram'} <span className="font-mono text-xs text-muted-foreground">{link.chat}</span></span>
                  <span className="text-xs text-muted-foreground">Từ {formatDateTime(link.linked_at)} · hết hạn {formatDateTime(link.expires_at)}</span>
                  <Button type="button" variant="ghost" size="sm" onClick={() => void handleRemove(link)} disabled={remove.isPending}>
                    <Unlink className="mr-1 size-4" /> Gỡ
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
