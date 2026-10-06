import { describe, expect, it } from 'vitest'

import { classifyLeaveForPrint } from './leave-print-category'

describe('classifyLeaveForPrint', () => {
  it('ticks paid leave for annual leave', () => {
    expect(classifyLeaveForPrint(['Phép năm'], 1)).toEqual({ paid: true, unpaid: false, insurance: false })
  })

  it('ticks unpaid for unpaid leave and personal leave without pay', () => {
    expect(classifyLeaveForPrint(['Nghỉ không lương'], 2).unpaid).toBe(true)
    expect(classifyLeaveForPrint(['Nghỉ việc riêng'], 2)).toEqual({ paid: false, unpaid: true, insurance: false })
  })

  //  Mẫu chỉ có ba ô: cưới / tang / bù vẫn hưởng lương công ty nên rơi vào ô «có lương».
  it('puts company-paid special leave (wedding, funeral, comp-off) under the paid box', () => {
    for (const name of ['Nghỉ cưới hỏi', 'Nghỉ tang chế', 'Nghỉ bù', 'Nghỉ việc riêng có lương']) {
      expect(classifyLeaveForPrint([name], 1)).toEqual({ paid: true, unpaid: false, insurance: false })
    }
  })

  it('puts social-insurance leave (sick, maternity, paternity) under the insurance box', () => {
    for (const name of ['Nghỉ ốm đau', 'Nghỉ thai sản', 'Nghỉ vợ sinh con', 'Nghỉ khám thai']) {
      expect(classifyLeaveForPrint([name], 1)).toEqual({ paid: false, unpaid: false, insurance: true })
    }
  })

  //  «ốm … không lương» chứa cả hai từ khóa — không lương thắng, vì BHXH không chi.
  it('lets «không lương» win over a sickness keyword in the same name', () => {
    expect(classifyLeaveForPrint(['Nghỉ ốm không lương'], 1)).toEqual({ paid: false, unpaid: true, insurance: false })
  })

  it('ticks several boxes for a request that mixes leave types', () => {
    expect(classifyLeaveForPrint(['Phép năm', 'Nghỉ không lương', 'Nghỉ ốm đau'], 5)).toEqual({
      paid: true,
      unpaid: true,
      insurance: true,
    })
  })

  it('ignores case, spaces, null and empty names', () => {
    expect(classifyLeaveForPrint(['  NGHỈ THAI SẢN  ', null, undefined, ''], 1)).toEqual({
      paid: false,
      unpaid: false,
      insurance: true,
    })
  })

  //  Đơn cũ không có tên loại: có ngày thì coi là phép năm (như bản in trước), 0 ngày thì không ô nào.
  it('falls back to paid leave only when a nameless request still has days', () => {
    expect(classifyLeaveForPrint([], 1).paid).toBe(true)
    expect(classifyLeaveForPrint([null, ''], 0)).toEqual({ paid: false, unpaid: false, insurance: false })
    expect(classifyLeaveForPrint([], -1).paid).toBe(false)
  })
})
