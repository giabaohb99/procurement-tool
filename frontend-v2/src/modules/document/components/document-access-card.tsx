import { Ban, Pencil, ShieldCheck, UserPlus } from 'lucide-react'
import { useState } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { cn } from '@/shared/utils/cn'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import { useDocumentAccess, useGrantAccess, useRevokeAccess } from '../hooks/use-document-access'
import { EFFECT, type DocumentAccess } from '../types/document-access'
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
  //  Dòng đang sửa. `grant` ở backend là ghi đè theo (văn bản, đối tượng, chiều)
  //  nên sửa một dòng chính là cấp lại đúng dòng đó với bộ quyền mới — không cần
  //  cửa API riêng, và cũng không đẻ thêm dòng thứ hai cho cùng một người.
  const [dongDangSua, setDongDangSua] = useState<DocumentAccess | null>(null)

  const active = rows.filter((row) => row.is_active)

  return (
    <Card>
      {/*  `flex` chứ không chỉ `flex-row`: `CardHeader` gốc là `grid`, mà hai lớp
           này khác nhóm trong tailwind-merge nên `grid` vẫn thắng và nút bên
           phải rơi xuống hàng dưới. */}
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
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
                      Đã hủy {formatDateTime(row.revoked_at)}
                      {row.revoked_by_name && ` bởi ${row.revoked_by_name}`}
                      {row.revoke_reason && ` — ${row.revoke_reason}`}
                    </p>
                  )}
                </div>

                {row.is_active && canWrite && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    title="Sửa quyền"
                    aria-label={`Sửa quyền của ${row.subject_name}`}
                    onClick={() => setDongDangSua(row)}
                  >
                    <Pencil />
                  </Button>
                )}

                {row.is_active && canWrite && (
                  <ConfirmIconButton
                    icon={Ban}
                    title="Hủy quyền"
                    destructive
                    confirmTitle={`Hủy quyền của ${row.subject_name}?`}
                    confirmDescription="Dòng này vẫn ở lại bảng kèm mốc hủy — nhật ký chia sẻ chỉ thêm, không xóa."
                    //  ⚠️ KHÔNG để trống nhãn này thành «Hủy» trơn: nút bỏ qua
                    //  của hộp xác nhận cũng đang là «Hủy» (xem
                    //  `confirm-icon-button.tsx`). Hai nút cạnh nhau cùng chữ
                    //  «Hủy», một cái bỏ qua một cái thi hành, trên đúng một
                    //  thao tác không hoàn tác được — thêm chữ «quyền» là đủ
                    //  tách hai nghĩa mà vẫn đúng từ khách yêu cầu.
                    confirmLabel="Hủy quyền"
                    onConfirm={() =>
                      revoke.mutate({ accessId: row.id, reason: 'Hủy từ trang văn bản' })
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

      {dongDangSua && (
        <DocumentAccessDialog
          open
          onOpenChange={(open) => !open && setDongDangSua(null)}
          pending={grant.isPending || revoke.isPending}
          initial={{
            subjectLabel: dongDangSua.subject_name,
            values: {
              subject_kind: dongDangSua.subject_kind,
              subject_id: dongDangSua.subject_id,
              effect: dongDangSua.effect,
              can_read: true,
              can_write: dongDangSua.can_write,
              can_delete: dongDangSua.can_delete,
              valid_from: dongDangSua.valid_from,
              valid_to: dongDangSua.valid_to,
              reason: dongDangSua.reason,
            },
          }}
          onSubmit={async (rows) => {
            for (const row of rows) await grant.mutateAsync(row.values)

            //  Đổi sang đối tượng khác (hoặc đổi chiều tác động) thì dòng vừa
            //  ghi là một dòng MỚI — dòng cũ vẫn còn hiệu lực. Không thu hồi nó
            //  thì người dùng tưởng mình vừa "sửa", trong khi thực tế là vừa
            //  chia thêm cho một người nữa mà người cũ vẫn giữ nguyên quyền.
            const unchanged = rows.some(
              (row) =>
                row.values.subject_kind === dongDangSua.subject_kind &&
                row.values.subject_id === dongDangSua.subject_id &&
                row.values.effect === dongDangSua.effect,
            )
            if (!unchanged) {
              await revoke.mutateAsync({
                accessId: dongDangSua.id,
                reason: 'Sửa lại dòng chia quyền',
              })
            }

            setDongDangSua(null)
          }}
        />
      )}
    </Card>
  )
}
