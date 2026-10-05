import { describe, expect, it } from 'vitest'

import {
  DEFAULT_PURCHASING_LABEL,
  HANDLING_DEPT_DEFAULT_OPTION,
  handlingDeptCreateChange,
  handlingDeptCreateOptions,
  handlingDeptCreateValue,
  handlingDeptForCreate,
  handlingDeptLabel,
  handlingDeptOptions,
  isHandlingDeptAssigned,
} from './handling-dept-display'

const departments = [
  { id: 5, name: 'Dego Organic', is_active: true },
  { id: 9, name: 'Phòng đã tắt', is_active: false },
  { id: 20, name: 'Sản xuất -Thu mua', is_active: true },
]

describe('handlingDeptLabel — bao-CR-480 / bao-CR-524', () => {
  it('shows the real central department name the backend sends, never «Thu mua chung»', () => {
    //  bao-CR-524: phiếu cũ còn 0 cũng được backend trả kèm tên phòng thu mua mặc định.
    expect(handlingDeptLabel(0, 'Sản xuất -Thu mua')).toBe('Sản xuất -Thu mua')
    expect(handlingDeptLabel(20, 'Sản xuất -Thu mua')).toBe('Sản xuất -Thu mua')
    expect(handlingDeptLabel(0)).not.toMatch(/thu mua chung/i)
  })

  it('0 with no name (catalog lacks the central department) falls back to a neutral label', () => {
    expect(handlingDeptLabel(0)).toBe(DEFAULT_PURCHASING_LABEL)
    expect(handlingDeptLabel(undefined, '', departments)).toBe(DEFAULT_PURCHASING_LABEL)
    expect(handlingDeptLabel(null, '   ')).toBe(DEFAULT_PURCHASING_LABEL)
  })

  it('ưu tiên tên backend trả kèm, không cần danh mục phòng ban', () => {
    expect(handlingDeptLabel(5, 'Dego Organic')).toBe('Dego Organic')
  })

  it('thiếu tên từ backend thì tra danh mục đã nạp', () => {
    expect(handlingDeptLabel(5, '', departments)).toBe('Dego Organic')
  })

  it('không tra được ở đâu thì in số id chứ không in rỗng', () => {
    expect(handlingDeptLabel(77, '', departments)).toBe('Phòng #77')
  })
})

describe('handlingDeptOptions — bao-CR-524 (không còn mục ảo)', () => {
  it('offers only real departments — no option with value 0, no «Thu mua chung»', () => {
    const options = handlingDeptOptions(departments, 0)
    expect(options).toEqual([
      { value: '5', label: 'Dego Organic' },
      { value: '20', label: 'Sản xuất -Thu mua' },
    ])
    expect(options.some((o) => o.value === '0')).toBe(false)
    expect(options.some((o) => /thu mua chung/i.test(o.label))).toBe(false)
  })

  it('phòng đã tắt mà phiếu cũ còn trỏ tới thì vẫn giữ để không mất nhãn', () => {
    expect(handlingDeptOptions(departments, 9)).toContainEqual({ value: '9', label: 'Phòng đã tắt' })
  })

  it('empty catalog gives an empty list rather than a fake entry', () => {
    expect(handlingDeptOptions([], 0)).toEqual([])
  })
})

describe('handlingDeptForCreate — bao-CR-488 (ô tick «Nhờ phòng khác xử lý» lúc lập phiếu)', () => {
  it('untouched tick + no department → send nothing, backend picks the default', () => {
    expect(isHandlingDeptAssigned({ handler_dept_id: 0 })).toBe(false)
    expect(handlingDeptForCreate({ handler_dept_id: 0 })).toBeUndefined()
  })

  it('ticked but left empty → send an explicit 0 (backend stores the central department)', () => {
    expect(handlingDeptForCreate({ handler_dept_id: 0, handler_dept_assigned: true })).toBe(0)
  })

  it('ticked and a department chosen → send that id', () => {
    expect(handlingDeptForCreate({ handler_dept_id: 20, handler_dept_assigned: true })).toBe(20)
  })

  it('un-ticking wins over a leftover id — nothing is sent', () => {
    expect(handlingDeptForCreate({ handler_dept_id: 20, handler_dept_assigned: false })).toBeUndefined()
  })

  it('a draft copied from a source ticket with a handling department counts as ticked', () => {
    // YCBG tạo từ YCMH mang sẵn phòng xử lý — không được âm thầm rơi mất.
    expect(isHandlingDeptAssigned({ handler_dept_id: 5 })).toBe(true)
    expect(handlingDeptForCreate({ handler_dept_id: 5 })).toBe(5)
    expect(handlingDeptForCreate({ handler_dept_id: null })).toBeUndefined()
  })
})

