import { describe, expect, it } from 'vitest'

import type { LeaveBalance } from '../types/leave'
import {
  flattenLeaveBalanceGroups,
  groupLeaveBalances,
  leaveBalanceRowClass,
  rowHasRealQuota,
  rowTotals,
} from './group-leave-balances'

let nextId = 1

function makeBalance(overrides: Partial<LeaveBalance> = {}): LeaveBalance {
  return {
    id: nextId++,
    employee_id: 1,
    employee_name: 'Trần Chí Dũng',
    year: 2026,
    leave_type_id: 1,
    leave_type_name: 'Phép năm',
    company_id: 1,
    allocated_days: 0,
    seniority_days: 0,
    carried_days: 0,
    adjusted_days: 0,
    used_days: 0,
    pending_days: 0,
    carried_out_days: 0,
    carried_expired_days: 0,
    note: '',
    total_days: 0,
    remaining_days: 0,
    ...overrides,
  }
}

describe('groupLeaveBalances', () => {
  it('cộng đúng mọi cột số của một người có nhiều loại nghỉ', () => {
    const groups = groupLeaveBalances([
      makeBalance({
        leave_type_name: 'Phép năm',
        allocated_days: 12,
        seniority_days: 2,
        used_days: 3,
        pending_days: 1,
        total_days: 14,
        remaining_days: 10,
      }),
      makeBalance({
        leave_type_id: 2,
        leave_type_name: 'Nghỉ bù',
        allocated_days: 0,
        carried_days: 2,
        total_days: 2,
        remaining_days: 2,
      }),
    ])

    expect(groups).toHaveLength(1)
    expect(groups[0].totals).toMatchObject({
      allocated_days: 12,
      seniority_days: 2,
      carried_days: 2,
      used_days: 3,
      pending_days: 1,
      total_days: 16,
      remaining_days: 12,
    })
  })

  it('giữ thứ tự người xuất hiện lần đầu, không tự sắp lại theo id hay theo tên', () => {
    //  Backend đã sắp danh sách; gom nhóm mà đảo thứ tự thì ô «Sắp xếp» của
    //  bảng nói một đằng, bảng hiện một nẻo.
    const groups = groupLeaveBalances([
      makeBalance({ employee_id: 9, employee_name: 'Vũ Anh' }),
      makeBalance({ employee_id: 2, employee_name: 'Bùi Bình' }),
      makeBalance({ employee_id: 9, employee_name: 'Vũ Anh', leave_type_id: 2 }),
    ])

    expect(groups.map((g) => g.employeeId)).toEqual([9, 2])
  })

  it('không để phép cộng dấu phẩy động rò ra bảng', () => {
    //  0.1 + 0.2 === 0.30000000000000004 trong JavaScript. Số ngày đi theo bước
    //  nửa ngày nên phép cộng này chạy thật, và một con số hai chục chữ số giữa
    //  bảng toàn số tròn là thứ người dùng chụp màn hình gửi lại ngay.
    const groups = groupLeaveBalances([
      makeBalance({ remaining_days: 0.1 }),
      makeBalance({ leave_type_id: 2, remaining_days: 0.2 }),
    ])

    expect(groups[0].totals.remaining_days).toBe(0.3)
  })

  it('lùi về #id khi mọi dòng đều rỗng tên, và không để một dòng rỗng xóa tên đã có', () => {
    const noName = groupLeaveBalances([
      makeBalance({ employee_id: 77, employee_name: '' }),
      makeBalance({ employee_id: 77, employee_name: '   ', leave_type_id: 2 }),
    ])
    expect(noName[0].employeeName).toBe('#77')

    const partial = groupLeaveBalances([
      makeBalance({ employee_id: 77, employee_name: '' }),
      makeBalance({ employee_id: 77, employee_name: 'Lê Có Tên', leave_type_id: 2 }),
      makeBalance({ employee_id: 77, employee_name: '', leave_type_id: 3 }),
    ])
    expect(partial[0].employeeName).toBe('Lê Có Tên')
  })

  it('chịu được danh sách rỗng và undefined', () => {
    expect(groupLeaveBalances([])).toEqual([])
    expect(groupLeaveBalances(undefined)).toEqual([])
  })

  it('coi cột thiếu hoặc không phải số là 0 thay vì đẻ ra NaN', () => {
    //  Một `NaN` lọt vào là CẢ CỘT tổng thành NaN, và bảng hiện "NaN" ở mọi
    //  hàng của người đó — vừa vô nghĩa vừa không truy ra được dòng nào gây ra.
    const broken = { ...makeBalance({ used_days: 3 }) } as unknown as Record<string, unknown>
    delete broken.remaining_days
    broken.total_days = null

    const groups = groupLeaveBalances([broken as unknown as LeaveBalance])
    expect(groups[0].totals.remaining_days).toBe(0)
    expect(groups[0].totals.total_days).toBe(0)
    expect(groups[0].totals.used_days).toBe(3)
  })

  it('đánh dấu có quỹ thật khi BẤT KỲ loại nghỉ nào được cấp, kể cả bị trừ tay', () => {
    //  `hasQuota` quyết «0 còn lại» tô đỏ (hết phép) hay để mờ (loại vốn không
    //  cấp hạn mức). Người có bảy loại hạn mức 0 và một loại 12 ngày mà tiêu
    //  hết thì vẫn là HẾT PHÉP.
    const noQuota = groupLeaveBalances([
      makeBalance({ leave_type_name: 'Nghỉ tang chế' }),
      makeBalance({ leave_type_id: 2, leave_type_name: 'Nghỉ cưới hỏi' }),
    ])
    expect(noQuota[0].hasQuota).toBe(false)

    const someQuota = groupLeaveBalances([
      makeBalance({ leave_type_name: 'Nghỉ tang chế' }),
      makeBalance({ leave_type_id: 2, allocated_days: 12 }),
    ])
    expect(someQuota[0].hasQuota).toBe(true)

    //  Điều chỉnh tay ÂM cũng là có động vào quỹ — `!== 0`, không phải `> 0`.
    const negativeAdjust = groupLeaveBalances([makeBalance({ adjusted_days: -2 })])
    expect(negativeAdjust[0].hasQuota).toBe(true)
  })
})

