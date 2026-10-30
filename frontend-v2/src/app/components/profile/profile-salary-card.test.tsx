import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import type { Employee } from '@/modules/hr/types/employee'
import { ProfileSalaryCard } from './profile-salary-card'

const BASE = { id: 7, code: 'NSU007', full_name: 'Trần Thị B' } as Employee

describe('ProfileSalaryCard', () => {
  it('hides every number by default so a shared screen does not leak the salary', () => {
    render(<ProfileSalaryCard employee={{ ...BASE, salary_monthly: 15_000_000, allowance_monthly: 1_000_000 }} />)
    expect(screen.getAllByText('••••')).toHaveLength(3)
    expect(screen.queryByText('15.000.000')).not.toBeInTheDocument()
    expect(screen.queryByText('16.000.000')).not.toBeInTheDocument()
  })

  it('shows salary, allowance and their total after pressing the eye, and hides them again', async () => {
    render(<ProfileSalaryCard employee={{ ...BASE, salary_monthly: 15_000_000, allowance_monthly: 1_000_000 }} />)
    await userEvent.click(screen.getByRole('button', { name: 'Hiện số lương' }))
    expect(screen.getByText('15.000.000')).toBeInTheDocument()
    expect(screen.getByText('1.000.000')).toBeInTheDocument()
    expect(screen.getByText('16.000.000')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Ẩn số lương' }))
    expect(screen.getAllByText('••••')).toHaveLength(3)
  })

  it('counts an allowance-only record as entered (total = allowance)', async () => {
    render(<ProfileSalaryCard employee={{ ...BASE, salary_monthly: 0, allowance_monthly: 700_000 }} />)
    await userEvent.click(screen.getByRole('button', { name: 'Hiện số lương' }))
    expect(screen.getAllByText('700.000')).toHaveLength(2)
  })

  it.each([
    ['both zero', { salary_monthly: 0, allowance_monthly: 0 }],
    ['both null', { salary_monthly: null, allowance_monthly: null }],
    ['left out by the server', {}],
  ])('says HR has not entered a salary when %s, with no eye button', (_case, over) => {
    render(<ProfileSalaryCard employee={{ ...BASE, ...over }} />)
    expect(screen.getByText('Phòng Nhân sự chưa nhập lương cho bạn.')).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
