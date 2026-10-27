import { describe, expect, it } from 'vitest'

import { buildDrilldownParams } from './build-drilldown-params'

const BASE = { preset: 'this_month', compare: 'previous', group_by: 'department', department_id: '7' }

describe('buildDrilldownParams', () => {
  it('keeps every page filter and asks for the whole list from a KPI card', () => {
    expect(buildDrilldownParams(BASE, { metric: 'expiring_30', group: null })).toEqual({
      preset: 'this_month',
      compare: 'previous',
      department_id: '7',
      metric: 'expiring_30',
      group_by: 'none',
    })
  })

  it('sends the group of the clicked row, including the empty «(Chưa gắn)» key', () => {
    const params = buildDrilldownParams(
      { ...BASE, group_key: 'stale' },
      { metric: 'active', group: { by: 'company', key: '', dimensionLabel: 'Công ty', label: '(Chưa gắn)' } },
    )
    expect(params.group_by).toBe('company')
    //  `""` phải CÒN trong tham số — mất khóa là backend trả cả danh sách.
    expect(params).toHaveProperty('group_key', '')
  })

  it('never leaks a stale group_key into a whole-list request', () => {
    const params = buildDrilldownParams({ ...BASE, group_key: '12' }, { metric: 'active', group: null })
    expect(params).not.toHaveProperty('group_key')
  })
})
