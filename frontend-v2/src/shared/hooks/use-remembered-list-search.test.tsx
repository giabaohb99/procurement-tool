import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import { useRememberedListSearch } from './use-remembered-list-search'

/** Màn giả: khôi phục thì đổi hướng, không thì in chuỗi lọc đang có. */
function FakeListPage() {
  const restoreSearch = useRememberedListSearch('test.list')
  const location = useLocation()
  const navigate = useNavigate()
  if (restoreSearch) return <Navigate replace to={{ search: restoreSearch }} />
  return (
    <>
      <output>search={location.search}</output>
      {/*  Giả nút *Xóa lọc*: về đúng màn, không còn tham số nào. */}
      <button type="button" onClick={() => navigate('/list', { replace: true })}>
        Xóa lọc
      </button>
    </>
  )
}

function build(url: string) {
  return render(
    <MemoryRouter initialEntries={[url]}>
      <FakeListPage />
    </MemoryRouter>,
  )
}

function signIn(id: number) {
  useAuthStore.setState({ user: { id, email: `u${id}@dego.vn`, full_name: `U${id}`, permissions: {} } })
}

beforeEach(() => {
  sessionStorage.clear()
  signIn(1)
})

afterEach(() => {
  useAuthStore.setState({ user: null })
})

describe('useRememberedListSearch', () => {
  it('brings back the last filters when the screen is opened again from the menu', () => {
    const first = build('/list?status=approved&is_urgent=true')
    first.unmount()

    build('/list')

    expect(screen.getByRole('status')).toHaveTextContent('search=?status=approved&is_urgent=true')
  })

  it('lets the URL win when the link already carries filters', () => {
    //  Link trong thông báo / link đồng nghiệp gửi phải mở ĐÚNG thứ nó chỉ, không bị bộ
    //  lọc cũ của người nhận đè lên.
    build('/list?status=approved').unmount()

    build('/list?status=draft')

    expect(screen.getByRole('status')).toHaveTextContent('search=?status=draft')
  })

  it('forgets the filters once they are cleared, so the next visit opens clean', () => {
    const first = build('/list?status=approved')
    fireEvent.click(screen.getByRole('button', { name: 'Xóa lọc' }))
    first.unmount()

    //  Mở lại màn: không được hiện lại `status=approved` vừa xóa.
    build('/list')
    expect(screen.getByRole('status')).toHaveTextContent(/^search=$/)
  })

  it('does not restore the filters a previous account left in the same tab', () => {
    build('/list?assignee=NSU209').unmount()

    signIn(2)
    build('/list')

    expect(screen.getByRole('status')).toHaveTextContent(/^search=$/)
  })

  it('remembers nothing for a signed-out visitor', () => {
    useAuthStore.setState({ user: null })
    build('/list?status=approved').unmount()

    build('/list')

    expect(screen.getByRole('status')).toHaveTextContent(/^search=$/)
    expect(sessionStorage.length).toBe(0)
  })

  it('keeps the screen usable when the stored value is broken or storage throws', () => {
    sessionStorage.setItem('list-search:1:test.list', '?')
    build('/list')
    expect(screen.getByRole('status')).toHaveTextContent(/^search=$/)
  })

  it('restores only once — clearing after a restore must not bounce back to the old filters', () => {
    //  Lỗi dễ mắc: điều kiện "URL trống + có bản nhớ" đúng lại ngay khi người dùng
    //  bấm Xóa lọc, màn đổi hướng về bộ lọc cũ và nút Xóa lọc coi như hỏng.
    build('/list?status=approved').unmount()
    build('/list')
    expect(screen.getByRole('status')).toHaveTextContent('search=?status=approved')

    fireEvent.click(screen.getByRole('button', { name: 'Xóa lọc' }))

    expect(screen.getByRole('status')).toHaveTextContent(/^search=$/)
  })
})
