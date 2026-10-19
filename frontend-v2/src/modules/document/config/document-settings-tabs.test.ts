import { describe, expect, it } from 'vitest'

import type { PermissionEntity } from '@/core/authorization/permission-types'
import { LABOR_CONTRACT_KIND, resolveSettingsView } from './document-settings-tabs'

const TABS = [
  { value: 'types', entity: 'doc_type' as PermissionEntity },
  { value: 'templates', entity: 'doc_template' as PermissionEntity },
  { value: 'security-levels', entity: 'security_level' as PermissionEntity },
  { value: 'partners', entity: 'external_party' as PermissionEntity },
]

/** `read` = khóa đọc được; `manage` = khóa có create/write/delete. */
function view(read: PermissionEntity[], manage: PermissionEntity[], tab = 'types', kind = '') {
  return resolveSettingsView(
    TABS,
    (e, a) => (a === 'read' ? read.includes(e) || manage.includes(e) : manage.includes(e)),
    (e) => manage.includes(e),
    tab,
    kind,
  )
}

const DOC_READ: PermissionEntity[] = ['doc_type', 'doc_template', 'security_level', 'external_party']

describe('resolveSettingsView', () => {
  it('Nhân sự thuần: một tab thư viện mẫu, ép mục HĐLĐ dù ?tab=types', () => {
    const v = view(DOC_READ, ['labor_contract_template'], 'types')
    expect(v.visible).toEqual(['templates'])
    expect(v.current).toBe('templates')
    expect(v.laborContract).toBe(true)
    expect(v.showKindSwitch).toBe(false)
  })

  it('văn thư thiếu khóa HĐLĐ: bốn tab, ?kind=labor-contract bị bỏ qua', () => {
    const v = view(DOC_READ, ['doc_template'], 'templates', LABOR_CONTRACT_KIND)
    expect(v.visible).toHaveLength(4)
    expect(v.laborContract).toBe(false)
    expect(v.showKindSwitch).toBe(false)
  })

  it('có cả hai: bốn tab, giữ ?kind, có công tắc', () => {
    const v = view([...DOC_READ, 'labor_contract_template'], ['doc_template', 'labor_contract_template'], 'templates', LABOR_CONTRACT_KIND)
    expect(v.visible).toHaveLength(4)
    expect(v.laborContract).toBe(true)
    expect(v.showKindSwitch).toBe(true)
  })

  it('có cả hai nhưng không ?kind: hiện thư viện thường + công tắc', () => {
    const v = view([...DOC_READ, 'labor_contract_template'], ['doc_template', 'labor_contract_template'], 'templates')
    expect(v.laborContract).toBe(false)
    expect(v.showKindSwitch).toBe(true)
  })

  it('không khóa nào: không tab', () => {
    const v = view([], [])
    expect(v.current).toBeUndefined()
  })
})
