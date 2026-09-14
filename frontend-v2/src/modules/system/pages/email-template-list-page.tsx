import { Mail, Pencil } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { FormCard } from '@/shared/ui/form-card'
import { Switch } from '@/shared/ui/switch'
import { cn } from '@/shared/utils/cn'

import { useEmailTemplates, useSaveEmailTemplate } from '../hooks/use-email-templates'
import type { EmailTemplate } from '../types/email-template'

//  Lưới CỘT dùng chung cho hàng tiêu đề và mọi dòng → các cột thẳng hàng và giãn
//  đều theo tỉ lệ (fr) thay vì để "Tiêu đề" nuốt hết chỗ, chừa khoảng trống lớn.
const ROW_GRID =
  'grid grid-cols-[minmax(9rem,1.2fr)_minmax(14rem,2.4fr)_minmax(8rem,1.1fr)_5rem_8rem] items-center gap-4'

/**
 * Mẫu email thông báo theo BƯỚC cho phân hệ Đặt xe — nằm trong Cấu hình hệ thống.
 *
 * Bật/tắt EMAIL từng bước ngay tại đây; **sửa nội dung mở TRANG CON**
 * (`/system/settings/email/:event`). Người NHẬN là luật nghiệp vụ ở backend (theo
 * vai trò), KHÔNG sửa ở đây. Công tắc chỉ chi phối email; chuông trong ứng dụng
 * vẫn gửi. Gác theo `setting.write` như cả trang Cấu hình.
 */
export function EmailTemplatePanel({ canWrite }: { canWrite: boolean }) {
  const navigate = useNavigate()
  const { data, isPending } = useEmailTemplates()
  const save = useSaveEmailTemplate()

  function toggle(t: EmailTemplate, enabled: boolean) {
    save.mutate(
      { event: t.event, enabled, subject: t.subject, body_html: t.body_html },
      {
        onSuccess: () => toast.success(enabled ? 'Đã bật email bước này' : 'Đã tắt email bước này'),
        onError: (error) => toast.error(extractErrorMessage(error)),
      },
    )
  }

  return (
    <FormCard
      title="Mẫu email thông báo theo bước (Đặt xe)"
      icon={Mail}
      iconClassName="text-muted-foreground"
    >
      <p className="mb-3 text-xs text-muted-foreground">
        Bật/tắt email cho từng bước và sửa nội dung HTML. Người nhận do hệ thống quyết định
        theo vai trò — không đặt tại đây. Chuông trong ứng dụng vẫn gửi kể cả khi tắt email.
      </p>

      {isPending ? (
        <div className="py-6 text-center text-sm text-muted-foreground">Đang tải mẫu email…</div>
      ) : (
        <div className="divide-y">
          <div className={cn(ROW_GRID, 'pb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground')}>
            <span>Tên bước</span>
            <span>Tiêu đề</span>
            <span>Người nhận</span>
            <span className="text-center">Email</span>
            <span />
          </div>
          {(data ?? []).map((t) => (
            <div key={t.event} className={cn(ROW_GRID, 'py-2.5')}>
              <div className="flex min-w-0 items-center gap-2">
                <span className="truncate text-sm font-medium">{t.label}</span>
                {t.is_custom && <Badge variant="secondary">Đã sửa</Badge>}
              </div>
              <div className="min-w-0 truncate text-sm text-muted-foreground">{t.subject}</div>
              <span className="truncate text-sm">{t.recipient}</span>
              <div className="flex justify-center">
                <Switch
                  checked={t.enabled}
                  disabled={!canWrite || save.isPending}
                  onCheckedChange={(v) => toggle(t, v)}
                  aria-label={`Bật email cho bước ${t.label}`}
                />
              </div>
              <Button
                className="w-full"
                variant="outline"
                size="sm"
                onClick={() => navigate(appRoutes.system.emailTemplate(t.event))}
              >
                <Pencil className="size-3.5" />
                {canWrite ? 'Sửa nội dung' : 'Xem nội dung'}
              </Button>
            </div>
          ))}
        </div>
      )}
    </FormCard>
  )
}
