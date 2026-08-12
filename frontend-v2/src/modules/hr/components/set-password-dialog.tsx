import { Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'

interface SetPasswordDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Chưa có tài khoản thì thao tác này TẠO tài khoản mới, không phải đổi mật khẩu. */
  hasAccount: boolean
  onSubmit: (password: string) => Promise<void>
}

/**
 * Đặt mật khẩu cho tài khoản của nhân sự.
 *
 * Form ngắn (2 ô) và có luật riêng "hai lần nhập phải khớp" nên dùng state
 * thường, không kéo react-hook-form + zod vào cho một chỗ này.
 */
export function SetPasswordDialog({
  open,
  onOpenChange,
  hasAccount,
  onSubmit,
}: SetPasswordDialogProps) {
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [saving, setSaving] = useState(false)

  // Dialog không unmount giữa các lần mở — xóa mật khẩu cũ khỏi ô nhập.
  useEffect(() => {
    if (open) {
      setPassword('')
      setConfirmation('')
    }
  }, [open])

  async function handleSubmit() {
    if (password.length < 4) {
      toast.error('Mật khẩu tối thiểu 4 ký tự')
      return
    }
    if (password !== confirmation) {
      toast.error('Hai mật khẩu không khớp')
      return
    }

    setSaving(true)
    try {
      await onSubmit(password)
      onOpenChange(false)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {hasAccount ? 'Đặt lại mật khẩu' : 'Tạo tài khoản & đặt mật khẩu'}
          </DialogTitle>
          <DialogDescription>
            Mật khẩu tối thiểu 4 ký tự. Nhân sự dùng email để đăng nhập.
            {!hasAccount && ' Tài khoản mới nhận vai trò mặc định "Nhân sự".'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="new-password">Mật khẩu mới</Label>
            <Input
              id="new-password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirm-password">Nhập lại mật khẩu</Label>
            <Input
              id="confirm-password"
              type="password"
              autoComplete="new-password"
              value={confirmation}
              onChange={(e) => setConfirmation(e.target.value)}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button onClick={handleSubmit} disabled={saving}>
            {saving && <Loader2 className="size-4 animate-spin" />}
            Xác nhận
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
