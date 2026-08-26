import { describe, expect, it } from 'vitest'

import {
  oversizedCount,
  splitBlocksIntoPages,
  type PrintBlock,
} from './split-blocks-into-pages'

const PAGE = 1000

function block(height: number, spaceBefore = 8, html = `<p>${height}</p>`): PrintBlock {
  return { html, height, spaceBefore }
}

describe('splitBlocksIntoPages', () => {
  it('gom hết vào một trang khi nội dung còn chỗ', () => {
    const pages = splitBlocksIntoPages([block(300), block(300), block(300)], PAGE)

    expect(pages).toHaveLength(1)
    expect(pages[0]).toHaveLength(3)
  })

  it('đẩy khối không còn chỗ sang trang sau, không cắt đôi nó', () => {
    const pages = splitBlocksIntoPages([block(600), block(500)], PAGE)

    expect(pages).toHaveLength(2)
    expect(pages[0]).toHaveLength(1)
    expect(pages[1]).toHaveLength(1)
  })

  it('không tính khe cách cho khối nằm đầu trang', () => {
    //  Hai khối 500 + khe 8: nếu tính khe cho khối đầu trang thì tổng thành
    //  1008 và trang thứ hai mọc ra vô cớ.
    const pages = splitBlocksIntoPages([block(500, 8), block(492, 8)], PAGE)

    expect(pages).toHaveLength(1)
  })

  it('khối cao hơn cả trang thì đứng riêng một tờ', () => {
    const pages = splitBlocksIntoPages([block(200), block(1400), block(200)], PAGE)

    expect(pages).toHaveLength(3)
    expect(pages[1][0].height).toBe(1400)
  })

  it('không có khối nào thì không sinh trang trắng', () => {
    expect(splitBlocksIntoPages([], PAGE)).toEqual([])
  })

  it('chiều cao trang vô lý thì dồn hết vào một trang thay vì lặp vô tận', () => {
    expect(splitBlocksIntoPages([block(100), block(100)], 0)).toHaveLength(1)
  })
})

describe('oversizedCount', () => {
  it('đếm đúng số khối sẽ tràn khi in', () => {
    expect(oversizedCount([block(200), block(1400), block(1200)], PAGE)).toBe(2)
  })
})
