import { describe, expect, it } from 'vitest'

import { buildCompanyChangeChoice } from './company-change-concurrent-choice'

describe('buildCompanyChangeChoice (duoc-CR-756)', () => {
  it('maps the one checkbox straight onto keep_old_company_concurrent', () => {
    expect(buildCompanyChangeChoice(true)).toEqual({ keep_old_company_concurrent: true })
    expect(buildCompanyChangeChoice(false)).toEqual({ keep_old_company_concurrent: false })
  })

  it('never carries the CR-755 keys the backend has dropped (extra=forbid would 422)', () => {
    const body = buildCompanyChangeChoice(true)
    expect(Object.keys(body)).toEqual(['keep_old_company_concurrent'])
  })
})
