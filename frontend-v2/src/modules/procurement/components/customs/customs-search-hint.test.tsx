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
    // Từ khóa in đậm nên câu tách thành nhiều nút chữ: khớp cả dòng qua textContent.
    expect(screen.getByText('3,6%', { selector: 'strong' }).parentElement).toHaveTextContent(
      'Có 3,6%: 3.6 · 3,6 · 36G/L · 36 G/L',
    )
    expect(screen.getByText(/^Không có/, { selector: 'span' })).toHaveTextContent('Không có TC: TC')
  })

  it('caps a long synonym list', () => {
    render(
      <CustomsSearchHint
        query="x"
        explain={{ include: [{ term: 'X', matches: ['a', 'b', 'c', 'd', 'e', 'f'] }], exclude: [] }}
      />,
    )
    expect(screen.getByText(/^Có/, { selector: 'span' })).toHaveTextContent('Có X: a · b · c · d · +2')
  })
})