describe('flattenLeaveBalanceGroups', () => {
  it('người có MỘT loại nghỉ ra một hàng thẳng, không có gì để bung', () => {
    //  Công ty mới khai mỗi «Phép năm» thì đây là toàn bộ 261 hàng — một bảng
    //  261 mũi tên bung ra đúng một dòng chép lại con số vừa đọc còn tệ hơn
    //  bảng phẳng cũ.
    const groups = groupLeaveBalances([makeBalance({ id: 5 })])
    const rows = flattenLeaveBalanceGroups(groups, new Set())

    expect(rows).toHaveLength(1)
    expect(rows[0].kind).toBe('single')
    expect(rows[0].id).toBe('b5')
  })

  it('người nhiều loại nghỉ: thu gọn ra một hàng, bung ra kèm đủ dòng con', () => {
    const groups = groupLeaveBalances([
      makeBalance({ id: 10, employee_id: 4 }),
      makeBalance({ id: 11, employee_id: 4, leave_type_id: 2 }),
      makeBalance({ id: 12, employee_id: 4, leave_type_id: 3 }),
    ])

    expect(flattenLeaveBalanceGroups(groups, new Set()).map((r) => r.kind)).toEqual(['group'])
    expect(flattenLeaveBalanceGroups(groups, new Set([4])).map((r) => r.kind)).toEqual([
      'group',
      'child',
      'child',
      'child',
    ])
  })

  it('id hàng không đụng nhau giữa nhóm và dòng quỹ', () => {
    //  `getRowId` trùng là React dựng lại sai hàng — dấu hiệu là bung một nhóm
    //  thì nhóm khác nhảy chỗ. Nhóm dùng id NHÂN SỰ, dòng quỹ dùng id DÒNG, hai
    //  dãy số này trùng nhau liên tục nên phải có tiền tố.
    const groups = groupLeaveBalances([
      //  Nhân sự #1 có hai loại -> hàng nhóm "g1".
      makeBalance({ id: 100, employee_id: 1 }),
      makeBalance({ id: 101, employee_id: 1, leave_type_id: 2 }),
      //  Dòng quỹ id = 1, thuộc người khác -> hàng "b1".
      makeBalance({ id: 1, employee_id: 2, employee_name: 'Người khác' }),
    ])
    const rows = flattenLeaveBalanceGroups(groups, new Set([1]))
    const ids = rows.map((r) => r.id)

    expect(new Set(ids).size).toBe(ids.length)
    expect(ids).toEqual(['g1', 'b100', 'b101', 'b1'])
  })

  it('bung một nhóm không kéo theo nhóm khác', () => {
    const groups = groupLeaveBalances([
      makeBalance({ id: 1, employee_id: 1 }),
      makeBalance({ id: 2, employee_id: 1, leave_type_id: 2 }),
      makeBalance({ id: 3, employee_id: 2, employee_name: 'B' }),
      makeBalance({ id: 4, employee_id: 2, employee_name: 'B', leave_type_id: 2 }),
    ])

    const rows = flattenLeaveBalanceGroups(groups, new Set([2]))
    expect(rows.map((r) => r.id)).toEqual(['g1', 'g2', 'b3', 'b4'])
  })

  it('id trong tập đang bung mà không thuộc trang này thì bỏ qua, không nổ', () => {
    const groups = groupLeaveBalances([makeBalance({ id: 1, employee_id: 1 })])
    expect(() => flattenLeaveBalanceGroups(groups, new Set([999, -1, 0]))).not.toThrow()
  })
})

