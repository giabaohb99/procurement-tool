import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { LeaveCloseYearReviewRow } from '../types/leave'
import { LeaveCloseYearReviewCard } from './leave-close-year-review-card'

function row(overrides: Partial<LeaveCloseYearReviewRow> = {}): LeaveCloseYearReviewRow {
  return {
    employee_id: 1,
    employee_code: 'NV001',
    employee_name: 'Nguyễn Văn An',
    source_type_id: 1,
    source_type_name: 'Phép năm',
    dest_type_id: 1,
    dest_type_name: 'Phép năm chuyển sang',
    ratio: 1,
    before_days: 8,
    after_days: 3,
    diff_days: -5,
    credited_days: 5,
    dest_carried_days: 5,
    ...overrides,
  }
}

/** Chữ của một đoạn, gộp khoảng trắng — số và nhãn nằm ở các span con khác nhau. */
function textOf(el: HTMLElement | null): string {
  return (el?.textContent ?? '').replace(/\s+/g, ' ').trim()
}

describe('LeaveCloseYearReviewCard', () => {
  it('puts the person first with the code on its own line, and the leave type beside it', () => {
    render(<LeaveCloseYearReviewCard row={row()} />)
    expect(screen.getByText('Nguyễn Văn An')).toBeInTheDocument()
    expect(screen.getByText('NV001')).toBeInTheDocument()
    expect(screen.getByText('Phép năm')).toBeInTheDocument()
  })

  it('keeps old -> new and the difference in one line so the comparison reads at a glance', () => {
    render(<LeaveCloseYearReviewCard row={row()} />)
    expect(textOf(screen.getByText('Số cũ').parentElement)).toBe('Số cũ 8 số mới 3 (chênh -5)')
  })

  it('formats half days exactly like the table (dot, no trailing zero)', () => {
    //  Bảng dùng 8.5 chứ không 8.50 / 8,5 — thẻ lệch định dạng là hai lối bày ra hai con số.
    render(<LeaveCloseYearReviewCard row={row({ before_days: 8.5, after_days: 0, diff_days: -8.5, credited_days: 4.25 })} />)
    expect(textOf(screen.getByText('Số cũ').parentElement)).toBe('Số cũ 8.5 số mới 0 (chênh -8.5)')
    expect(screen.getByText('4.25')).toBeInTheDocument()
  })

  it('says the destination type is not configured instead of leaving a blank', () => {
    render(<LeaveCloseYearReviewCard row={row({ dest_type_name: '', credited_days: 0 })} />)
    expect(textOf(screen.getByText('Chưa khai').parentElement)).toBe('Sang Chưa khai, cộng vào năm sau 0 ngày')
  })
})
