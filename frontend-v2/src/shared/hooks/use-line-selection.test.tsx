import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { useLineSelection } from './use-line-selection'

// bao-CR-547 — tick nhiều DÒNG trên bảng dòng chứng từ rồi xóa một lần (chỉ form tạo / phiếu Nháp).
interface Line {
  id?: number
  code: string
  locked?: boolean
}

const rowKey = (row: Line, index: number) => row.id ?? `new-${index}`
const unlocked = (row: Line) => !row.locked

const rows: Line[] = [{ id: 1, code: 'A' }, { code: 'B' }, { id: 3, code: 'C', locked: true }]

function setup(initial: Line[] = rows, enabled = true) {
  return renderHook(
    ({ items }) =>
      useLineSelection<Line>({
        rows: items,
        rowKey,
        enabled,
        isSelectable: unlocked,
        unselectableReason: 'Dòng đã khóa',
      }),
    { initialProps: { items: initial } },
  )
}

describe('useLineSelection', () => {
  it('toggles single rows and reports their current indexes', () => {
    const { result } = setup()
    act(() => result.current.selection?.onToggle(rows[1], 1))
    expect(result.current.selectedIndexes).toEqual([1])
    expect(result.current.selection?.isSelected(rows[1], 1)).toBe(true)

    act(() => result.current.selection?.onToggle(rows[1], 1))
    expect(result.current.selectedIndexes).toEqual([])
  })

  it('select-all skips locked rows, and a second click clears everything', () => {
    const { result } = setup()
    act(() => result.current.selection?.onToggleAll())
    expect(result.current.selectedIndexes).toEqual([0, 1])
    expect(result.current.selection?.allSelected).toBe(true)

    act(() => result.current.selection?.onToggleAll())
    expect(result.current.selectedIndexes).toEqual([])
    expect(result.current.selection?.someSelected).toBe(false)
  })

  it('a locked row can never land in the batch even if toggled by hand', () => {
    const { result } = setup()
    act(() => result.current.selection?.onToggle(rows[2], 2))
    expect(result.current.selectedIndexes).toEqual([])
  })

  it('rows that disappear from the array drop out of the batch; clear() empties it', () => {
    const { result, rerender } = setup()
    act(() => result.current.selection?.onToggleAll())
    //  Dòng B (chưa lưu, khóa `new-1`) bị xóa → chỉ còn A.
    rerender({ items: [rows[0], rows[2]] })
    expect(result.current.selectedIndexes).toEqual([0])

    act(() => result.current.clear())
    expect(result.current.selectedIndexes).toEqual([])
  })

  it('is fully off when disabled: no selection object, nothing selected', () => {
    const { result } = setup(rows, false)
    expect(result.current.selection).toBeUndefined()
    expect(result.current.selectedIndexes).toEqual([])
  })

  it('an unsaved row keeps its tick while its index is stable, nothing more', () => {
    //  Khóa dòng chưa lưu là chỉ số: hai dòng mới liên tiếp phải là hai khóa khác nhau.
    const { result } = setup([{ code: 'X' }, { code: 'Y' }])
    act(() => result.current.selection?.onToggle({ code: 'X' }, 0))
    expect(result.current.selectedIndexes).toEqual([0])
  })
})
