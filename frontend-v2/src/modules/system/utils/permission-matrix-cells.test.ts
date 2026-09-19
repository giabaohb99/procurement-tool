import { describe, expect, it } from 'vitest'

import type { RolePermissionRow } from '@/modules/hr/types/role'
import type { PermissionGroup } from '../config/permission-groups'
import {
  cellsState,
  collapseGroupsWithoutTicks,
  setCells,
  toggleCells,
  toPermissionPayload,
} from './permission-matrix-cells'

const ACTIONS = ['read', 'create', 'write', 'delete']

function rowsOf(...defs: Array<[string, string[]]>): Record<string, RolePermissionRow> {
  return Object.fromEntries(
    defs.map(([entity, granted]) => [
      entity,
      {
        entity,
        scope: 'own',
        ...Object.fromEntries(granted.map((action) => [`can_${action}`, true])),
      } as RolePermissionRow,
    ]),
  )
}

describe('cellsState', () => {
  it('trả false cho tập rỗng — dấu tick trên một phân hệ không có mục con là lời hứa suông', () => {
    expect(cellsState({}, [], ACTIONS)).toBe(false)
    expect(cellsState({}, ['purchase_request'], [])).toBe(false)
    expect(cellsState(rowsOf(['purchase_request', ACTIONS]), [], [])).toBe(false)
  })

  it('đọc được entity CHƯA CÓ DÒNG như là chưa cấp quyền gì', () => {
    expect(cellsState({}, ['purchase_request'], ACTIONS)).toBe(false)
  })

  it('phân biệt đủ / một phần / không', () => {
    const rows = rowsOf(['a', ACTIONS], ['b', ['read']])
    expect(cellsState(rows, ['a'], ACTIONS)).toBe(true)
    expect(cellsState(rows, ['b'], ACTIONS)).toBe('indeterminate')
    expect(cellsState(rows, ['a', 'b'], ACTIONS)).toBe('indeterminate')
    expect(cellsState(rows, ['a', 'b'], ['read'])).toBe(true)
    expect(cellsState(rows, ['a', 'b'], ['delete'])).toBe('indeterminate')
  })

  it('không đếm dồn khi entity bị khai TRÙNG trong danh sách', () => {
    // Một entity khai hai lần ở `permission-groups.ts` sẽ nhân đôi số ô "đang
    // bật" nhưng mẫu số cũng nhân đôi -> vẫn phải ra `true`, không ra nửa vời.
    const rows = rowsOf(['a', ACTIONS])
    expect(cellsState(rows, ['a', 'a'], ACTIONS)).toBe(true)
  })

  it('bỏ qua giá trị rác (chuỗi) ở ô quyền — chỉ cột nào TRUTHY mới tính là bật', () => {
    // `RolePermissionRow` khai index signature `boolean | string`, nên backend
    // trả "0"/"" là chuyện có thể xảy ra.
    const rows: Record<string, RolePermissionRow> = {
      a: { entity: 'a', scope: 'own', can_read: '', can_create: 'true' },
    }
    expect(cellsState(rows, ['a'], ['read'])).toBe(false)
    expect(cellsState(rows, ['a'], ['create'])).toBe(true)
  })
})

describe('setCells', () => {
  it('tạo dòng mới với phạm vi own cho entity chưa từng được tick', () => {
    const next = setCells({}, ['purchase_request'], ['read'], true)
    expect(next.purchase_request).toEqual({
      entity: 'purchase_request',
      scope: 'own',
      can_read: true,
    })
  })

  it('GIỮ NGUYÊN phạm vi đã đặt — bật thêm quyền không được reset về own', () => {
    const rows: Record<string, RolePermissionRow> = {
      a: { entity: 'a', scope: 'all', can_read: true },
    }
    expect(setCells(rows, ['a'], ['write'], true).a.scope).toBe('all')
    expect(setCells(rows, ['a'], ACTIONS, false).a.scope).toBe('all')
  })

  it('không sửa tại chỗ (state React phải đổi tham chiếu mới vẽ lại)', () => {
    const rows = rowsOf(['a', ['read']])
    const snapshot = structuredClone(rows)
    const next = setCells(rows, ['a'], ['write'], true)
    expect(rows).toEqual(snapshot)
    expect(next).not.toBe(rows)
    expect(next.a).not.toBe(rows.a)
  })

  it('không đụng tới entity ngoài danh sách', () => {
    const rows = rowsOf(['a', ['read']], ['b', ['read']])
    const next = setCells(rows, ['a'], ACTIONS, false)
    expect(next.b).toBe(rows.b)
  })

  it('tắt hết giữ lại dòng với đủ cột false — payload lọc dòng rỗng ở bước gửi', () => {
    const next = setCells(rowsOf(['a', ACTIONS]), ['a'], ACTIONS, false)
    for (const action of ACTIONS) expect(next.a[`can_${action}`]).toBe(false)
  })

  it('tập rỗng thì không tạo dòng nào', () => {
    expect(setCells({}, [], ACTIONS, true)).toEqual({})
    // Entity có mặt nhưng KHÔNG hành động nào: vẫn tạo dòng rỗng, và đó là ý
    // muốn — dòng rỗng bị `toPermissionPayload` loại trước khi gửi.
    expect(setCells({}, ['a'], [], true)).toEqual({ a: { entity: 'a', scope: 'own' } })
  })
})

