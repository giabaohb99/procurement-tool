import { describe, expect, it } from 'vitest'

import type { WorkBoard } from '../types/work'
import { anchorInsideLoaded, boardModeFor, remainingCounts, remainingOf } from './board-paging'

describe('boardModeFor — bao-CR-483', () => {
  const base = { view: 'kanban', keyword: '', sort: 'manual', hasConditions: false }

  it('kanban / danh sách, không lọc, sắp theo tay → chế độ nhẹ', () => {
    expect(boardModeFor(base)).toBe('light')
    expect(boardModeFor({ ...base, view: 'list' })).toBe('light')
  })

  it('Gantt, từ khóa, sắp xếp khác tay hay bộ lọc → cần đủ dữ liệu → đầy đủ', () => {
    expect(boardModeFor({ ...base, view: 'gantt' })).toBe('full')
    expect(boardModeFor({ ...base, keyword: ' a ' })).toBe('full')
    expect(boardModeFor({ ...base, sort: 'due' })).toBe('full')
    expect(boardModeFor({ ...base, hasConditions: true })).toBe('full')
  })
})

describe('anchorInsideLoaded / remainingOf — bao-CR-483', () => {
  const board = {
    remaining: { 7: { count: 120, next_task_id: 900 }, 0: { count: 2, next_task_id: 55 } },
  } as unknown as WorkBoard

  it('thả xuống cuối cột đang tải dở → neo trước thẻ chưa tải đầu tiên', () => {
    expect(anchorInsideLoaded({ sectionId: 7, beforeTaskId: null }, board)).toEqual({
      sectionId: 7,
      beforeTaskId: 900,
    })
  })

  it('cột đã tải hết hoặc thả giữa cột thì giữ nguyên mốc', () => {
    expect(anchorInsideLoaded({ sectionId: 8, beforeTaskId: null }, board)).toEqual({
      sectionId: 8,
      beforeTaskId: null,
    })
    expect(anchorInsideLoaded({ sectionId: 7, beforeTaskId: 12 }, board)).toEqual({
      sectionId: 7,
      beforeTaskId: 12,
    })
    expect(anchorInsideLoaded({ sectionId: 7, beforeTaskId: null }, undefined).beforeTaskId).toBeNull()
  })

  it('remainingCounts: rút gọn về số đếm theo cột; bảng đủ thì undefined', () => {
    expect(remainingCounts(board)).toEqual({ 7: 120, 0: 2 })
    expect(remainingCounts({ remaining: {} } as unknown as WorkBoard)).toBeUndefined()
    expect(remainingCounts(undefined)).toBeUndefined()
  })

  it('remainingOf: cột null là «Chưa phân cột» (khóa 0); không có = 0', () => {
    expect(remainingOf(board, 7)).toBe(120)
    expect(remainingOf(board, null)).toBe(2)
    expect(remainingOf(board, 99)).toBe(0)
    expect(remainingOf(undefined, 7)).toBe(0)
  })
})
