// bao-CR-495 — dòng giải thích dưới ô tìm tên hàng.
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { CustomsSearchHint } from './customs-search-hint'

describe('CustomsSearchHint', () => {
  it('shows the syntax tip when the box is empty', () => {
    render(<CustomsSearchHint query="" />)
    expect(screen.getByText(/dấu trừ trước từ cần loại/i)).toBeInTheDocument()
  })

  it('lists include and exclude terms with their matched spellings', () => {
    render(
      <CustomsSearchHint
        query="abamectin 3,6% -TC"
        explain={{
          include: [
            { term: 'ABAMECTIN', matches: ['ABAMECTIN'] },
            { term: '3,6%', matches: ['3.6', '3,6', '36G/L', '36 G/L'] },
          ],
          exclude: [{ term: 'TC', matches: ['TC'] }],
        }}
      />,
    )
    expect(screen.getByText('Có «3,6%»: 3.6 · 3,6 · 36G/L · 36 G/L')).toBeInTheDocument()
    expect(screen.getByText('Không có «TC»: TC')).toBeInTheDocument()
  })

  it('caps a long synonym list', () => {
    render(
      <CustomsSearchHint
        query="x"
        explain={{ include: [{ term: 'X', matches: ['a', 'b', 'c', 'd', 'e', 'f'] }], exclude: [] }}
      />,
    )
    expect(screen.getByText('Có «X»: a · b · c · d · +2')).toBeInTheDocument()
  })
})
