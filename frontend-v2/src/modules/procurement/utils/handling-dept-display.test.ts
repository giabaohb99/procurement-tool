import { describe, expect, it } from 'vitest'

import {
  SHARED_PURCHASING_LABEL,
  handlingDeptForCreate,
  handlingDeptLabel,
  handlingDeptOptions,
  isHandlingDeptAssigned,
} from './handling-dept-display'

const departments = [
  { id: 5, name: 'Dego Organic', is_active: true },
  { id: 9, name: 'Phòng đã tắt', is_active: false },
]

describe('handlingDeptLabel — bao-CR-480', () => {
  it('0 / rỗng là Thu mua chung, không còn chữ «Không nhờ»', () => {
    expect(handlingDeptLabel(0)).toBe(SHARED_PURCHASING_LABEL)
    expect(handlingDeptLabel(undefined, '', departments)).toBe(SHARED_PURCHASING_LABEL)
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

describe('handlingDeptOptions — bao-CR-480', () => {
  it('Thu mua chung đứng đầu với giá trị 0, phòng đã tắt bị ẩn', () => {
    expect(handlingDeptOptions(departments, 0)).toEqual([
      { value: '0', label: SHARED_PURCHASING_LABEL },
      { value: '5', label: 'Dego Organic' },
    ])
  })

  it('phòng đã tắt mà phiếu cũ còn trỏ tới thì vẫn giữ để không mất nhãn', () => {
    expect(handlingDeptOptions(departments, 9)).toContainEqual({ value: '9', label: 'Phòng đã tắt' })
  })
})

describe('handlingDeptForCreate — bao-CR-488 (ô tick «Nhờ phòng khác xử lý» lúc lập phiếu)', () => {
  it('untouched tick + no department → send nothing, backend picks the default', () => {
    expect(isHandlingDeptAssigned({ handler_dept_id: 0 })).toBe(false)
    expect(handlingDeptForCreate({ handler_dept_id: 0 })).toBeUndefined()
  })

  it('ticked and «Thu mua chung» chosen → send an explicit 0 (factory asks shared purchasing)', () => {
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
