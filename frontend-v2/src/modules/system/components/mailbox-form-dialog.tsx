import { useState } from 'react'
import { KeyRound } from 'lucide-react'

import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { EmployeeMultiSelect } from '@/shared/ui/employee-multi-select'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Switch } from '@/shared/ui/switch'
import { Textarea } from '@/shared/ui/textarea'
import type { Mailbox, MailboxInput } from '../types/mailbox'

const EMPTY: MailboxInput = {
  code: '',
  name: '',
  email: '',
  display_name: '',
  smtp_host: 'smtp.gmail.com',
  smtp_port: 587,
  smtp_user: '',
  smtp_password: '',
  use_tls: true,
  company_id: null,
  note: '',
  is_active: true,
  employee_ids: [],
}

interface MailboxFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Có = sửa, không có = thêm mới. */
  mailbox?: Mailbox
  isPending?: boolean
  onSubmit: (input: MailboxInput) => void
  onClearPassword?: () => void
}

/**
 * KHAI MỘT HỘP THƯ GỬI (26/08/2026).
 *
 * Hai chỗ lệch khỏi form thường, cả hai đều cố ý:
 *
 * 1. **Mật khẩu ứng dụng để trống nghĩa là GIỮ NGUYÊN**, không phải xóa. API
 *    không bao giờ trả giá trị cũ nên form không có gì để điền sẵn; coi trống là
 *    xóa thì sửa mỗi cái tên cũng đủ làm hộp thư ngừng gửi được mà không dòng
 *    nào báo. Muốn xóa thật thì có nút riêng.
 * 2. **Danh sách người được dùng khai đích danh.** Quyền gửi thư danh nghĩa cả
 *    một phòng ban phải chỉ mặt đặt tên từng người, và phải kiểm toán được về
 *    sau "ai đã từng gửi thay ai".
 */