//  03/10/2026 — ô Phòng xử lý lúc LẬP phiếu bỏ ô tick: mục mặc định «Phòng thu mua mặc định»
//  phải là trạng thái CHƯA nhờ (không gửi gì, backend tự chọn — nhà máy → chính phòng mình).
//  Quy nó về phòng 0 là ép mọi phiếu nhà máy sang thu mua chung, im lặng.
describe('handling department picker when creating', () => {
  it('puts the default entry first, then the department catalogue', () => {
    const options = handlingDeptCreateOptions(departments, 0)
    expect(options[0]).toEqual({ value: HANDLING_DEPT_DEFAULT_OPTION, label: DEFAULT_PURCHASING_LABEL })
    expect(options.slice(1)).toEqual(handlingDeptOptions(departments, 0))
  })

  it('never collides the default entry with a department id', () => {
    expect(HANDLING_DEPT_DEFAULT_OPTION).not.toBe('0')
    expect(Number.isNaN(Number(HANDLING_DEPT_DEFAULT_OPTION))).toBe(true)
  })

  it('shows the default entry until a real department is picked', () => {
    expect(handlingDeptCreateValue({})).toBe(HANDLING_DEPT_DEFAULT_OPTION)
    expect(handlingDeptCreateValue({ handler_dept_id: 0 })).toBe(HANDLING_DEPT_DEFAULT_OPTION)
    expect(handlingDeptCreateValue({ handler_dept_id: null })).toBe(HANDLING_DEPT_DEFAULT_OPTION)
    //  Bản cũ: tick mà để trống → vẫn là mặc định, không hiện số 0.
    expect(handlingDeptCreateValue({ handler_dept_assigned: true, handler_dept_id: 0 })).toBe(
      HANDLING_DEPT_DEFAULT_OPTION,
    )
    //  Nhờ rồi lại bỏ nhờ — id cũ còn nằm đó nhưng không được hiện.
    expect(handlingDeptCreateValue({ handler_dept_assigned: false, handler_dept_id: 5 })).toBe(
      HANDLING_DEPT_DEFAULT_OPTION,
    )
    expect(handlingDeptCreateValue({ handler_dept_id: 5 })).toBe('5')
  })

  it('maps the default entry and junk to un-assigned, a real id to assigned', () => {
    const unassigned = { handler_dept_assigned: false, handler_dept_id: 0 }
    expect(handlingDeptCreateChange(HANDLING_DEPT_DEFAULT_OPTION)).toEqual(unassigned)
    expect(handlingDeptCreateChange('0')).toEqual(unassigned)
    expect(handlingDeptCreateChange('')).toEqual(unassigned)
    expect(handlingDeptCreateChange('-3')).toEqual(unassigned)
    expect(handlingDeptCreateChange('abc')).toEqual(unassigned)
    expect(handlingDeptCreateChange('20')).toEqual({ handler_dept_assigned: true, handler_dept_id: 20 })
  })

  it('sends nothing for the default entry so the backend still picks the factory department', () => {
    expect(handlingDeptForCreate(handlingDeptCreateChange(HANDLING_DEPT_DEFAULT_OPTION))).toBeUndefined()
    expect(handlingDeptForCreate(handlingDeptCreateChange('20'))).toBe(20)
  })
})
