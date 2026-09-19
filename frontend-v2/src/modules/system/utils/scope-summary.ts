import type { PermissionMeta, RolePermissionRow } from '@/modules/hr/types/role'
import type { UserScope } from '@/modules/hr/types/user-account'

/**
 * Dịch hệ phân quyền HAI TẦNG ra lời thường.
 *
 * Tầng 1 — **bậc của vai trò** (`tab_permission.scope`, khai ở ma trận quyền):
 * cho trước một vùng nhìn, tính tương đối với chính người đang xem.
 * Tầng 2 — **giới hạn riêng của tài khoản** (`tab_user_scope`, khai ở hộp thoại
 * Phạm vi): cộng thêm hoặc bớt đi trên nền tầng 1.
 *
 * Hai tầng nằm ở hai màn khác nhau nên người khai quyền chỉ nhìn thấy một nửa
 * và không đọc ra được câu trả lời duy nhất họ cần: "rốt cuộc tài khoản này
 * thấy những gì". Mấy hàm dưới đây dựng đúng câu đó, tách khỏi giao diện để
 * kiểm được bằng test.
 */

/**
 * Bậc phạm vi nói bằng lời thường — KHÔNG nhắc tên cột, tên bảng, tên bậc.
 * Chủ ngữ ngầm là "tài khoản này thấy...".
 *
 * Nội dung lấy đúng theo `core/scoping.py`; sửa luật bên đó thì sửa cả ở đây.
 */
export const SCOPE_MEANINGS: Record<string, string> = {
  own: 'chỉ chứng từ do chính người này lập.',
  assigned: 'chứng từ do người này lập, cộng những chứng từ được giao cho họ xử lý.',
  proc: 'chứng từ được giao cho người này, cộng mọi chứng từ ĐÃ DUYỆT của toàn hệ.',
  dept_proc:
    'chứng từ ĐÃ DUYỆT của phòng người này, kể cả phiếu phòng khác nhờ phòng này mua giúp. Phiếu của phòng khác thì không thấy.',
  dept: 'mọi chứng từ của phòng ban người này.',
  company: 'mọi chứng từ trong công ty của người này.',
  all: 'mọi chứng từ trong toàn hệ thống, không phân biệt công ty hay phòng ban.',
}

/**
 * Hồ sơ nhân sự gắn với tài khoản — nguồn của công ty / phòng ban MẶC ĐỊNH.
 *
 * Vì sao câu tóm tắt phải đọc hồ sơ: `_role_scope_cond` lấy công ty và phòng ban
 * từ chính hồ sơ này (`profile["company_id"]`, `profile["dept_ids"]`). Bậc
 * «Công ty» của một tài khoản thuộc ABA nghĩa là *công ty ABA*, không phải một
 * ô ai đó phải đi tick. Đại ca nói đúng chỗ này ngày 19/09/2026: "tài khoản
 * thuộc công ty ABA thì mặc định phạm vi của nó là ABA".
 */
export interface ScopeOwnerProfile {
  /** `false` = tài khoản không gắn hồ sơ nhân sự nào (`employee_id = 0`). */
  hasProfile: boolean
  companyName?: string | null
  departmentName?: string | null
}

/** Một bậc đã dịch sang lời thường, có thay tên thật khi hồ sơ đủ dữ liệu. */
export interface ScopeMeaning {
  text: string
  /** Mốc trong hồ sơ mà bậc này cần nhưng tài khoản chưa có -> backend CHẶN SẠCH. */
  missing?: 'profile' | 'company' | 'department'
}

/**
 * Câu cảnh báo cho từng mốc còn thiếu.
 *
 * ⚠️ Không phải "lọc hụt" mà là **không thấy gì**: `_role_scope_cond` trả
 * `false()` khi `company_id = 0` (bậc công ty) hoặc khi không gắn phòng nào
 * (bậc phòng ban / thu mua trong phòng). Đó là chủ ý của backend — thiếu dữ
 * liệu thì chặn, mở toang nguy hiểm hơn — nên việc phải làm là đi gắn hồ sơ,
 * không phải khai bù ở hộp thoại này.
 */
export const SCOPE_MISSING_WARNINGS: Record<'profile' | 'company' | 'department', string> = {
  profile:
    'Tài khoản chưa gắn hồ sơ nhân sự nên không biết công ty / phòng ban của người này — bậc trên sẽ chặn sạch, tài khoản không thấy một chứng từ nào. Gắn hồ sơ nhân sự cho tài khoản trước đã.',
  company:
    'Hồ sơ nhân sự của tài khoản chưa gắn công ty — bậc trên sẽ chặn sạch, tài khoản không thấy một chứng từ nào. Vào Nhân sự gắn công ty cho người này, đừng khai bù ở dưới.',
  department:
    'Hồ sơ nhân sự của tài khoản chưa gắn phòng ban — bậc trên sẽ chặn sạch, tài khoản không thấy một chứng từ nào. Vào Nhân sự gắn phòng ban cho người này, đừng khai bù ở dưới.',
}

