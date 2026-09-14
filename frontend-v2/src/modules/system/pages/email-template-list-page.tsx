import { Pencil } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Switch } from '@/shared/ui/switch'
import { cn } from '@/shared/utils/cn'

import { useEmailTemplates, useSaveEmailTemplate } from '../hooks/use-email-templates'
import type { EmailTemplate } from '../types/email-template'

//  Lưới CỘT dùng chung cho hàng tiêu đề và mọi dòng → các cột thẳng hàng và giãn
//  đều theo tỉ lệ (fr) thay vì để "Tiêu đề" nuốt hết chỗ, chừa khoảng trống lớn.
const ROW_GRID =
  'grid grid-cols-[minmax(9rem,1.2fr)_minmax(14rem,2.4fr)_minmax(8rem,1.1fr)_5rem_8rem] items-center gap-4'

/**
 * MẪU EMAIL THÔNG BÁO theo BƯỚC — trang riêng của phân hệ Quản trị.
 *
 * ⚠️ **Tách khỏi Cấu hình hệ thống ngày 14/09/2026** (duoc-CR-397). Trước đó nó
 * là một khối nằm giữa trang Cấu hình, dưới ba nhóm ô nhập và trên khối Loại trừ
 * email — cả trang cuộn một mạch hơn ba màn hình. Nó không cùng họ với phần còn
 * lại: mấy ô kia là thông số kỹ thuật gõ một lần rồi thôi (SMTP host, bucket),
 * còn đây là NỘI DUNG soạn thảo, sửa đi sửa lại, và mỗi mẫu lại mở tiếp một
 * trang con.
 *
 * ⚠️ **KHÔNG có nút Lưu chung.** Công tắc email lưu NGAY lúc gạt (mỗi dòng một
 * lần gọi), còn nội dung thì lưu ở trang con. Đó cũng là lý do tách được sạch:
 * khối này chưa bao giờ dùng nút *Lưu cấu hình* của trang Cấu hình.
 *
 * Người NHẬN là luật nghiệp vụ ở backend (theo vai trò), KHÔNG sửa ở đây. Công
 * tắc chỉ chi phối email; chuông trong ứng dụng vẫn gửi.
 */
export function EmailTemplateListPage() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const canWrite = can('setting', 'write')
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
    <PageContainer>
      <PageHeader
        title="Mẫu email thông báo"
        //  ⚠️ KHÔNG ghi "của phân hệ Đặt xe" — câu đó đi theo từ hồi khối này còn
        //  nằm trong Cấu hình và nay đã sai: danh sách có cả bước của Duyệt dấu
        //  (YCĐD). Backend quyết định có bao nhiêu bước, màn này chỉ vẽ theo.
        description="Bật/tắt email cho từng bước của các luồng duyệt và sửa nội dung HTML. Người nhận do hệ thống quyết định theo vai trò — không đặt tại đây. Chuông trong ứng dụng vẫn gửi kể cả khi tắt email."
      />

      {!canWrite && (
        <p className="mb-4 rounded-lg bg-accent px-3 py-2 text-[13px] text-muted-foreground">
          Bạn chỉ có quyền xem. Liên hệ Quản trị hệ thống nếu cần thay đổi.
        </p>
      )}

      <Card className="p-4">
        {isPending ? (
          <div className="py-6 text-center text-sm text-muted-foreground">Đang tải mẫu email…</div>
        ) : (
          <div className="divide-y">
            <div
              className={cn(
                ROW_GRID,
                'pb-2 text-[11px] font-semibold tracking-wider text-muted-foreground uppercase',
              )}
            >
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
      </Card>
    </PageContainer>
  )
}
