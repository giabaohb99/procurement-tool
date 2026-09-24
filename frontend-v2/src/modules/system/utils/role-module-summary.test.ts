import { describe, expect, it } from 'vitest'

import type { Role } from '@/modules/hr/types/role'
import {
  BASELINE_MIN_ROLES,
  findBaselineCells,
  summarizeRoleModules,
} from './role-module-summary'

/**
 * Chip phân hệ chỉ là CHỮ, nhưng chữ sai ở đây là người quản trị gán nhầm vai
 * trò cho người ("Kế toán" mà chip ghi "Thu mua"). Kiểm như một luật nghiệp vụ.
 */

let nextId = 1
function role(granted: Role['granted'] | undefined, code = `r${nextId}`): Role {
  const id = nextId++
  return { id, code, name: code, description: '', sort_order: id, granted }
}

/** Ô nền mà seed cấp cho mọi vai trò (rút gọn). */
const BASELINE = {
  job_position: ['read'],
  leave_request: ['read', 'create'],
  work_task: ['read', 'create', 'write'],
}

describe('summarizeRoleModules', () => {
  it('names the module whose cells the role actually has', () => {
    const r = role({ purchase_order: ['read', 'create'], supplier: ['read'] })
    const out = summarizeRoleModules([r])
    expect(out.get(r.id)).toEqual(['Thu mua', 'Sản xuất & Danh mục'])
  })

  it('returns an empty list for a role with no ticks, and for a role the old API sent without `granted`', () => {
    // Hai ca khác nhau, cùng một kết quả: nơi gọi in "Chưa cấp quyền".
    const empty = role({})
    const legacy = role(undefined)
    const out = summarizeRoleModules([empty, legacy])
    expect(out.get(empty.id)).toEqual([])
    expect(out.get(legacy.id)).toEqual([])
  })

  it('drops cells that nearly every role shares, so chips show what is DISTINCTIVE', () => {
    //  Lỗi gốc: seed cấp `work_task` đủ tám hành động cho mọi vai trò, đếm thô
    //  thì Kế toán, Thu mua, Tài xế đều ra chip "Dự án / Công việc" đứng đầu.
    const roles = [
      role({ ...BASELINE, payable: ['read', 'write'] }, 'ketoan'),
      role({ ...BASELINE, purchase_order: ['read'] }, 'thumua'),
      role({ ...BASELINE, vehicle_booking: ['read'] }, 'taixe'),
      role({ ...BASELINE, document: ['read'] }, 'vanthu'),
    ]
    const out = summarizeRoleModules(roles)
    expect(out.get(roles[0].id)).toEqual(['Tài chính'])
    expect(out.get(roles[1].id)).toEqual(['Thu mua'])
    expect(out.get(roles[2].id)).toEqual(['Đặt xe'])
    expect(out.get(roles[3].id)).toEqual(['Văn thư'])
  })

  it('falls back to the raw count for a role that has ONLY baseline cells', () => {
    //  Vai trò `employee` mặc định chỉ có đúng phần nền. Loại nền xong còn rỗng
    //  mà in "Chưa cấp quyền" là nói sai — nó vẫn vào được Nghỉ phép, Công việc.
    const roles = [
      role({ ...BASELINE }, 'employee'),
      role({ ...BASELINE, payable: ['read'] }),
      role({ ...BASELINE, purchase_order: ['read'] }),
      role({ ...BASELINE, document: ['read'] }),
    ]
    const out = summarizeRoleModules(roles)
    //  Xếp theo SỐ Ô giảm dần: work_task 3 ô · leave_request 2 ô · job_position 1 ô.
    expect(out.get(roles[0].id)).toEqual(['Dự án / Công việc', 'Nghỉ phép', 'Nhân sự'])
  })

  it('does not treat anything as baseline while the system has fewer roles than the floor', () => {
    //  Hệ mới 2-3 vai trò: hai vai trò tình cờ cùng đọc ĐMH không phải là nền.
    const roles = Array.from({ length: BASELINE_MIN_ROLES - 1 }, () =>
      role({ purchase_order: ['read'] }),
    )
    expect(findBaselineCells(roles).size).toBe(0)
    for (const r of roles) expect(summarizeRoleModules(roles).get(r.id)).toEqual(['Thu mua'])
  })

  it('ranks the module with more distinctive cells first, ties by declared group order', () => {
    const r = role({
      document: ['read'],
      purchase_order: ['read', 'create', 'write'],
      payable: ['read'],
    })
    const out = summarizeRoleModules([r])
    //  Thu mua 3 ô đứng đầu; Tài chính và Văn thư hòa 1-1 → theo thứ tự khai
    //  nhóm (Tài chính khai trước Văn thư).
    expect(out.get(r.id)).toEqual(['Thu mua', 'Tài chính', 'Văn thư'])
  })

  it('puts an entity no group knows under "Khác" instead of losing it', () => {
    const r = role({ brand_new_thing: ['read'] })
    expect(summarizeRoleModules([r]).get(r.id)).toEqual(['Khác'])
  })

  it('survives a null action list inside `granted`', () => {
    //  Backend không trả null, nhưng cột trái không được trắng màn vì một khóa lạ.
    const r = role({ purchase_order: null as unknown as string[], payable: ['read'] })
    expect(summarizeRoleModules([r]).get(r.id)).toEqual(['Tài chính'])
  })

  it('returns an empty map for no roles', () => {
    expect(summarizeRoleModules([]).size).toBe(0)
  })
})
