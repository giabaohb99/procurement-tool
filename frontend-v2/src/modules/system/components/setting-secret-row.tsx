import { Badge } from '@/shared/ui/badge'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'

import type { SettingSecret } from '../types/setting'

interface SettingSecretRowProps {
  secret: SettingSecret
  value: string
  disabled: boolean
  onChange: (key: string, value: string) => void
}

/**
 * Ô nhập MỘT khóa bí mật (mật khẩu SMTP, khóa R2).
 *
 * Ba điều KHÔNG được làm ở đây, dù nhìn có vẻ tiện:
 * 1. Không hiển thị giá trị cũ — backend không trả về, và cũng không được xin.
 * 2. Không vẽ chuỗi chấm giả để "cho thấy có gì đó": số chấm là gợi ý độ dài
 *    mật khẩu. Trạng thái đã đặt hay chưa nói bằng nhãn, không bằng độ dài.
 * 3. Không có nút con mắt xem lại — chỉ xem được thứ chính mình vừa gõ, còn
 *    người đứng sau lưng thì xem được luôn.
 *
 * Ô để trống = giữ nguyên khóa cũ (xem `build-setting-values.ts`).
 */
export function SettingSecretRow({
  secret,
  value,
  disabled,
  onChange,
}: SettingSecretRowProps) {
  const inputId = `secret-${secret.key}`

  return (
    <div className="flex flex-col gap-1.5 py-2">
      <Label htmlFor={inputId} className="flex flex-wrap items-center gap-2 text-[13px]">
        {secret.label}
        {secret.configured ? (
          <Badge className="bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400">
            Đã cấu hình
          </Badge>
        ) : (
          <Badge variant="outline" className="text-muted-foreground">
            Chưa đặt
          </Badge>
        )}
      </Label>
      <Input
        id={inputId}
        type="password"
        autoComplete="new-password"
        disabled={disabled}
        value={value}
        placeholder={secret.configured ? 'Để trống nếu giữ nguyên' : 'Nhập giá trị…'}
        onChange={(event) => onChange(secret.key, event.target.value)}
      />
    </div>
  )
}