export function MailboxFormDialog({
  open,
  onOpenChange,
  mailbox,
  isPending = false,
  onSubmit,
  onClearPassword,
}: MailboxFormDialogProps) {
  const [form, setForm] = useState<MailboxInput>(EMPTY)
  //  Danh sách nhân sự để chọn người được dùng hộp thư. Lấy trang lớn thay vì
  //  phân trang: bộ chọn có ô tìm sẵn, mà công ty chỉ vài trăm người.
  const { data: employeeList } = useEmployees({ page_size: 500 })

  //  Nạp lại mỗi lần mở: hộp thoại dùng chung cho mọi dòng, không nạp lại là mở
  //  dòng thứ hai vẫn thấy dữ liệu dòng thứ nhất.
  //
  //  ⚠️ Chỉnh state NGAY TRONG LÚC RENDER, không dùng `useEffect` theo dõi
  //  `open`: đặt state trong effect gây render dây chuyền (cảnh báo
  //  `react-hooks/set-state-in-effect`), và React khuyên đúng cách này cho ca
  //  "dựng lại state khi một prop đổi". React thấy `setState` lúc đang render
  //  thì bỏ luôn kết quả render dở và chạy lại ngay — không có nhịp nào hiện ra
  //  màn hình với dữ liệu của dòng cũ.
  const [dangMo, setDangMo] = useState(open)
  if (open !== dangMo) {
    setDangMo(open)
    if (open) {
      setForm(
        mailbox
          ? {
              code: mailbox.code,
              name: mailbox.name,
              email: mailbox.email,
              display_name: mailbox.display_name,
              smtp_host: mailbox.smtp_host,
              smtp_port: mailbox.smtp_port,
              smtp_user: mailbox.smtp_user,
              //  Luôn rỗng — xem ghi chú ở đầu component.
              smtp_password: '',
              use_tls: mailbox.use_tls,
              company_id: mailbox.company_id,
              note: mailbox.note,
              is_active: mailbox.is_active,
              employee_ids: mailbox.employee_ids,
            }
          : EMPTY,
      )
    }
  }

  const set = <K extends keyof MailboxInput>(key: K, value: MailboxInput[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }))

  const canSubmit =
    form.code.trim() !== '' && form.name.trim() !== '' && form.email.includes('@')

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{mailbox ? 'Sửa hộp thư gửi' : 'Thêm hộp thư gửi'}</DialogTitle>
          <DialogDescription>
            Người được cấp hộp thư này sẽ chọn được nó lúc ban hành văn bản, và thư
            thông báo sẽ đi dưới danh nghĩa địa chỉ ở đây.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="mailbox-code">Mã</Label>
            <Input
              id="mailbox-code"
              value={form.code}
              placeholder="VD: HR"
              onChange={(event) => set('code', event.target.value.toUpperCase())}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="mailbox-name">Tên hộp thư</Label>
            <Input
              id="mailbox-name"
              value={form.name}
              placeholder="VD: Phòng Hành chính"
              onChange={(event) => set('name', event.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="mailbox-email">Địa chỉ gửi</Label>
            <Input
              id="mailbox-email"
              value={form.email}
              placeholder="hr@gmail.com"
              onChange={(event) => set('email', event.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="mailbox-display">Tên hiện trên thư</Label>
            <Input
              id="mailbox-display"
              value={form.display_name}
              placeholder="Phòng Hành chính"
              onChange={(event) => set('display_name', event.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="mailbox-host">Máy chủ SMTP</Label>
            <Input
              id="mailbox-host"
              value={form.smtp_host}
              onChange={(event) => set('smtp_host', event.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="mailbox-port">Cổng</Label>
            <Input
              id="mailbox-port"
              type="number"
              value={form.smtp_port}
              onChange={(event) => set('smtp_port', Number(event.target.value) || 587)}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="mailbox-user">Tài khoản đăng nhập SMTP</Label>
            <Input
              id="mailbox-user"
              value={form.smtp_user}
              placeholder="Để trống thì dùng chính địa chỉ gửi"
              onChange={(event) => set('smtp_user', event.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="mailbox-password">Mật khẩu ứng dụng</Label>
            <Input
              id="mailbox-password"
              type="password"
              autoComplete="new-password"
              value={form.smtp_password}
              placeholder={
                mailbox?.has_password ? 'Đã có — để trống nếu không đổi' : 'Dán mật khẩu ứng dụng'
              }
              onChange={(event) => set('smtp_password', event.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Gmail: bật xác minh 2 bước rồi tạo <b>Mật khẩu ứng dụng</b> — mật khẩu đăng
              nhập thường sẽ không gửi được.
            </p>
            {mailbox?.has_password && onClearPassword && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="text-destructive"
                onClick={onClearPassword}
              >
                <KeyRound className="size-3.5" />
                Xóa mật khẩu đang lưu
              </Button>
            )}
          </div>

          <div className="space-y-1.5 sm:col-span-2">
            <Label>Ai được gửi danh nghĩa hộp thư này</Label>
            <EmployeeMultiSelect
              value={form.employee_ids}
              onChange={(ids) => set('employee_ids', ids)}
              employees={employeeList?.items ?? []}
              placeholder="Chọn nhân sự…"
            />
            <p className="text-xs text-muted-foreground">
              Chỉ những người ở đây thấy hộp thư này trong hộp thoại Ban hành.
            </p>
          </div>

          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="mailbox-note">Ghi chú</Label>
            <Textarea
              id="mailbox-note"
              rows={2}
              value={form.note}
              onChange={(event) => set('note', event.target.value)}
            />
          </div>

          <div className="flex items-center gap-3 sm:col-span-2">
            <Switch
              id="mailbox-active"
              checked={form.is_active}
              onCheckedChange={(checked) => set('is_active', checked)}
            />
            <Label htmlFor="mailbox-active">Còn dùng</Label>
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button
            type="button"
            disabled={!canSubmit || isPending}
            onClick={() => onSubmit(form)}
          >
            Lưu
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
