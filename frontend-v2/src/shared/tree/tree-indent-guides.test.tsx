import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { TreeIndentGuides } from './tree-indent-guides'

function renderGuides(depth: number, bold = false) {
  const { container } = render(
    <div role="treeitem" aria-selected={false}>
      <TreeIndentGuides depth={depth} bold={bold} />
    </div>,
  )
  const row = container.firstElementChild as HTMLElement
  const guide = row.querySelector<HTMLElement>('[data-tree-indent-guide]')
  return { row, guide }
}

describe('TreeIndentGuides', () => {
  it('depth 0 or negative draws nothing', () => {
    expect(renderGuides(0).row.childElementCount).toBe(0)
    expect(renderGuides(-3).row.childElementCount).toBe(0)
  })

  it('draws a single element whatever the depth — deep trees must not explode the DOM', () => {
    //  Lỗi 26/09/2026: mỗi cấp 2 phần tử DOM, cây 100 cấp ~10.000 phần tử,
    //  mỗi phím gõ vào ô lọc cây khóa giao diện 200-560ms.
    const { row } = renderGuides(100)
    expect(row.querySelectorAll('*').length).toBeLessThanOrEqual(2)
  })

  it('indents one 16px step per level up to the cap', () => {
    const { guide } = renderGuides(5)
    expect(guide?.getAttribute('data-tree-indent-levels')).toBe('5')
    expect(guide?.style.width).toBe('80px')
  })

  it('stops indenting at 6 levels and shows how many levels are hidden', () => {
    //  6 đo trên khung cây mặc định 288px — trần 12 vẫn ép tên còn 0 ký tự.
    const { row, guide } = renderGuides(100)
    expect(guide?.getAttribute('data-tree-indent-levels')).toBe('6')
    expect(guide?.style.width).toBe('96px')
    expect(row.textContent).toBe('+94')
  })

  it('exactly at the cap shows no hidden-level marker', () => {
    const { row, guide } = renderGuides(6)
    expect(guide?.getAttribute('data-tree-indent-levels')).toBe('6')
    expect(row.textContent).toBe('')
    expect(renderGuides(7).row.textContent).toBe('+1')
  })
})
