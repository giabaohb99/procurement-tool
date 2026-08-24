import { Ban, ShieldCheck, UserPlus } from 'lucide-react'
import { useState } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { cn } from '@/shared/utils/cn'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import { useDocumentAccess, useGrantAccess, useRevokeAccess } from '../hooks/use-document-access'
import { EFFECT } from '../types/document-access'
import { DocumentAccessDialog } from './document-access-dialog'

interface DocumentAccessCardProps {
  documentId: number
  /** Ai sửa được văn bản thì mới quyết được ai đọc nó. */
  canWrite: boolean
}

/**
 * QUYỀN TRUY CẬP của một văn bản: đang chia cho ai, tới bao giờ, ai bị cấm.
 *
 * Hai điều nhìn thấy ngay trên bảng và cả hai đều là cố ý:
 *  - **dòng CẤM lên đầu**, tô đỏ — người đọc bảng cần thấy ngay ai đang bị chặn,
 *    vì cấm thắng mọi dòng cho phép và thắng cả phạm vi vai trò;
 *  - **dòng đã thu hồi vẫn nằm trong bảng** ở dạng mờ, kèm mốc và lý do (G19,
 *    G20). Xóa đi thì ba tháng sau không trả lời được câu "hồi tháng 7 ai đọc
 *    được văn bản này" — mà đó chính là câu người ta hỏi khi có chuyện.
 */
export function DocumentAccessCard({ documentId, canWrite }: DocumentAccessCardProps) {
  const { data: rows = [] } = useDocumentAccess(documentId)
  const grant = useGrantAccess(documentId)
  const revoke = useRevokeAccess(documentId)
  const [dialogOpen, setDialogOpen] = useState(false)

  const active = rows.filter((row) => row.is_active)

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <ShieldCheck className="size-4 text-muted-foreground" />
          Quyền truy cập ({active.length})
        </CardTitle>
        {canWrite && (
          <Button type="button" variant="outline" size="sm" onClick={() => setDialogOpen(true)}>
            <UserPlus className="size-4" />
            Chia quyền
          </Button>
        )}
      </CardHeader>

      <CardContent>
        <p className="mb-3 text-sm text-muted-foreground">
          Ngoài những người thấy văn bản này theo phạm vi vai trò của họ. Dòng
          <span className="font-medium"> Không cho phép </span>
          thắng mọi dòng cho phép.
        </p>

        {rows.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Chưa chia cho ai — hiện chỉ những người trong phạm vi vai trò xem được.
          </p>
        ) : (
          <ul className="divide-y">
            {rows.map((row) => (
              <li
                key={row.id}
                className={cn(
                  'flex flex-wrap items-start gap-3 py-3',
                  !row.is_active && 'opacity-55',
                )}
              >
                <div className="min-w-0 flex-1">
                  <p className="flex flex-wrap items-center gap-2 text-sm">
                    {row.effect === EFFECT.deny && (
                      <Ban className="size-3.5 shrink-0 text-destructive" />
                    )}
                    <span className="font-medium">{row.subject_name || '(đã xóa)'}</span>
                    <Badge variant="outline">{row.subject_kind_label}</Badge>
                    <Badge variant={row.effect === EFFECT.deny ? 'destructive' : 'secondary'}>
                      {row.effect_label}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {[row.can_read && 'xem', row.can_write && 'sửa', row.can_delete && 'xóa']
                        .filter(Boolean)
                        .join(' · ')}
                    </span>
                  </p>

                  <p className="mt-1 text-xs text-muted-foreground">
                    {row.valid_to ? `Hết hạn ${formatDate(row.valid_to)}` : 'Không đặt hạn'}
                    {row.granted_by_name && ` · ${row.granted_by_name} cấp`}
                    {row.reason && ` · ${row.reason}`}
                  </p>

                  {!row.is_active && (
                    <p className="mt-1 text-xs text-destructive">
                      Đã thu hồi {formatDateTime(row.revoked_at)}
                      {row.revoked_by_name && ` bởi ${row.revoked_by_name}`}
                      {row.revoke_reason && ` — ${row.revoke_reason}`}
                    </p>
                  )}
                </div>

                {row.is_active && canWrite && (
                  <ConfirmIconButton
                    icon={Ban}
                    title="Thu hồi"
                    destructive
                    confirmTitle={`Thu hồi quyền của ${row.subject_name}?`}
                    confirmDescription="Dòng này vẫn ở lại bảng kèm mốc thu hồi — nhật ký chia sẻ chỉ thêm, không xóa."
                    confirmLabel="Thu hồi"
                    onConfirm={() =>
                      revoke.mutate({ accessId: row.id, reason: 'Thu hồi từ trang văn bản' })
                    }
                  />
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>

      <DocumentAccessDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        pending={grant.isPending}
        //  Văn bản đã có id nên gửi thẳng lên máy chủ, tuần tự từng dòng. Trang
        //  TẠO văn bản dùng cùng hộp này nhưng xếp hàng chờ tới lúc tạo xong.
        onSubmit={async (rows) => {
          for (const row of rows) await grant.mutateAsync(row.values)
          setDialogOpen(false)
        }}
      />
    </Card>
  )
}
