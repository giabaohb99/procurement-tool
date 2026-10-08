import { QrCode, RefreshCw, Smartphone } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { cn } from '@/shared/utils/cn'

import { useZaloLogin, useZaloRefreshGroups, useZaloStatus } from '../hooks/use-chat-groups'
import { describeZaloState, toQrImageSrc } from '../utils/chat-group-format'

interface ZaloAccountCardProps {
  /** `agent_group.write` — mới được đăng nhập / đồng bộ, và mới thấy ảnh QR. */
  canManage: boolean
}

/**
 * Tài khoản Zalo của công ty (ai-CR-122) — tình trạng phiên + đăng nhập QR ngay trên web (ai-CR-123).
 *
 * Số Zalo dùng ở đây phải KHÁC mọi số đang chạy bot IDA: mỗi tài khoản Zalo chỉ giữ được một phiên trên máy tính,
 * quét trùng là hai bot đá nhau.
 */
export function ZaloAccountCard({ canManage }: ZaloAccountCardProps) {
  const [qrOpen, setQrOpen] = useState(false)
  const status = useZaloStatus(true)
  const login = useZaloLogin()
  const refresh = useZaloRefreshGroups()
  const view = describeZaloState(status.data)
  const qrSrc = toQrImageSrc(status.data?.qr_image)
  const connected = status.data?.state === 'connected'

  const startLogin = () => {
    setQrOpen(true)
    login.mutate(undefined, { onError: (e) => toast.error(extractErrorMessage(e)) })
  }

  return (
    <Card className="flex flex-wrap items-center gap-3 p-4">
      <Smartphone className="size-5 text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <div className="text-sm font-medium">Zalo tài khoản công ty</div>
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span className={cn('rounded-full px-2 py-0.5 font-medium', view.tone)}>{view.label}</span>
          {status.data?.name && <span>{status.data.name}</span>}
          {typeof status.data?.groups === 'number' && <span>{status.data.groups} nhóm</span>}
          {status.data?.reason && !connected && <span>{status.data.reason}</span>}
        </div>
      </div>
      {canManage && status.data?.enabled && (
        <div className="flex gap-2">
          {connected ? (
            <Button
              variant="outline"
              size="sm"
              disabled={refresh.isPending}
              onClick={() =>
                refresh.mutate(undefined, {
                  onSuccess: () => toast.success('Đang đồng bộ lại nhóm và thành viên Zalo'),
                  onError: (e) => toast.error(extractErrorMessage(e)),
                })
              }
            >
              <RefreshCw className="mr-1.5 size-4" /> Đồng bộ nhóm
            </Button>
          ) : (
            <Button size="sm" disabled={login.isPending} onClick={startLogin}>
              <QrCode className="mr-1.5 size-4" /> Đăng nhập Zalo
            </Button>
          )}
        </div>
      )}

      <Dialog open={qrOpen && !connected} onOpenChange={setQrOpen}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Quét mã để đăng nhập Zalo</DialogTitle>
            <DialogDescription>
              Mở Zalo trên điện thoại giữ <b>số Zalo của công ty</b>, chọn quét mã QR. Không dùng số đang chạy bot
              IDA. Mã sống khoảng một phút, hết hạn thì bấm lấy mã mới.
            </DialogDescription>
          </DialogHeader>
          <div className="flex min-h-56 items-center justify-center">
            {qrSrc ? (
              <img src={qrSrc} alt="Mã QR đăng nhập Zalo" className="size-56 rounded-md border" />
            ) : (
              <span className="text-sm text-muted-foreground">Đang lấy mã QR…</span>
            )}
          </div>
          {status.data?.state !== 'qr' && !login.isPending && (
            <Button variant="outline" onClick={startLogin}>
              Lấy mã mới
            </Button>
          )}
        </DialogContent>
      </Dialog>
    </Card>
  )
}
