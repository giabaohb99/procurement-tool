import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { FORUM_BODY_FORMAT } from '../types/forum-post'
import { PostBody } from './post-body'

//  Hình dạng HTML thật sau khi backend sanitize bài dán từ báo (bao-CR-275):
//  data-editor-image đã bị lột, chỉ còn <figure> trần + <figcaption> chữ trơn.
const RICH_BODY =
  '<p>mở bài</p>' +
  '<figure><img src="https://example.com/a.png" alt="Ảnh một"><figcaption>Chú thích một</figcaption></figure>' +
  '<figure><img src="https://example.com/b.png" alt="Ảnh hai"><figcaption>Chú thích hai</figcaption></figure>'

describe('PostBody', () => {
  it('keeps the pasted figcaption text visible in the rich body', () => {
    render(<PostBody body={RICH_BODY} format={FORUM_BODY_FORMAT.richHtml} detail />)
    expect(screen.getByText('Chú thích một')).toBeInTheDocument()
    expect(screen.getByText('Chú thích hai')).toBeInTheDocument()
  })

  it('opens the shared lightbox at the exact in-body image clicked', async () => {
    render(<PostBody body={RICH_BODY} format={FORUM_BODY_FORMAT.richHtml} detail />)
    await userEvent.click(screen.getByAltText('Ảnh hai'))
    //  Bộ đếm 2/2 = đang đứng ở ảnh THỨ HAI — bấm ảnh nào mở đúng ảnh đó,
    //  không phải lúc nào cũng nhảy về ảnh đầu (lỗi dễ mắc khi ủy quyền click).
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('2/2')).toBeInTheDocument()
  })

  it('leaves plain-text clicks alone instead of popping the lightbox', async () => {
    render(<PostBody body={RICH_BODY} format={FORUM_BODY_FORMAT.richHtml} detail />)
    await userEvent.click(screen.getByText('mở bài'))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