/**
 * Bậc phạm vi nói bằng TÊN THẬT của công ty / phòng ban trong hồ sơ.
 *
 * "mọi chứng từ trong công ty của người này" là câu đúng nhưng người đọc vẫn
 * phải tự đi tra người này thuộc công ty nào; "mọi chứng từ trong công ty
 * Dego Organic" thì đọc một lần là xong.
 */
export function describeScopeForOwner(scope: string, owner: ScopeOwnerProfile): ScopeMeaning {
  const company = (owner.companyName ?? '').trim()
  const department = (owner.departmentName ?? '').trim()
  const missingCompany = owner.hasProfile ? 'company' : 'profile'
  const missingDepartment = owner.hasProfile ? 'department' : 'profile'

  if (scope === 'company') {
    if (!company) return { text: SCOPE_MEANINGS.company, missing: missingCompany }
    return { text: `mọi chứng từ trong công ty ${company}.` }
  }
  if (scope === 'dept') {
    if (!department) return { text: SCOPE_MEANINGS.dept, missing: missingDepartment }
    return { text: `mọi chứng từ của phòng ${department}.` }
  }
  if (scope === 'dept_proc') {
    if (!department) return { text: SCOPE_MEANINGS.dept_proc, missing: missingDepartment }
    return {
      text: `chứng từ ĐÃ DUYỆT của phòng ${department}, kể cả phiếu phòng khác nhờ phòng này mua giúp. Phiếu của phòng khác thì không thấy.`,
    }
  }
  //  Mấy bậc còn lại tính theo chính NGƯỜI đó (`created_by`, `assignee_id`...),
  //  không mượn tới công ty hay phòng ban, nên không có gì để thay tên.
  return { text: SCOPE_MEANINGS[scope] ?? '' }
}

/** Một bậc phạm vi và những đối tượng đang dùng bậc đó. */
export interface ScopeTierGroup {
  scope: string
  /** Nhãn bậc do backend cấp (`/api/roles/meta`), vd "Được giao + đã duyệt trong phòng". */
  label: string
  /** Câu giải thích bằng lời thường; rỗng nếu backend thêm bậc mới mà đây chưa kịp. */
  meaning: string
  /** Nhãn các đối tượng (YCMH, ĐMH, Nhà cung cấp...) đang ở bậc này. */
  entityLabels: string[]
}

/**
 * Gom ma trận quyền của một vai trò thành vài NHÓM THEO BẬC.
 *
 * Chỉ tính dòng có quyền XEM: bậc của một đối tượng không được xem thì không
 * nói lên điều gì, mà kể ra thì nhóm nào cũng dài ngoằng.
 *
 * Thứ tự nhóm bám theo `meta.scopes` (backend xếp từ hẹp tới rộng), nên nhóm
 * đáng chú ý nhất — phần bị bó hẹp — luôn nằm trên.
 */
export function groupEntitiesByScope(
  rows: RolePermissionRow[],
  meta: PermissionMeta,
): ScopeTierGroup[] {
  const entityLabelByKey = new Map(meta.entities.map((item) => [item.key, item.label]))
  const scopeLabelByKey = new Map(meta.scopes.map((item) => [item.key, item.label]))
  const scopeOrder = new Map(meta.scopes.map((item, index) => [item.key, index]))

  const groups = new Map<string, ScopeTierGroup>()
  for (const row of rows) {
    if (row.can_read !== true) continue
    // Dòng cũ có thể thiếu `scope`; backend mặc định "own" (`tab_permission.scope`).
    const scope = row.scope || 'own'
    const group = groups.get(scope) ?? {
      scope,
      label: scopeLabelByKey.get(scope) ?? scope,
      meaning: SCOPE_MEANINGS[scope] ?? '',
      entityLabels: [],
    }
    group.entityLabels.push(entityLabelByKey.get(row.entity) ?? row.entity)
    groups.set(scope, group)
  }

  // Bậc lạ (backend thêm mới, meta chưa kịp) xếp cuối thay vì rơi lên đầu.
  const last = meta.scopes.length
  return [...groups.values()].sort(
    (a, b) => (scopeOrder.get(a.scope) ?? last) - (scopeOrder.get(b.scope) ?? last),
  )
}

