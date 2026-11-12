import { describe, expect, it } from 'vitest'

import type { EmployeeConcurrent } from '../types/employee-concurrent'
import { buildCompanyChangeChoice } from './company-change-concurrent-choice'

const rows = [{ id: 7 }, { id: 8 }, { id: 9 }] as EmployeeConcurrent[]

describe('buildCompanyChangeChoice', () => {
  it('nothing ticked → end all rows, no keep list', () => {
    expect(buildCompanyChangeChoice(rows, new Set())).toEqual({ end_old_company_concurrent: true, keep_concurrent_ids: [] })
  })

  it('some ticked → end the rest and send exactly the kept ids', () => {
    expect(buildCompanyChangeChoice(rows, new Set([8]))).toEqual({ end_old_company_concurrent: true, keep_concurrent_ids: [8] })
  })

  it('all ticked → send false (keep everything) instead of a full keep list', () => {
    expect(buildCompanyChangeChoice(rows, new Set([7, 8, 9]))).toEqual({
      end_old_company_concurrent: false,
      keep_concurrent_ids: [],
    })
  })

  it('stale ids in the tick set that are not in the rows are never sent', () => {
    expect(buildCompanyChangeChoice(rows, new Set([8, 999]))).toEqual({
      end_old_company_concurrent: true,
      keep_concurrent_ids: [8],
    })
  })

  it('empty row list → end (nothing to keep), never "keep all" by vacuous truth', () => {
    expect(buildCompanyChangeChoice([], new Set())).toEqual({ end_old_company_concurrent: true, keep_concurrent_ids: [] })
  })
})
