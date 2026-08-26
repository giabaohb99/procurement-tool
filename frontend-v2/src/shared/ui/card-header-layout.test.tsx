import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Card, CardHeader, CardTitle } from './card'

/**
 * CÁI BẪY: `CardHeader` gốc của shadcn là `grid`. Viết đè `flex-row` KHÔNG kéo
 * nó về flex, vì `grid` (display) và `flex-row` (flex-direction) là HAI NHÓM
 * khác nhau trong `tailwind-merge` — cả hai cùng sống, `display: grid` thắng, và
 * `flex-row` thành vô nghĩa.
 *
 * Hậu quả nhìn thấy được (đo trên trình duyệt 25/08/2026): nút bên phải rơi
 * xuống hàng dưới ở bốn thẻ Văn thư, và ở `StatCard` thì biểu tượng với nhãn
 * xếp chồng lên nhau (y=229 so với y=269).
 *
 * Bài này chỉ ghim đúng một điều: muốn hàng ngang thì phải có `flex`.
 */
/**
 * Tách thành TỪNG LỚP rồi so khớp chính xác.
 *
 * Không dùng regex `\bgrid\b` được: dấu `-` cũng là ranh giới từ nên nó khớp
 * luôn vào `grid-rows-[auto_auto]` — bài kiểm xanh/đỏ sai cả hai chiều.
 */
function coLop(node: Element | null, lop: string): boolean {
  return String(node?.className ?? '').split(/\s+/).includes(lop)
}

function buildHeader(className: string): Element | null {
  const { container } = render(
    <Card>
      <CardHeader className={className}>
        <CardTitle>Bộ đếm</CardTitle>
        <button type="button">Năm 2026</button>
      </CardHeader>
    </Card>,
  )
  return container.querySelector('[data-slot="card-header"]')
}

describe('CardHeader — bẫy grid/flex-row', () => {
  it('chỉ `flex-row` thì KHÔNG thắng được `grid` mặc định', () => {
    const head = buildHeader('flex-row items-center justify-between')
    expect(coLop(head, 'grid')).toBe(true) //  `grid` vẫn còn -> vẫn là lưới
    expect(coLop(head, 'flex')).toBe(false)
  })

  it('thêm `flex` thì `grid` bị gỡ, hàng ngang mới ăn', () => {
    const head = buildHeader('flex flex-row items-center justify-between')
    expect(coLop(head, 'grid')).toBe(false)
    expect(coLop(head, 'flex')).toBe(true)
  })
})
