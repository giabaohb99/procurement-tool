import { describe, expect, it } from 'vitest'

import type { PermissionMeta, RolePermissionRow } from '@/modules/hr/types/role'
import {
  SCOPE_MEANINGS,
  findContradictingDepartments,
  findSelfExcludedDepartments,
  groupEntitiesByScope,
  joinLabels,
  summarizeScopeLimits,
} from './scope-summary'

/**
 * Mấy hàm này chỉ sinh CHỮ, không ghi gì xuống cơ sở dữ liệu — nhưng chữ sai ở
 * đây dẫn tới khai quyền sai, mà khai quyền sai thì không có triệu chứng nào.
 * Nên kiểm như kiểm một quy tắc nghiệp vụ, không kiểm như kiểm một nhãn.
 */

/** Đúng thứ tự backend trả (`SCOPES` trong `core/permissions.py`): hẹp -> rộng. */
const META: PermissionMeta = {
  entities: [
    { key: 'purchase_request', label: 'Yêu cầu mua hàng' },
    { key: 'purchase_order', label: 'Đơn mua hàng' },
    { key: 'supplier', label: 'Nhà cung cấp' },
  ],
  actions: [{ key: 'read', label: 'Xem' }],
  scopes: [
    { key: 'own', label: 'Của mình' },
    { key: 'assigned', label: 'Được giao' },
    { key: 'proc', label: 'Được giao + đã duyệt' },
    { key: 'dept_proc', label: 'Được giao + đã duyệt trong phòng' },
    { key: 'dept', label: 'Phòng ban' },
    { key: 'company', label: 'Công ty' },
    { key: 'all', label: 'Tất cả' },
  ],
}

function row(entity: string, scope: string, canRead = true): RolePermissionRow {
  return { entity, scope, can_read: canRead }
}

const NO_LIMIT = {
  companies: [],
  departments: [],
  employees: [],
  excludeDepartments: [],
  excludeEmployees: [],
}

describe('groupEntitiesByScope', () => {
  it('groups entities that share a scope and keeps the backend narrow-to-wide order', () => {
    const groups = groupEntitiesByScope(
      [
        row('supplier', 'all'),
        row('purchase_request', 'assigned'),
        row('purchase_order', 'dept_proc'),
      ],
      META,
    )

    expect(groups.map((g) => g.scope)).toEqual(['assigned', 'dept_proc', 'all'])
    expect(groups[0].entityLabels).toEqual(['Yêu cầu mua hàng'])
    expect(groups[1].label).toBe('Được giao + đã duyệt trong phòng')
    expect(groups[1].meaning).toBe(SCOPE_MEANINGS.dept_proc)
  })

  it('drops rows without read: a scope on something invisible says nothing', () => {
    // Ma trận quyền lưu ĐỦ mọi đối tượng, kể cả dòng không tick ô nào. Kể ra hết
    // thì nhóm "Của mình" phình lên mấy chục mục và che mất phần thật sự đáng đọc.
    const groups = groupEntitiesByScope(
      [row('purchase_request', 'assigned'), row('purchase_order', 'own', false)],
      META,
    )

    expect(groups).toHaveLength(1)
    expect(groups[0].scope).toBe('assigned')
  })

  it('falls back to "own" when a legacy row has an empty scope', () => {
    const groups = groupEntitiesByScope([{ entity: 'supplier', scope: '', can_read: true }], META)

    expect(groups[0].scope).toBe('own')
    expect(groups[0].label).toBe('Của mình')
  })

  it('puts a scope the backend added but meta does not know at the END, still readable', () => {
    // Bậc mới lên trước, meta của trình duyệt còn cache bản cũ 30 phút
    // (`usePermissionMeta`) -> phải hiện được, và không được chen lên đầu.
    const groups = groupEntitiesByScope(
      [row('supplier', 'ban_moi'), row('purchase_request', 'own')],
      META,
    )

    expect(groups.map((g) => g.scope)).toEqual(['own', 'ban_moi'])
    expect(groups[1].label).toBe('ban_moi')
    expect(groups[1].meaning).toBe('')
  })

  it('shows the raw key when meta has no label for an entity', () => {
    const groups = groupEntitiesByScope([row('thing_chua_khai', 'all')], META)

    expect(groups[0].entityLabels).toEqual(['thing_chua_khai'])
  })

  it('returns nothing for an empty matrix instead of throwing', () => {
    expect(groupEntitiesByScope([], META)).toEqual([])
  })

  it('survives meta with no scopes at all (API lỗi trả rỗng)', () => {
    const groups = groupEntitiesByScope([row('supplier', 'all')], {
      entities: [],
      actions: [],
      scopes: [],
    })

    expect(groups).toHaveLength(1)
    expect(groups[0].label).toBe('all')
  })
})

