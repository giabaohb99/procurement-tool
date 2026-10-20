import { describe, expect, it } from 'vitest'

import { formatDays, formatEstimateRatio, formatRework, typeLabel } from './work-capability-format'

describe('work-capability-format', () => {
  it('formats days with a decimal comma and distinguishes null from zero', () => {
    expect(formatDays(3.5)).toBe('3,5 ngày')
    expect(formatDays(2)).toBe('2 ngày')
    expect(formatDays(0)).toBe('0 ngày')
    expect(formatDays(null)).toBe('—')
  })

  it('formats rework as a percentage and null as a dash', () => {
    expect(formatRework(0.08)).toBe('8,0%')
    expect(formatRework(null)).toBe('—')
  })

  it('formats the estimate ratio', () => {
    expect(formatEstimateRatio(1.5)).toBe('1,5×')
    expect(formatEstimateRatio(1)).toBe('1×')
    expect(formatEstimateRatio(null)).toBe('—')
  })

  it('joins kind and task type', () => {
    expect(typeLabel({ kind_label: 'Công việc dự án', task_type_name: 'Thiết kế' })).toBe('Công việc dự án › Thiết kế')
    expect(typeLabel({ kind_label: 'Đơn mua hàng', task_type_name: '' })).toBe('Đơn mua hàng')
  })
})
