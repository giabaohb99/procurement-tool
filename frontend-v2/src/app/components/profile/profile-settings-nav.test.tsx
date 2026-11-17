import { fireEvent, render, screen, within } from '@testing-library/react'
import { Bell, CheckSquare, User } from 'lucide-react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ProfileGroupDefinition } from './profile-sections'
import { ProfileSettingsNav } from './profile-settings-nav'

const GROUPS = [
  {
    key: 'profile',
    label: 'Hồ sơ',
    sections: [{ key: 'info', label: 'Thông tin cá nhân', icon: User }],
  },
  {
    key: 'work',
    label: 'Việc của tôi',
    sections: [
      { key: 'tasks', label: 'Việc cần làm', icon: CheckSquare },
      { key: 'notifications', label: 'Thông báo', icon: Bell },
    ],
  },
] as unknown as ProfileGroupDefinition[]

function renderNav(active: 'info' | 'tasks' = 'info') {
  return render(
    <ProfileSettingsNav
      groups={GROUPS}
      active={active}
      onSelect={vi.fn()}
      badges={{ tasks: { count: 3, variant: 'destructive' }, notifications: { count: 2, variant: 'destructive' } }}
    />,
  )
}

const nav = () => screen.getByRole('navigation', { name: 'Các mục trang cá nhân' })

describe('ProfileSettingsNav — gập nhóm (duoc-CR-774)', () => {
  beforeEach(() => localStorage.clear())

  it('collapses a group from its heading and shows the summed badge so pending work stays visible', () => {
    renderNav()
    const heading = within(nav()).getByRole('button', { name: /Việc của tôi/ })
    expect(heading).toHaveAttribute('aria-expanded', 'true')

    fireEvent.click(heading)
    expect(heading).toHaveAttribute('aria-expanded', 'false')
    expect(within(nav()).getByRole('button', { name: /Việc cần làm/, hidden: true })).not.toBeVisible()
    expect(heading).toHaveTextContent('5')
  })

  it('remembers a collapsed group after the page is opened again', () => {
    const { unmount } = renderNav()
    fireEvent.click(within(nav()).getByRole('button', { name: /Việc của tôi/ }))
    unmount()

    renderNav()
    expect(within(nav()).getByRole('button', { name: /Việc của tôi/ })).toHaveAttribute('aria-expanded', 'false')
  })

  it('keeps the group holding the open section expanded even if it was collapsed before', () => {
    //  Mở trang bằng ?tab=tasks vào nhóm đã gập: nhóm vẫn phải mở, không thì thanh bên không chỉ ra mình đang ở đâu.
    localStorage.setItem('erp.section.me.nav.work', '0')
    renderNav('tasks')
    const heading = within(nav()).getByRole('button', { name: /Việc của tôi/ })
    expect(heading).toHaveAttribute('aria-expanded', 'true')
    expect(heading).toBeDisabled()
    expect(within(nav()).getByRole('button', { name: /Việc cần làm/ })).toBeVisible()
  })
})
