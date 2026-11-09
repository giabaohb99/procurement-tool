import { describe, expect, it } from 'vitest'

import {
  COST_STAGE_ESTIMATE,
  COST_STAGE_FINAL,
  type PurchaseOrderItem,
} from '../types/purchase-order-detail'
import {
  buildCompleteConfirmMessage,
  buildExpectedDateDiffMessage,
  findExpectedDateDiffs,
} from './purchase-order-detail-confirm-messages'

type Summary = Parameters<typeof buildCompleteConfirmMessage>[0]['import_cost_summary']

function summary(overrides: Partial<NonNullable<Summary>> = {}): Summary {
  return { remaining_total: 0, lines_not_final: 0, ...overrides } as Summary
}

/** duoc-CR-741 — Hoàn thành LUÔN hỏi lại như bản v1; lời nhắc của v2 nối vào cùng hộp. */
describe('buildCompleteConfirmMessage', () => {
  it('asks even when nothing is owed — v2 used to complete silently in that case', () => {
    const message = buildCompleteConfirmMessage({
      status: 'received',
      cost_stage: COST_STAGE_FINAL,
      import_cost_summary: summary(),
    })
    expect(message).toBe(
      'Xác nhận HOÀN THÀNH đơn mua hàng này? Sau khi hoàn thành sẽ khóa, không chỉnh sửa được nữa.',
    )
  })

  it('warns that a partially received order is closed short', () => {
    const message = buildCompleteConfirmMessage({
      status: 'partial',
      cost_stage: COST_STAGE_FINAL,
      import_cost_summary: undefined,
    })
    expect(message).toMatch(/^Đơn mới nhận MỘT PHẦN\./)
  })

  it('appends both v2 reminders in one dialog instead of two dialogs in a row', () => {
    const message = buildCompleteConfirmMessage({
      status: 'received',
      cost_stage: COST_STAGE_ESTIMATE,
      import_cost_summary: summary({ remaining_total: 1_500_000, lines_not_final: 2 }),
    })
    expect(message).toContain('Đơn còn 1.500.000 đ chi phí thu mua chưa thanh toán.')
    expect(message).toContain('Còn 2 dòng chi phí chưa quyết toán.')
  })

  it('ignores sub-cent leftovers and skips the settle hint once the stage is final', () => {
    const message = buildCompleteConfirmMessage({
      status: 'received',
      cost_stage: COST_STAGE_FINAL,
      import_cost_summary: summary({ remaining_total: 0.005, lines_not_final: 3 }),
    })
    expect(message).not.toContain('chi phí thu mua chưa thanh toán')
    expect(message).not.toContain('chưa quyết toán')
  })
})

function line(overrides: Partial<PurchaseOrderItem> & { pr_expected_date?: string }) {
  return { product_code: 'ABA36', product_name: 'Abamectin', expected_date: '', ...overrides } as
    PurchaseOrderItem
}

/** duoc-CR-741 — bản v1 nhắc khi Ngày dự kiến có hàng lệch YCMH nguồn; v2 thiếu. */
describe('findExpectedDateDiffs', () => {
  it('flags only lines whose two dates are both set and differ', () => {
    const diffs = findExpectedDateDiffs([
      line({ expected_date: '2026-11-20', pr_expected_date: '2026-11-15' }),
      line({ product_name: 'Cùng ngày', expected_date: '2026-11-15', pr_expected_date: '2026-11-15' }),
      line({ product_name: 'Đơn trống', expected_date: '', pr_expected_date: '2026-11-15' }),
      line({ product_name: 'YCMH trống', expected_date: '2026-11-15', pr_expected_date: '' }),
      line({ product_name: 'Không có trường', expected_date: '2026-11-15' }),
    ])
    expect(diffs).toEqual([
      { name: 'Abamectin', requestDate: '2026-11-15', orderDate: '2026-11-20' },
    ])
  })

  it('skips blank lines that are not sent on save, and trims whitespace before comparing', () => {
    const diffs = findExpectedDateDiffs([
      line({ product_code: '', product_name: '', expected_date: '2026-11-20', pr_expected_date: '2026-11-15' }),
      line({ expected_date: ' 2026-11-15 ', pr_expected_date: '2026-11-15' }),
    ])
    expect(diffs).toEqual([])
  })

  it('falls back to the code when the line has no name', () => {
    const diffs = findExpectedDateDiffs([
      line({ product_name: '', expected_date: '2026-11-20', pr_expected_date: '2026-11-15' }),
    ])
    expect(diffs[0].name).toBe('ABA36')
  })

  it('returns nothing for an empty order', () => {
    expect(findExpectedDateDiffs([])).toEqual([])
  })
})

describe('buildExpectedDateDiffMessage', () => {
  it('prints the v1 sentence with dd/mm/yyyy dates', () => {
    const message = buildExpectedDateDiffMessage('YCMH-0001', [
      { name: 'Abamectin', requestDate: '2026-11-15', orderDate: '2026-11-20' },
    ])
    expect(message).toBe(
      'Các dòng sau đang có ngày dự kiến khác với yêu cầu mua hàng YCMH-0001:\n' +
        '• Abamectin: YCMH 15/11/2026 → đơn này 20/11/2026' +
        '\n\nNgày trên YCMH sẽ KHÔNG tự đổi theo. Nếu cần đổi, vào phiếu YCMH sửa (phải kèm lý do).',
    )
  })
})
