import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { useEmployeeWorkHistoryEditorDialog } from './use-employee-work-history-editor-dialog'

function row(overrides: Partial<EmployeeWorkHistory> = {}): EmployeeWorkHistory {
  return {
    id: 5,
    employee_id: 1,
    event_type: 3,
    from_date: '2026-01-01',
    to_date: null,
    company_id: 10,
    company_name: 'DEGO',
    department_id: 20,
    department_name: 'Phòng KD',
    position_id: 30,
    position_label: 'Trưởng phòng',
    decision_no: '',
    decision_date: null,
    note: '',
    applied_at: null,
    file_count: 0,
    is_current: true,
    can_apply: true,
    ...overrides,
  }
}

describe('useEmployeeWorkHistoryEditorDialog', () => {
  it('mặc định đóng, không dòng đang sửa, không seed', () => {
    const { result } = renderHook(() => useEmployeeWorkHistoryEditorDialog())
    expect(result.current.open).toBe(false)
    expect(result.current.editRow).toBeNull()
    expect(result.current.seed).toBeUndefined()
    expect(result.current.requireDecisionNo).toBe(false)
    expect(result.current.createTitle).toBeUndefined()
  })

  it('openCreate() không tham số → mở, editRow null, seed undefined (khuôn «Thêm dòng» cũ)', () => {
    const { result } = renderHook(() => useEmployeeWorkHistoryEditorDialog())
    act(() => result.current.openCreate())

    expect(result.current.open).toBe(true)
    expect(result.current.editRow).toBeNull()
    expect(result.current.seed).toBeUndefined()
    expect(result.current.requireDecisionNo).toBe(false)
    expect(result.current.createTitle).toBeUndefined()
  })

  it('openCreate(seed, {requireDecisionNo, createTitle}) → giữ đúng cả ba (nút «+ Thêm quyết định»)', () => {
    const { result } = renderHook(() => useEmployeeWorkHistoryEditorDialog())
    act(() =>
      result.current.openCreate({ event_type: 3 }, { requireDecisionNo: true, createTitle: 'Thêm quyết định bổ nhiệm' }),
    )

    expect(result.current.open).toBe(true)
    expect(result.current.editRow).toBeNull()
    expect(result.current.seed).toEqual({ event_type: 3 })
    expect(result.current.requireDecisionNo).toBe(true)
    expect(result.current.createTitle).toBe('Thêm quyết định bổ nhiệm')
  })

  it('openEdit(row) → mở, editRow đúng dòng, KHÔNG ép Số QĐ dù trước đó openCreate đã ép', () => {
    const { result } = renderHook(() => useEmployeeWorkHistoryEditorDialog())
    act(() => result.current.openCreate({}, { requireDecisionNo: true, createTitle: 'Thêm quyết định bổ nhiệm' }))
    const target = row({ id: 9 })
    act(() => result.current.openEdit(target))

    expect(result.current.open).toBe(true)
    expect(result.current.editRow).toEqual(target)
    expect(result.current.seed).toBeUndefined()
    //  Sửa dòng CŨ không phải ngữ cảnh "thêm quyết định" — không được kế thừa
    //  cờ ép buộc của lần mở TRƯỚC, kể cả khi dùng lại cùng một state hook.
    expect(result.current.requireDecisionNo).toBe(false)
    expect(result.current.createTitle).toBeUndefined()
  })

  it('onOpenChange(false) đóng hộp mà không đổi editRow/seed (khớp hành vi Dialog đóng bằng Esc/overlay)', () => {
    const { result } = renderHook(() => useEmployeeWorkHistoryEditorDialog())
    const target = row()
    act(() => result.current.openEdit(target))
    act(() => result.current.onOpenChange(false))

    expect(result.current.open).toBe(false)
    expect(result.current.editRow).toEqual(target)
  })
})