/** Nhãn đã tick ở từng chiều của hộp thoại Phạm vi, đã đổi id sang tên. */
export interface ScopeLimitLabels {
  companies: string[]
  departments: string[]
  employees: string[]
  excludeDepartments: string[]
  excludeEmployees: string[]
}

/**
 * Ghép một danh sách nhãn thành cụm đọc được, cắt bớt khi quá dài.
 *
 * Người khai quyền hay chọn vài chục nhân sự; in hết ra thì câu tóm tắt dài hơn
 * cả phần tick và chẳng ai đọc.
 */
export function joinLabels(labels: string[], max = 3): string {
  if (labels.length <= max) return labels.join(', ')
  return `${labels.slice(0, max).join(', ')} và ${labels.length - max} mục khác`
}

/**
 * Giới hạn riêng của tài khoản, mỗi chiều một câu.
 *
 * ⚠️ "Phòng ban được xem" là **CỘNG THÊM**, không phải thu hẹp — `scope_condition`
 * ghép nó bằng `or_` với phạm vi của vai trò. Đây là chỗ hiểu nhầm đắt nhất của
 * màn này: tick một phòng vào đó KHÔNG làm tài khoản chỉ còn thấy phòng đó.
 *
 * Mảng rỗng trả về = chưa giới hạn gì, nơi gọi tự nói câu đó.
 */
export function summarizeScopeLimits(labels: ScopeLimitLabels): string[] {
  const lines: string[] = []
  if (labels.companies.length)
    lines.push(`Chỉ trong công ty ${joinLabels(labels.companies)}.`)
  if (labels.departments.length)
    lines.push(`Xem THÊM chứng từ của phòng ${joinLabels(labels.departments)}.`)
  if (labels.employees.length)
    lines.push(`Chỉ chứng từ do ${joinLabels(labels.employees)} lập.`)
  if (labels.excludeDepartments.length)
    lines.push(
      `Bỏ chứng từ của phòng ${joinLabels(labels.excludeDepartments)} (trừ phiếu phòng đó nhờ phòng mình mua giúp).`,
    )
  if (labels.excludeEmployees.length)
    lines.push(`Bỏ chứng từ do ${joinLabels(labels.excludeEmployees)} lập.`)
  return lines
}

/**
 * Đếm số mục NGOẠI LỆ đang khai ở tầng 2.
 *
 * Con số này đứng trên nhãn mục «Ngoại lệ» đang gấp lại — không có nó thì gấp
 * xong là giấu luôn cả thứ đang có hiệu lực, và người khai quyền không biết
 * mình cần mở ra xem hay không.
 */
export function countScopeExceptions(scope: UserScope): number {
  return (
    scope.companies.length +
    scope.departments.length +
    scope.employees.length +
    scope.exclude_companies.length +
    scope.exclude_departments.length +
    scope.exclude_employees.length
  )
}

/**
 * Cùng một phòng vừa ở ô "xem thêm" vừa ở ô "loại trừ" thì loại trừ THẮNG —
 * `_explicit_cond` nối mọi điều kiện loại trừ bằng `and_` sau phần cộng thêm.
 * Tick cả hai là tự bịt lại thứ vừa mở, nên phải nói ra tại chỗ.
 */
export function findContradictingDepartments(
  included: string[],
  excluded: string[],
): string[] {
  return included.filter((name) => excluded.includes(name))
}

/**
 * Phòng nào trong ô "loại trừ" lại là phòng của CHÍNH chủ tài khoản (phòng
 * chính hoặc kiêm nhiệm) — bao-CR-430, đại ca 19/09/2026: "cảnh báo thôi,
 * đừng chặn".
 *
 * Loại trừ thắng mọi bậc phạm vi, nên trừ đúng phòng mình là phiếu của phòng
 * mình biến mất khỏi mọi vai trò có gắn phạm vi này. Với bậc `dept_proc` (được
 * giao + đã duyệt TRONG PHÒNG) thì luật bậc gần như bị triệt tiêu: chỉ còn
 * phiếu phòng khác NHỜ phòng mình xử lý (`handler_dept_id`, CR-414) là lọt qua.
 * Có thể đó là ý người quản trị (nhà máy chỉ xem phiếu được nhờ), nên chỉ nói
 * ra chứ không chặn lưu.
 *
 * So bằng TÊN vì popup làm việc bằng tên phòng (lỗ 09-A). Tên rỗng/khoảng
 * trắng của chủ tài khoản bị bỏ qua — "chưa gắn phòng" không được khớp với gì.
 */
export function findSelfExcludedDepartments(
  excluded: string[],
  ownDepartments: string[],
): string[] {
  const own = new Set(ownDepartments.map((name) => name.trim()).filter(Boolean))
  if (own.size === 0) return []
  return excluded.filter((name) => own.has(name.trim()))
}
