import { ExternalLink, Eye } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Skeleton } from '@/shared/ui/skeleton'
import {
  SCOPE_MISSING_WARNINGS,
  describeScopeForOwner,
  joinLabels,
  type ScopeOwnerProfile,
  type ScopeTierGroup,
} from '../utils/scope-summary'

interface AccountScopeSummaryPanelProps {
  roleId: number | null
  roleName: string
  /** Bậc của vai trò, gom theo bậc (`groupEntitiesByScope`). */
  groups: ScopeTierGroup[]
  /**
   * Hồ sơ nhân sự của tài khoản. `null` = CHƯA ĐỌC ĐƯỢC (đang tải, thiếu quyền
   * xem nhân sự, hoặc hồ sơ nằm ngoài phạm vi của người đang khai) — khác hẳn
   * với "đọc được và thấy chưa gắn công ty", nên không được gộp một nhánh.
   */
  owner: ScopeOwnerProfile | null
  /** Ngoại lệ đang khai ở tầng 2, mỗi chiều một câu; rỗng = chưa khai gì. */
  exceptionLines: string[]
  isLoading: boolean
  /** Người đang khai quyền có đọc được ma trận vai trò không (`role.read`). */
  canReadRole: boolean
  /** Có `employee.read` không — để nói đúng LÝ DO khi `owner` là `null`. */
  canReadEmployee: boolean
}

/**
 * MỘT khối trả lời đúng một câu: **tài khoản này thấy gì**.
 *
 * Bản trước bày hai khối "Tầng 1" / "Tầng 2" nằm cạnh nhau kèm mấy đoạn giải
 * thích cơ chế. Đại ca bác ngày 19/09/2026: "viết dài quá đâu ai hiểu đâu, vậy
 * thì 2 tầng thành 1 rồi" — và đại ca nói đúng phần cốt lõi: bậc «Công ty» của
 * backend vốn đã nghĩa là *công ty trong hồ sơ của chính người này*, nên gán
 * vai trò xong là tài khoản có phạm vi đó luôn, không ai phải đi tick gì cả.
 * Vì thế khối này in thẳng TÊN THẬT lấy từ hồ sơ, còn năm ô tick tụt xuống mục
 * «Ngoại lệ» gấp lại bên dưới.
 *
 * CHỈ ĐỌC, cố ý: bậc thuộc về vai trò nên sửa ở đây là lặng lẽ đổi phạm vi của
 * mọi tài khoản khác đang mang vai trò đó — thứ không ai chờ đợi khi đang mở
 * một hộp thoại mang tên một người.
 */
export function AccountScopeSummaryPanel({
  roleId,
  roleName,
  groups,
  owner,
  exceptionLines,
  isLoading,
  canReadRole,
  canReadEmployee,
}: AccountScopeSummaryPanelProps) {
  //  Chưa đọc được hồ sơ thì vẫn nói được luật, chỉ là nói bằng "của người này"
  //  thay cho tên thật — và tuyệt đối KHÔNG cảnh báo "chưa gắn công ty", vì lúc
  //  đó mình không biết điều ấy đúng hay sai.
  const meanings = groups.map((group) => ({
    group,
    meaning: owner ? describeScopeForOwner(group.scope, owner) : { text: group.meaning },
  }))

  return (
    <div className="rounded-lg border border-primary/30 bg-primary/5 p-3">
      <p className="flex items-center gap-1.5 text-xs font-semibold text-navy">
        <Eye className="size-3.5" />
        Tài khoản này thấy gì với vai trò «{roleName}»
      </p>

      {isLoading ? (
        <Skeleton className="mt-2 h-16 w-full" />
      ) : !canReadRole ? (
        <p className="mt-2 text-xs text-muted-foreground">
          Bạn không có quyền xem vai trò nên không đọc được phạm vi của vai trò này.
          Phần Ngoại lệ bên dưới vẫn khai được, nhưng bạn đang khai mà không thấy nền.
        </p>
      ) : groups.length === 0 ? (
        <p className="mt-2 text-xs text-destructive">
          Vai trò này chưa được tick quyền XEM ở đối tượng nào — gán vai trò xong tài
          khoản vẫn không thấy gì. Kiểm lại ma trận quyền trước khi khai phạm vi.
        </p>
      ) : (
        <ul className="mt-2 space-y-1.5">
          {meanings.map(({ group, meaning }) => (
            <li key={group.scope} className="text-xs leading-relaxed">
              {/* Danh sách đầy đủ để ở `title`: nhóm "Tất cả" thường có vài chục
                  mục danh mục, in hết ra là che mất hai nhóm đáng đọc phía trên. */}
              <span className="font-medium text-navy" title={group.entityLabels.join(', ')}>
                {joinLabels(group.entityLabels, 4)}
              </span>
              {meaning.text && <span className="text-navy"> — {meaning.text}</span>}
              {meaning.missing && (
                <span className="mt-0.5 block font-medium text-destructive">
                  {SCOPE_MISSING_WARNINGS[meaning.missing]}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}

      {canReadRole && groups.length > 0 && owner === null && (
        //  Nói ra rằng câu trên đang thiếu tên thật, chứ đừng để người đọc tưởng
        //  hệ thống chỉ biết nói chung chung.
        <p className="mt-1.5 text-xs text-muted-foreground">
          {canReadEmployee
            ? 'Chưa đọc được hồ sơ nhân sự của tài khoản nên chưa thay được tên công ty / phòng ban thật vào câu trên.'
            : 'Bạn không có quyền xem nhân sự nên chưa thay được tên công ty / phòng ban thật vào câu trên.'}
        </p>
      )}

      {exceptionLines.length > 0 && (
        //  Ngoại lệ đã khai phải hiện Ở ĐÂY dù mục bên dưới đang gấp: gấp lại mà
        //  không nhắc thì khối này nói "thấy công ty ABA" trong khi thật ra còn
        //  một phòng bị loại trừ — đúng kiểu nói dối bằng cách bỏ bớt.
        <div className="mt-2 border-t border-primary/20 pt-2">
          <p className="text-xs font-medium text-navy">Ngoại lệ đang khai cho riêng tài khoản này:</p>
          <ul className="mt-0.5 list-disc space-y-0.5 pl-4 text-xs text-navy">
            {exceptionLines.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
      )}

      {canReadRole && roleId !== null && (
        <Link
          to={`${appRoutes.system.permissions}?role=${roleId}`}
          className="mt-2 inline-flex items-center gap-1 text-xs text-primary hover:underline"
        >
          Sửa bậc ở màn Ma trận quyền
          <ExternalLink className="size-3" />
        </Link>
      )}
    </div>
  )
}