describe('toggleCells', () => {
  it('đang bật ĐỦ thì tắt hết', () => {
    const next = toggleCells(rowsOf(['a', ACTIONS]), ['a'], ACTIONS)
    expect(cellsState(next, ['a'], ACTIONS)).toBe(false)
  })

  it('NỬA VỜI thì bật cho đủ, không phải tắt sạch', () => {
    // Bấm vào ô đang hiện dấu gạch nghĩa là "cho hết". Nếu tắt sạch thì người
    // dùng mất luôn những ô đã tick tay trước đó.
    const next = toggleCells(rowsOf(['a', ['read']], ['b', []]), ['a', 'b'], ACTIONS)
    expect(cellsState(next, ['a', 'b'], ACTIONS)).toBe(true)
  })

  it('chưa bật gì thì bật hết', () => {
    const next = toggleCells({}, ['a', 'b'], ACTIONS)
    expect(cellsState(next, ['a', 'b'], ACTIONS)).toBe(true)
  })

  it('tập rỗng thì bấm không đổi gì (và không nổ)', () => {
    expect(toggleCells({}, [], ACTIONS)).toEqual({})
  })
})

describe('toPermissionPayload', () => {
  const meta = {
    entities: [
      { key: 'purchase_order', label: 'Đơn mua hàng' },
      { key: 'document', label: 'Văn bản' },
    ],
    actions: ACTIONS.map((key) => ({ key, label: key })),
    scopes: [{ key: 'own', label: 'Của mình' }],
  }

  it('loại dòng không bật hành động nào — giữ lại chỉ tạo rác trong bảng phân quyền', () => {
    const payload = toPermissionPayload(meta, rowsOf(['purchase_order', ['read']]))
    expect(payload.map((row) => row.entity)).toEqual(['purchase_order'])
  })

  it('điền ĐỦ mọi cột hành động, kể cả cột chưa từng được tick', () => {
    const payload = toPermissionPayload(meta, rowsOf(['purchase_order', ['read']]))
    expect(payload[0]).toEqual({
      entity: 'purchase_order',
      scope: 'own',
      can_read: true,
      can_create: false,
      can_write: false,
      can_delete: false,
    })
  })

  it('KHÔNG phụ thuộc cây đang hiện — dòng bị ô tìm lọc ra ngoài vẫn được gửi', () => {
    // Đây là chốt chống MẤT QUYỀN của ô tìm (duoc-CR-408): lọc còn 1 dòng rồi
    // bấm Lưu thì quyền của những dòng đang ẩn phải còn nguyên. Hàm này đọc
    // `meta.entities` chứ không đọc `buildPermissionTree`, nên nó còn nguyên.
    const payload = toPermissionPayload(
      meta,
      rowsOf(['purchase_order', ['read']], ['document', ['read', 'write']]),
    )
    expect(payload.map((row) => row.entity).sort()).toEqual(['document', 'purchase_order'])
  })

  it('entity KHÔNG có trong meta thì không gửi lên, dù state còn giữ', () => {
    // Backend vừa bỏ một khóa quyền: state cũ trong `localStorage`/bộ nhớ không
    // được phép hồi sinh nó.
    const payload = toPermissionPayload(meta, rowsOf(['entity_da_xoa', ACTIONS]))
    expect(payload).toEqual([])
  })

  it('phạm vi rỗng rơi về own — backend không nhận chuỗi rỗng', () => {
    const rows: Record<string, RolePermissionRow> = {
      purchase_order: { entity: 'purchase_order', scope: '', can_read: true },
    }
    expect(toPermissionPayload(meta, rows)[0].scope).toBe('own')
  })
})

describe('collapseGroupsWithoutTicks', () => {
  // bao-CR-428: ma trận mở ra lần đầu chỉ xoè nhóm CÓ dấu tick; nhóm trống gập lại
  // để mắt người đọc rơi ngay vào phần vai trò thật sự được cấp.
  const COLLAPSE_TREE: PermissionGroup[] = [
    {
      id: 'procurement',
      title: 'Thu mua',
      entities: [
        { key: 'purchase_request', label: 'Yêu cầu mua hàng' },
        { key: 'purchase_order', label: 'Đơn mua hàng' },
      ],
    },
    { id: 'finance', title: 'Tài chính', entities: [{ key: 'payable', label: 'Công nợ' }] },
    { id: 'hr', title: 'Nhân sự', entities: [{ key: 'employee', label: 'Nhân sự' }] },
  ]
  const COLLAPSE_ACTIONS = ['read', 'create', 'write']

  it('collapses only the groups that have no tick at all', () => {
    const collapsed = collapseGroupsWithoutTicks(
      COLLAPSE_TREE,
      rowsOf(['purchase_order', ['read']]),
      COLLAPSE_ACTIONS,
    )
    expect([...collapsed].sort()).toEqual(['finance', 'hr'])
  })

  it('opens everything when the role has no tick anywhere — collapsing all would hide the whole matrix', () => {
    expect(collapseGroupsWithoutTicks(COLLAPSE_TREE, {}, COLLAPSE_ACTIONS).size).toBe(0)
    const allFalse: Record<string, RolePermissionRow> = {
      payable: { entity: 'payable', scope: 'own', can_read: false, can_write: false },
    }
    expect(collapseGroupsWithoutTicks(COLLAPSE_TREE, allFalse, COLLAPSE_ACTIONS).size).toBe(0)
  })

  it('ignores columns outside the action list', () => {
    const rows: Record<string, RolePermissionRow> = {
      payable: { entity: 'payable', scope: 'own', can_legacy: true },
      employee: { entity: 'employee', scope: 'own', can_read: true },
    }
    const collapsed = collapseGroupsWithoutTicks(COLLAPSE_TREE, rows, COLLAPSE_ACTIONS)
    expect([...collapsed].sort()).toEqual(['finance', 'procurement'])
  })

  it('returns an empty set for an empty tree', () => {
    expect(collapseGroupsWithoutTicks([], rowsOf(['a', ['read']]), COLLAPSE_ACTIONS).size).toBe(0)
  })
})
