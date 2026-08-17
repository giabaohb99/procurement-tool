import { Building2, MinusCircle, PlusCircle, User, Users, X } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { SCOPE_DIM, SCOPE_MODE, type DocumentScope } from '../types/document-scope'

interface DocumentScopeRowProps {
  scope: DocumentScope
  onDelete?: (scopeId: number) => void
}

/** Một dòng phạm vi đọc thành câu: "Bao gồm · Phòng Kế toán — Công ty A". */
export function DocumentScopeRow({ scope, onDelete }: DocumentScopeRowProps) {
  const isExclude = scope.mode === SCOPE_MODE.exclude
  const Icon =
    scope.dim === SCOPE_DIM.company
      ? Building2
      : scope.dim === SCOPE_DIM.department
        ? Users
        : User

  return (
    <li className="flex items-center gap-3 py-2 first:pt-0">
      {/*  Loại trừ dùng biểu tượng trừ và màu cảnh báo: nó THẮNG mọi dòng bao
           gồm, nên phải nhìn ra ngay giữa một danh sách toàn dòng bao gồm. */}
      {isExclude ? (
        <MinusCircle className="size-4 shrink-0 text-destructive" />
      ) : (
        <PlusCircle className="size-4 shrink-0 text-muted-foreground" />
      )}

      <Icon className="size-4 shrink-0 text-muted-foreground" />

      <div className="min-w-0 flex-1">
        <p className="text-sm">
          {scope.dim === SCOPE_DIM.company && scope.company_name}
          {scope.dim === SCOPE_DIM.department && (
            <>
              {scope.department_name}
              <span className="text-muted-foreground"> — {scope.company_name}</span>
            </>
          )}
          {scope.dim === SCOPE_DIM.employee && scope.employee_name}
        </p>
        {scope.include_children && (
          <p className="text-xs text-muted-foreground">
            Gồm cả đơn vị con — kể cả công ty mở sau này
          </p>
        )}
      </div>

      {isExclude && <Badge variant="destructive">Loại trừ</Badge>}

      {onDelete && (
        <ConfirmIconButton
          icon={X}
          title="Gỡ dòng phạm vi"
          destructive
          confirmTitle="Gỡ dòng phạm vi này?"
          confirmDescription="Người thuộc dòng này sẽ không còn thấy văn bản trong mục «áp dụng cho tôi»."
          confirmLabel="Gỡ"
          onConfirm={() => onDelete(scope.id)}
        />
      )}
    </li>
  )
}
