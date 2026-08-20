import { describe, expect, it } from 'vitest'

import {
  pendingFilesOfLine,
  setPendingDeliveryFiles,
  shiftPendingAfterDeliveryRemove,
  shiftPendingAfterLineInsert,
  shiftPendingAfterLineRemove,
  type PendingDeliveryFiles,
} from './pending-delivery-files'

function file(name: string) {
  return new File(['x'], name, { type: 'application/pdf' })
}

/** Đọc tên tệp ra để khẳng định cho dễ nhìn: {'0:1': [a.pdf]} -> {'0:1': 'a.pdf'}. */
function names(files: Record<string | number, File[]>) {
  return Object.fromEntries(
    Object.entries(files).map(([key, value]) => [key, value.map((f) => f.name).join(',')]),
  )
}

describe('giỏ phiếu giao của lần giao chưa lưu', () => {
  it('lọc đúng giỏ của một dòng hàng và đổi về khóa theo chỉ số lần giao', () => {
    const before: PendingDeliveryFiles = {
      '0:0': [file('a.pdf')],
      '1:0': [file('b.pdf')],
      '1:2': [file('c.pdf')],
    }

    expect(names(pendingFilesOfLine(before, 1))).toEqual({ 0: 'b.pdf', 2: 'c.pdf' })
  })

  it('đặt giỏ rỗng thì bỏ hẳn khóa, không để lại mảng rỗng', () => {
    const before: PendingDeliveryFiles = { '0:0': [file('a.pdf')] }

    expect(setPendingDeliveryFiles(before, 0, 0, [])).toEqual({})
  })

  it('xóa lần giao giữa thì các lần sau CỦA CÙNG DÒNG lùi một bậc', () => {
    const before: PendingDeliveryFiles = {
      '0:0': [file('a.pdf')],
      '0:1': [file('b.pdf')],
      '0:2': [file('c.pdf')],
    }

    expect(names(shiftPendingAfterDeliveryRemove(before, 0, 1))).toEqual({
      '0:0': 'a.pdf',
      '0:1': 'c.pdf',
    })
  })

  it('xóa lần giao của dòng này thì không đụng tới giỏ của dòng khác', () => {
    const before: PendingDeliveryFiles = { '0:0': [file('a.pdf')], '1:0': [file('b.pdf')] }

    expect(names(shiftPendingAfterDeliveryRemove(before, 0, 0))).toEqual({ '1:0': 'b.pdf' })
  })

  it('xóa dòng hàng thì bỏ giỏ của nó, các dòng sau lùi một bậc', () => {
    const before: PendingDeliveryFiles = {
      '0:0': [file('a.pdf')],
      '1:0': [file('b.pdf')],
      '2:1': [file('c.pdf')],
    }

    expect(names(shiftPendingAfterLineRemove(before, 1))).toEqual({
      '0:0': 'a.pdf',
      '1:1': 'c.pdf',
    })
  })

  it('nhân bản dòng hàng thì các dòng sau tiến một bậc, bản sao để trống', () => {
    const before: PendingDeliveryFiles = { '0:0': [file('a.pdf')], '1:0': [file('b.pdf')] }

    // Bản sao nằm ở dòng 1; giỏ cũ của dòng 1 dời sang dòng 2.
    expect(names(shiftPendingAfterLineInsert(before, 0))).toEqual({
      '0:0': 'a.pdf',
      '2:0': 'b.pdf',
    })
  })

  it('giỏ rỗng thì mọi phép dời đều trả về rỗng, không văng lỗi', () => {
    expect(shiftPendingAfterDeliveryRemove({}, 0, 0)).toEqual({})
    expect(shiftPendingAfterLineRemove({}, 0)).toEqual({})
    expect(shiftPendingAfterLineInsert({}, 0)).toEqual({})
  })
})
