import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { useClearUrlParams, useUrlParamState } from './use-url-param-state'

/** Màn giả có hai nút xóa: kiểu cũ (gọi từng setter) và kiểu mới (một lượt). */
function FakePage({ advanced = false }: { advanced?: boolean }) {
  const [, setStatus] = useUrlParamState('status', 'all')
  const [, setCompany] = useUrlParamState('company_id', 'all')
  const [, setFrom] = useUrlParamState('date_from', '')
  const clearUrlParams = useClearUrlParams()
  const location = useLocation()
  return (
    <>
      <output>{location.search}</output>
      <button
        type="button"
        onClick={() => {
          setStatus('all')
          setCompany('all')
          setFrom('')
        }}
      >
        Xóa kiểu cũ
      </button>
      <button
        type="button"
        onClick={() => clearUrlParams(['status', 'company_id', 'date_from'], { advanced })}
      >
        Xóa lọc
      </button>
    </>
  )
}

function build(url: string, advanced = false) {
  return render(
    <MemoryRouter initialEntries={[url]}>
      <FakePage advanced={advanced} />
    </MemoryRouter>,
  )
}

describe('useUrlParamState — gọi nhiều setter trong MỘT lần bấm', () => {
  it('loses every change but the last — the trap useClearUrlParams exists for', () => {
    //  Bài kiểm này GHI LẠI hành vi của react-router chứ không phải mong muốn: mỗi
    //  setter dựng URL mới từ URL LÚC DỰNG, nên lần sau đè lần trước. Một ngày nó
    //  xanh ngược (router đổi cách) thì mới được bỏ `useClearUrlParams`.
    build('/x?status=a&company_id=1&date_from=2026-10-01')
    fireEvent.click(screen.getByRole('button', { name: 'Xóa kiểu cũ' }))

    expect(screen.getByRole('status').textContent).toBe('?status=a&company_id=1')
  })
})

describe('useClearUrlParams', () => {
  it('clears every listed filter in one write', () => {
    build('/x?status=a&company_id=1&date_from=2026-10-01')
    fireEvent.click(screen.getByRole('button', { name: 'Xóa lọc' }))

    expect(screen.getByRole('status').textContent).toBe('')
  })

  it('keeps the keyword, the sort and anything else it was not told to clear', () => {
    build('/x?q=bao&sort_by=id&sort_dir=desc&status=a&tab=2')
    fireEvent.click(screen.getByRole('button', { name: 'Xóa lọc' }))

    expect(screen.getByRole('status').textContent).toBe('?q=bao&sort_by=id&sort_dir=desc&tab=2')
  })

  it('leaves advanced conditions alone unless asked', () => {
    build('/x?status=a&code__contains=A&conjunction=or')
    fireEvent.click(screen.getByRole('button', { name: 'Xóa lọc' }))

    expect(screen.getByRole('status').textContent).toBe('?code__contains=A&conjunction=or')
  })

  it('also clears advanced conditions and the conjunction when asked', () => {
    build('/x?q=bao&status=a&code__contains=A&purpose__contains=B&conjunction=or', true)
    fireEvent.click(screen.getByRole('button', { name: 'Xóa lọc' }))

    expect(screen.getByRole('status').textContent).toBe('?q=bao')
  })

  it('does nothing harmful on a URL that is already clean', () => {
    build('/x')
    fireEvent.click(screen.getByRole('button', { name: 'Xóa lọc' }))

    expect(screen.getByRole('status').textContent).toBe('')
  })
})