describe('leaveBalanceRowClass', () => {
  function rowsOf(expandedIds: number[]) {
    const groups = groupLeaveBalances([
      makeBalance({ id: 1, employee_id: 1 }),
      makeBalance({ id: 2, employee_id: 1, leave_type_id: 2 }),
      makeBalance({ id: 3, employee_id: 2, employee_name: 'Người một loại' }),
    ])
    return flattenLeaveBalanceGroups(groups, new Set(expandedIds))
  }

  it('hàng cha ĐANG BUNG khác hẳn hàng cha đang thu', () => {
    //  Khách nêu 19/09/2026: bung ra mà cha với con chỉ khác nhau một sắc xám
    //  thì giữa khối bốn năm hàng liền nhau không thấy hàng nào mở ra hàng nào.
    const [closed] = rowsOf([])
    const [open] = rowsOf([1])

    expect(leaveBalanceRowClass(closed, false)).not.toBe(leaveBalanceRowClass(open, true))
    expect(leaveBalanceRowClass(open, true)).toContain('bg-row-selected')
  })

  it('ba mức nền khác nhau hẳn — cha đang bung · con · hàng thường', () => {
    const [group, child] = rowsOf([1])
    const single = rowsOf([1])[3]

    const classes = [
      leaveBalanceRowClass(group, true),
      leaveBalanceRowClass(child, false),
      leaveBalanceRowClass(single, false),
    ]
    expect(new Set(classes).size).toBe(3)
  })

  it('hàng nhóm khai cả ba lớp nền về CÙNG một màu', () => {
    //  ⚠️ Hai luật nền tranh nhau ở cùng độ đặc hiệu (0,2,0): kẻ sọc
    //  `odd:`/`even:` của DataTable và `has-aria-expanded:bg-muted` nằm sẵn
    //  trong TableRow của shadcn — luật sau bắt theo SỰ CÓ MẶT của thuộc tính
    //  nên nó phủ lên mọi hàng có nút mũi tên. Thứ tự sinh CSS quyết định ai
    //  vẽ, nên cả ba phải cùng màu thì ai thắng cũng ra đúng màu.
    //  (Bỏ `has-aria-expanded:` là hàng cha đang bung bị kéo về xám — đúng lỗi
    //  khách bắt được 19/09/2026.)
    for (const expanded of [true, false]) {
      const [group] = rowsOf(expanded ? [1] : [])
      const cls = leaveBalanceRowClass(group, expanded)
      const mau = [...cls.matchAll(/(?:odd|even|has-aria-expanded):(bg-\S+)/g)].map((m) => m[1])

      expect(mau).toHaveLength(3)
      expect(new Set(mau).size).toBe(1)
    }
  })

  it('hàng con và hàng đơn không cần lớp has-aria-expanded — chúng không có nút', () => {
    const rows = rowsOf([1])
    const child = rows[1]
    const single = rows[3]

    expect(leaveBalanceRowClass(child, false)).not.toContain('has-aria-expanded')
    expect(leaveBalanceRowClass(child, false)).toMatch(/odd:bg-/)
    expect(leaveBalanceRowClass(single, false)).toMatch(/odd:bg-/)
  })

  it('CHỈ hàng con có nhánh cây, và nhánh đặt đúng chỗ thẳng hàng mũi tên', () => {
    //  24px = 12px đệm ô + nửa bề rộng nút mũi tên. Lệch con số này là thân cây
    //  chạy xuyên qua chữ hoặc nằm ngoài mép ô.
    const rows = rowsOf([1])
    const [group, child] = rows
    const single = rows[3]

    const cls = leaveBalanceRowClass(child, false)
    expect(cls).toContain('bg-[position:24px_0,24px_50%]')
    //  Hai lớp: thân dọc + nhánh ngang. Thiếu lớp ngang thì chỉ ra một vạch
    //  trơn — nó nói "cùng một khối" nhưng không nói hàng nào NỐI VÀO đâu, và
    //  khách bắt đúng chỗ đó (19/09/2026).
    expect(cls).toContain('12px_1px')

    //  Hàng đơn đứng một mình, không thuộc cụm nào — vẽ nhánh cho nó là bịa ra
    //  một quan hệ không có.
    expect(leaveBalanceRowClass(single, false)).not.toContain('bg-[position:')
    //  Hàng cha CHƯA bung cũng vậy: cụm đang đóng thì chưa có gì để nối tới.
    expect(leaveBalanceRowClass(group, false)).not.toContain('bg-[position:')
  })

  it('hàng cha ĐANG BUNG mọc gốc cây ở nửa dưới ô, và KHÔNG có nhánh ngang', () => {
    //  Thiếu đoạn gốc thì cây bắt đầu lơ lửng ở mép trên dòng con đầu, hở đúng
    //  nửa hàng ngay dưới mũi tên — chỗ mắt tìm đầu tiên khi hỏi "cụm này bắt
    //  đầu từ đâu". Nhánh ngang thì KHÔNG: hàng cha là gốc, không phải một nhánh.
    const [group] = rowsOf([1])
    const cls = leaveBalanceRowClass(group, true)

    expect(cls).toContain('bg-[position:24px_100%]')
    expect(cls).toContain('bg-[length:1px_50%]')
    expect(cls).not.toContain('12px_1px')
  })

  it('dòng con CUỐI cụm cắt thân cây ở giữa thành khuỷu └', () => {
    //  Thân chạy trọn chiều cao hàng cuối thì nó đâm sang hàng của người kế
    //  bên, và người đó đọc ra như thể cũng thuộc nhóm này.
    const rows = rowsOf([1])
    const giua = rows[1]
    const cuoi = rows[2]

    expect(giua.kind === 'child' && giua.isLast).toBe(false)
    expect(cuoi.kind === 'child' && cuoi.isLast).toBe(true)
    expect(leaveBalanceRowClass(giua, false)).toContain('bg-[length:1px_100%,12px_1px]')
    expect(leaveBalanceRowClass(cuoi, false)).toContain('bg-[length:1px_50%,12px_1px]')
  })
})

