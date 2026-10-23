import type { Employee } from '../types/employee'
import { SelfChangeRequestForm, type FamiliesSource } from './self-change-request-form'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'

interface SelfChangeRequestDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  employee: Employee
  families: FamiliesSource
}

/**
 * Hộp «Đề nghị sửa thông tin» của Trang cá nhân (duoc-CR-676, C6) — khung hộp thoại; thân ở
 * `self-change-request-form.tsx`.
 *
 * Bốn tab Cá nhân · Ngân hàng · Giấy tờ · Hộ gia đình, điền sẵn từ hồ sơ hiện tại. Gửi đi CHỈ ô đã
 * đổi; không đổi gì thì chặn bằng đúng câu 400 của backend. Phòng Nhân sự duyệt rồi mới áp vào hồ sơ.
 */
export function SelfChangeRequestDialog({ open, onOpenChange, employee, families }: SelfChangeRequestDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>Đề nghị sửa thông tin hồ sơ</DialogTitle>
          <DialogDescription>
            Sửa những ô cần đổi rồi bấm «Gửi đề nghị». Phòng Nhân sự duyệt rồi mới cập nhật vào hồ
            sơ. Số điện thoại, địa chỉ và người báo tin thì bạn tự sửa ngay ở thẻ «Liên hệ».
          </DialogDescription>
        </DialogHeader>
        {/*  Thân dựng lại MỖI LẦN mở: nháp luôn bắt đầu từ hồ sơ mới nhất, không sót chữ lần trước. */}
        {open && (
          <SelfChangeRequestForm employee={employee} families={families} onDone={() => onOpenChange(false)} />
        )}
      </DialogContent>
    </Dialog>
  )
}