describe('joinLabels', () => {
  it('lists everything while the list is short', () => {
    expect(joinLabels(['A', 'B', 'C'])).toBe('A, B, C')
  })

  it('cuts a long list instead of printing 40 names into one sentence', () => {
    expect(joinLabels(['A', 'B', 'C', 'D', 'E'])).toBe('A, B, C và 2 mục khác')
  })

  it('handles the empty and single cases', () => {
    expect(joinLabels([])).toBe('')
    expect(joinLabels(['A'])).toBe('A')
  })
})

describe('summarizeScopeLimits', () => {
  it('says nothing when no box is ticked — the caller prints "chưa giới hạn"', () => {
    expect(summarizeScopeLimits(NO_LIMIT)).toEqual([])
  })

  it('calls the department include an ADDITION, never a restriction', () => {
    //  `scope_condition` ghép ô này bằng `or_` với phạm vi vai trò. Viết thành
    //  "chỉ xem phòng X" là dạy người khai quyền một luật NGƯỢC với backend —
    //  đúng chỗ đại ca đọc nhầm khi khai cho nhà máy (19/09/2026).
    const [line] = summarizeScopeLimits({ ...NO_LIMIT, departments: ['Dego Organic'] })

    expect(line).toContain('THÊM')
    expect(line).not.toMatch(/^Chỉ/)
  })

  it('calls the company include a restriction, because it really is one', () => {
    const [line] = summarizeScopeLimits({ ...NO_LIMIT, companies: ['DEGO'] })

    expect(line).toBe('Chỉ trong công ty DEGO.')
  })

  it('warns that an excluded department still shows tickets it asked us to buy', () => {
    // bao-CR-414: `_explicit_cond` mở ngoại lệ cho `handler_dept_id` là phòng mình.
    const [line] = summarizeScopeLimits({ ...NO_LIMIT, excludeDepartments: ['Dego Organic'] })

    expect(line).toContain('nhờ phòng mình mua giúp')
  })

  it('keeps one line per dimension, in reading order', () => {
    const lines = summarizeScopeLimits({
      companies: ['DEGO'],
      departments: ['Nhà máy'],
      employees: ['Nam'],
      excludeDepartments: ['Kế toán'],
      excludeEmployees: ['Hoa'],
    })

    expect(lines).toHaveLength(5)
    expect(lines[0]).toContain('công ty')
    expect(lines[4]).toContain('Hoa')
  })
})

describe('findContradictingDepartments', () => {
  it('catches a department ticked in both boxes — loại trừ thắng, phần mở thành vô nghĩa', () => {
    expect(findContradictingDepartments(['A', 'B'], ['B', 'C'])).toEqual(['B'])
  })

  it('stays quiet when the two boxes do not overlap', () => {
    expect(findContradictingDepartments(['A'], ['C'])).toEqual([])
    expect(findContradictingDepartments([], [])).toEqual([])
  })
})

describe('findSelfExcludedDepartments', () => {
  // bao-CR-430: trừ đúng phòng của chính chủ tài khoản thì phiếu phòng mình biến
  // mất khỏi mọi vai trò — chỉ cảnh báo, không chặn, nhưng phải nói ra.
  it('returns the owner primary department when it sits in the exclude box', () => {
    expect(findSelfExcludedDepartments(['Nhà máy', 'Kế toán'], ['Nhà máy'])).toEqual([
      'Nhà máy',
    ])
  })

  it('also catches a kiêm nhiệm department, not only the primary one', () => {
    expect(
      findSelfExcludedDepartments(['Kho', 'Kế toán'], ['Nhà máy', 'Kho']),
    ).toEqual(['Kho'])
  })

  it('stays quiet when only other departments are excluded', () => {
    expect(findSelfExcludedDepartments(['Kế toán'], ['Nhà máy'])).toEqual([])
    expect(findSelfExcludedDepartments([], ['Nhà máy'])).toEqual([])
  })

  it('never matches when the owner has no department — an empty name must not equal anything', () => {
    // Chủ tài khoản chưa gắn phòng: `department_name` về rỗng. Không lọc rỗng
    // thì một chip có tên rỗng/khoảng trắng (dữ liệu bẩn) sẽ khớp giả.
    expect(findSelfExcludedDepartments(['', '  ', 'Nhà máy'], ['', '  '])).toEqual([])
    expect(findSelfExcludedDepartments(['Nhà máy'], [])).toEqual([])
  })

  it('tolerates stray whitespace on either side', () => {
    expect(findSelfExcludedDepartments([' Nhà máy '], ['Nhà máy'])).toEqual([' Nhà máy '])
  })
})
