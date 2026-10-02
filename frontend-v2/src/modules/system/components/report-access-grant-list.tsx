import { Ban, Trash2 } from 'lucide-react'

import { AccessSubjectAvatar } from '@/shared/access-subject/access-subject-avatar'
import { EFFECT } from '@/shared/access-subject/subject-kind'
import { Badge } from '@/shared/ui/badge'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { useRevokeReportAccess } from '../hooks/use-report-access'
import type { ReportAccessGrant } from '../types/report-access'

interface ReportAccessGrantListProps {
  grants: ReportAccessGrant[]
}

/**
 * Khối 1 của hộp «Sửa quyền xem báo cáo» — mọi dòng CÒN SỐNG (API chỉ trả
 * loại này, không có dòng đã thu hồi để hiện lịch sử), thu hồi được từng dòng.
 *
 * Thu hồi dùng `ConfirmIconButton` có sẵn (hộp hỏi lại trước khi chạy) với lý
 * do rỗng — cùng tiền lệ `folder-share-people-list.tsx` / `document-share-
 * access-list.tsx`: không bắt gõ lại một câu mỗi lần thu hồi, hộp xác nhận đã
 * đủ để tránh bấm nhầm.
 */
export function ReportAccessGrantList({ grants }: ReportAccessGrantListProps) {
  const revoke = useRevokeReportAccess()

  if (grants.length === 0) {
    return (
      <p className="rounded-md border border-dashed px-3 py-6 text-center text-xs text-muted-foreground">
        Chưa gán cho ai — báo cáo này đang «Chưa gán — không ai xem được trong
        phân hệ Báo cáo».
      </p>
    )
  }

  return (
    <ul className="divide-y rounded-md border">
      {grants.map((grant) => {
        const name = grant.subject_name || '(đã xóa)'
        const denied = grant.effect === EFFECT.deny
        return (
          <li key={grant.id} className="flex items-center gap-3 px-3 py-2">
            <AccessSubjectAvatar subjectKind={grant.subject_kind} subjectName={name} />

            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium" title={name}>
                {name}
              </p>
              <p className="truncate text-xs text-muted-foreground">
                {grant.subject_kind_label}
                {grant.reason && ` · ${grant.reason}`}
              </p>
            </div>

            {denied ? (
              <Badge variant="destructive" className="shrink-0">
                <Ban className="size-3" />
                Cấm
              </Badge>
            ) : (
              <Badge variant="outline" className="shrink-0">
                Cho phép
              </Badge>
            )}

            <ConfirmIconButton
              icon={Trash2}
              title={`Thu hồi quyền của ${name}`}
              confirmTitle={`Thu hồi quyền của ${name}?`}
              //  KHÔNG "mất ngay" — backend nhớ hồ sơ phân quyền tối đa 60
              //  giây (cùng cơ chế với `role-permission-roles-tab.tsx`), và
              //  menu/route của chính NGƯỜI BỊ THU HỒI chỉ đổi khi họ tải lại
              //  thông tin tài khoản (đăng nhập lại / làm mới token) — không
              //  phải trong vòng 1 phút như cổng dữ liệu phía máy chủ.
              confirmDescription="Mất quyền xem trong tối đa 1 phút — gán lại được bất cứ lúc nào."
              confirmLabel="Thu hồi"
              destructive
              disabled={revoke.isPending}
              onConfirm={() => revoke.mutate({ accessId: grant.id, reason: '' })}
            />
          </li>
        )
      })}
    </ul>
  )
}
