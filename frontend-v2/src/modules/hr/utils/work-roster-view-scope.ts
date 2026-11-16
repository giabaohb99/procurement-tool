import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import type { LookupOption } from '@/shared/types/api'
import { CONCURRENT_KIND_DEPARTMENT } from '../types/employee-concurrent'

/**
 * Ai XEM được lịch của ai trên màn Lịch làm việc (duoc-CR-761) — luật HIỂN THỊ, khớp chốt phạm vi của backend
 * `/api/work-roster`:
 *
 * - `all`: Nhân sự (`work_schedule.write`; quản trị có sẵn khóa này) — xem theo phạm vi `employee` như trước, đủ bộ lọc.
 * - `departments`: Trưởng phòng (`work_schedule_personal.write`, không có khóa Nhân sự) — chỉ phòng của mình (phòng
 *   chính + phòng kiêm nhiệm có bật phạm vi) và chính mình. Không lọc pháp nhân; ô phòng ban chỉ có phòng của mình.
 * - `company`: Giám đốc (`work_schedule_personal.read` bậc công ty, KHÔNG có `.write`) — chỉ xem, backend giới hạn trong
 *   công ty của họ. Không lọc pháp nhân; ô phòng ban đủ danh mục ("Tất cả phòng ban"), giữ ô tìm; không xếp ca.
 * - `self`: mọi người khác — chỉ lịch của chính mình, không bộ lọc, không ô tìm.
 *
 * Backend chốt thật; giao diện đoán sai chỉ làm bộ lọc thừa / thiếu, không lộ dữ liệu.
 */
export type RosterViewScope = 'all' | 'departments' | 'company' | 'self'

type CanFn = (entity: PermissionEntity, action: PermissionAction) => boolean

export function resolveRosterViewScope(can: CanFn): RosterViewScope {
  if (can('work_schedule', 'write')) return 'all'
  if (can('work_schedule_personal', 'write')) return 'departments'
  if (can('work_schedule_personal', 'read')) return 'company'
  return 'self'
}

interface ViewerDepartments {
  department_id?: number
  department_name?: string
  concurrents?: { kind: number; department_id: number; department_name: string; counts_scope: boolean }[]
}

/** Phòng của người xem cho ô lọc của Trưởng phòng: phòng chính trước, rồi phòng kiêm nhiệm có bật phạm vi; bỏ trùng. */
export function viewerDepartmentOptions(user: ViewerDepartments | null | undefined): LookupOption[] {
  const out: LookupOption[] = []
  const seen = new Set<number>()
  const push = (id: number, name: string | undefined) => {
    if (id > 0 && !seen.has(id)) {
      seen.add(id)
      out.push({ id, name: name || `Phòng #${id}` })
    }
  }
  push(Number(user?.department_id ?? 0), user?.department_name)
  for (const c of user?.concurrents ?? []) {
    if (c.kind === CONCURRENT_KIND_DEPARTMENT && c.counts_scope) push(Number(c.department_id), c.department_name)
  }
  return out
}

/** Nhãn mục `0` của ô phòng ban theo phạm vi; `null` = không có mục đó (Trưởng phòng chỉ một phòng). */
export function departmentAllLabel(scope: RosterViewScope, ownDepartments: number): string | null {
  if (scope === 'all' || scope === 'company') return 'Tất cả phòng ban'
  return ownDepartments > 1 ? 'Các phòng của tôi' : null
}

/** Phòng mặc định khi mở màn: Trưởng phòng = phòng chính (không có thì "các phòng của tôi"); còn lại = mọi phòng. */
export function defaultRosterDepartment(scope: RosterViewScope, own: readonly LookupOption[]): number {
  return scope === 'departments' ? (own[0]?.id ?? 0) : 0
}

/**
 * Phòng ĐANG LỌC của Trưởng phòng: id trên URL phải là phòng của mình (hoặc `0` khi được chọn "Các phòng của tôi");
 * dán link phòng khác thì kéo về phòng mặc định thay vì gửi bộ lọc backend sẽ trả rỗng. Phạm vi khác giữ nguyên.
 */
export function clampRosterDepartment(scope: RosterViewScope, requested: number, own: readonly LookupOption[]): number {
  if (scope !== 'departments') return requested
  if (requested === 0) return own.length > 1 ? 0 : defaultRosterDepartment(scope, own)
  return own.some((d) => d.id === requested) ? requested : defaultRosterDepartment(scope, own)
}
