import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Bell, KeyRound, Loader2, Mail, MailX } from 'lucide-react'
import { toast } from 'sonner'

import { authService } from '@/core/auth/auth-service'
import { queryKeys } from '@/shared/constants/query-keys'
import { Button } from '@/shared/ui/button'
import { FormCard } from '@/shared/ui/form-card'
import { cn } from '@/shared/utils/cn'

/**
 * Bật/tắt EMAIL thông báo luồng duyệt cho chính tài khoản đang đăng nhập (bao-CR-349).
 *
 * Đặt cạnh khối "Tài khoản" chứ không nằm trong tab Thông báo: dòng Email ở ngay
 * trên, và người muốn ngưng nhận thư đi tìm nơi nào nói về hộp thư của họ.
 *
 * Tắt rồi thì việc cần duyệt chỉ còn thấy ở chuông trong app — phải nói thẳng điều
 * đó ra, chứ không ai tự suy được từ nhãn nút.
 */
export function EmailNotificationCard({ value }: { value?: boolean }) {
  const queryClient = useQueryClient()
  // Chưa có trường (hệ chưa chạy migration) = vẫn đang nhận, đúng chiều mặc định
  // của cột `tab_user.notify_email`.
  const on = value !== false

  const toggle = useMutation({
    mutationFn: (next: boolean) => authService.setNotifyEmail(next),
    onSuccess: (_data, next) => {
      toast.success(next ? 'Đã bật email thông báo' : 'Đã tắt email thông báo')
      // Hồ sơ `/api/auth/me` là nguồn duy nhất của công tắc này — nạp lại để cả
      // trang (và `useAuth().user`) cùng đổi, khỏi giữ thêm một bản state riêng.
      void queryClient.invalidateQueries({ queryKey: queryKeys.auth.me() })
    },
  })

  return (
    <FormCard title="Email thông báo" icon={Mail} iconClassName="text-muted-foreground">
      <div className="flex flex-wrap items-center justify-between gap-3 py-1">
        <div className="flex items-center gap-2 text-sm">
          <span
            className={cn(
              'size-2 shrink-0 rounded-full',
              on ? 'bg-emerald-500' : 'bg-muted-foreground/40',
            )}
          />
          <span className="font-medium text-navy dark:text-foreground">
            {on ? 'Đang bật' : 'Đang tắt'}
          </span>
        </div>

        <Button
          variant="outline"
          size="sm"
          disabled={toggle.isPending}
          onClick={() => toggle.mutate(!on)}
        >
          {toggle.isPending ? <Loader2 className="animate-spin" /> : on ? <MailX /> : <Mail />}
          {on ? 'Tắt email thông báo' : 'Bật email thông báo'}
        </Button>
      </div>

      <p className="text-[13px] leading-relaxed text-muted-foreground">
        Thư báo về hộp thư của bạn mỗi khi có chứng từ cần duyệt, được duyệt hoặc bị trả
        lại. Cài đặt này áp cho tài khoản, không phụ thuộc thiết bị.
      </p>

      <p className="mt-2 flex gap-2 rounded-lg bg-accent px-3 py-2 text-xs text-muted-foreground">
        <Bell className="mt-0.5 size-3.5 shrink-0" />
        <span>
          Tắt email <b>không</b> tắt thông báo: chuông trong app vẫn ghi đủ. Nhưng nếu bạn
          là người duyệt thì từ lúc tắt, chỉ mở app mới biết có việc chờ ký.
        </span>
      </p>

      {/*  `mt-2` khớp ô nhắc ở trên. `CardContent` của `FormCard` không khai
           `space-y-*`, nên thiếu lề ở đây là hai ô cùng nền `bg-accent` dính
           liền thành MỘT cục, chỉ cách nhau đúng một vạch bo góc — đọc ra như
           một đoạn bị lỗi xuống dòng chứ không ra hai lời nhắc riêng. */}
      <p className="mt-2 flex gap-2 rounded-lg bg-accent px-3 py-2 text-xs text-muted-foreground">
        <KeyRound className="mt-0.5 size-3.5 shrink-0" />
        <span>Thư đặt lại mật khẩu và thư cấp tài khoản vẫn gửi bình thường.</span>
      </p>
    </FormCard>
  )
}
