import { describe, expect, it } from 'vitest'

import {
  shiftPendingAfterInsert,
  shiftPendingAfterRemove,
  type PendingLineFiles,
} from './pending-line-files'

function file(name: string) {
  return new File(['x'], name, { type: 'image/png' })
}

/** Đọc tên tệp ra để khẳng định cho dễ nhìn: {0: ['a.png']} -> {0: 'a.png'}. */
function names(files: PendingLineFiles) {
  return Object.fromEntries(
    Object.entries(files).map(([key, value]) => [key, value.map((f) => f.name).join(',')]),
  )
}

describe('giỏ hình của dòng chưa lưu', () => {
  it('xóa dòng giữa thì hình của dòng sau lùi một bậc, không nhảy sang dòng khác', () => {
    const before: PendingLineFiles = { 0: [file('a.png')], 1: [file('b.png')], 2: [file('c.png')] }

    expect(names(shiftPendingAfterRemove(before, 1))).toEqual({ 0: 'a.png', 1: 'c.png' })
  })

  it('xóa dòng nào thì bỏ luôn hình của dòng đó', () => {
    const before: PendingLineFiles = { 0: [file('a.png')], 1: [file('b.png')] }

    expect(names(shiftPendingAfterRemove(before, 0))).toEqual({ 0: 'b.png' })
  })

  it('xóa dòng đứng SAU thì các giỏ phía trước giữ nguyên chỗ', () => {
    const before: PendingLineFiles = { 0: [file('a.png')], 2: [file('c.png')] }

    expect(names(shiftPendingAfterRemove(before, 2))).toEqual({ 0: 'a.png' })
  })

  it('nhân bản dòng thì hình của các dòng sau tiến một bậc, bản sao để trống', () => {
    const before: PendingLineFiles = { 0: [file('a.png')], 1: [file('b.png')] }

    // Bản sao nằm ở chỉ số 1; giỏ cũ của chỉ số 1 dời sang 2, chỉ số 1 bỏ trống.
    expect(names(shiftPendingAfterInsert(before, 0))).toEqual({ 0: 'a.png', 2: 'b.png' })
  })

  it('nhân bản dòng cuối thì không giỏ nào phải dời', () => {
    const before: PendingLineFiles = { 0: [file('a.png')], 1: [file('b.png')] }

    expect(names(shiftPendingAfterInsert(before, 1))).toEqual({ 0: 'a.png', 1: 'b.png' })
  })

  it('giỏ rỗng thì hai phép dời đều trả về rỗng, không văng lỗi', () => {
    expect(shiftPendingAfterRemove({}, 0)).toEqual({})
    expect(shiftPendingAfterInsert({}, 0)).toEqual({})
  })
})