describe('rowTotals · rowHasRealQuota', () => {
  it('hàng nhóm đọc TỔNG, hàng con đọc chính dòng quỹ đó', () => {
    const groups = groupLeaveBalances([
      makeBalance({ id: 1, employee_id: 1, remaining_days: 4, allocated_days: 12 }),
      makeBalance({ id: 2, employee_id: 1, leave_type_id: 2, remaining_days: 6 }),
    ])
    const [groupRow, ...children] = flattenLeaveBalanceGroups(groups, new Set([1]))

    expect(rowTotals(groupRow).remaining_days).toBe(10)
    expect(rowTotals(children[0]).remaining_days).toBe(4)
    expect(rowTotals(children[1]).remaining_days).toBe(6)
  })

  it('dòng con KHÔNG thừa hưởng "có quỹ" của anh em cùng nhóm', () => {
    //  Người có phép năm 12 ngày và nghỉ tang chế 0 ngày: hàng nhóm và dòng
    //  phép năm tô đỏ khi hết, còn dòng tang chế phải để MỜ — nó vốn luôn 0.
    const groups = groupLeaveBalances([
      makeBalance({ id: 1, employee_id: 1, allocated_days: 12, remaining_days: 0 }),
      makeBalance({ id: 2, employee_id: 1, leave_type_id: 2, leave_type_name: 'Tang chế' }),
    ])
    const [groupRow, quotaChild, freeChild] = flattenLeaveBalanceGroups(groups, new Set([1]))

    expect(rowHasRealQuota(groupRow)).toBe(true)
    expect(rowHasRealQuota(quotaChild)).toBe(true)
    expect(rowHasRealQuota(freeChild)).toBe(false)
  })
})
