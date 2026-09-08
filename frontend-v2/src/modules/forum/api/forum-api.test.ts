import { describe, expect, it, vi } from 'vitest'

vi.mock('@/core/api', () => ({
  apiGet: vi.fn().mockResolvedValue({}),
  apiPost: vi.fn(),
  apiPut: vi.fn(),
  apiDelete: vi.fn(),
}))

import { apiGet } from '@/core/api'

import { searchForumPosts } from './forum-api'

describe('searchForumPosts (CR-263)', () => {
  it('drops empty filters from the query string but always sends the page', async () => {
    //  Bộ lọc rỗng mà vẫn gửi `q=&company_id=0...` thì URL rác và backend phải
    //  đoán "0 nghĩa là bỏ lọc" ở nhiều chỗ — hợp đồng là KHÔNG gửi mới là bỏ.
    await searchForumPosts({})
    expect(apiGet).toHaveBeenLastCalledWith('/api/forum/posts/search', {
      params: { page: 1 },
    })
  })

  it('passes every set filter through untouched', async () => {
    await searchForumPosts({
      q: '100%',
      author_q: 'NV A',
      company_id: 3,
      dept_id: 7,
      status: 2,
      page: 4,
    })
    expect(apiGet).toHaveBeenLastCalledWith('/api/forum/posts/search', {
      params: { q: '100%', author_q: 'NV A', company_id: 3, dept_id: 7, status: 2, page: 4 },
    })
  })

  it('treats zero-valued filters the same as unset ones', async () => {
    //  0 là giá trị "Mọi công ty/Mọi phòng ban" của ô chọn — lọt xuống URL thì
    //  hai lần tìm giống nhau sinh hai key cache khác nhau.
    await searchForumPosts({ q: '', company_id: 0, dept_id: 0, status: 0, page: 0 })
    expect(apiGet).toHaveBeenLastCalledWith('/api/forum/posts/search', {
      params: { page: 1 },
    })
  })
})
