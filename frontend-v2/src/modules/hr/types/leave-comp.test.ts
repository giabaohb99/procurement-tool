import { describe, expect, it } from 'vitest'

import { LEAVE_STATUS } from './leave'
import {
  LEAVE_COMP_STATUS,
  LEAVE_COMP_STATUS_LABELS,
  getLeaveCompActions,
} from './leave-comp'

const ALL = { write: true, delete: true, approve: true, cancel: true }
const NONE = { write: false, delete: false, approve: false, cancel: false }

describe('LEAVE_COMP_STATUS', () => {
  it('stays in step with the leave-request status codes the shared badge keys on', () => {
    expect(LEAVE_COMP_STATUS).toEqual(LEAVE_STATUS)
  })

  it('has a Vietnamese label for every code', () => {
    for (const code of Object.values(LEAVE_COMP_STATUS)) {
      expect(LEAVE_COMP_STATUS_LABELS[code]).toBeTruthy()
    }
  })
})

describe('getLeaveCompActions', () => {
  it('draft: edit, delete and submit; nothing about decisions', () => {
    const a = getLeaveCompActions({ status: LEAVE_COMP_STATUS.DRAFT, approval_instance_id: 0 }, ALL)
    expect(a).toMatchObject({ edit: true, remove: true, submit: true, cancel: false })
    expect(a.directDecision || a.engineDecision).toBe(false)
  })

  it('returned: still editable and submittable but NOT deletable (only drafts delete)', () => {
    const a = getLeaveCompActions({ status: LEAVE_COMP_STATUS.RETURNED, approval_instance_id: 0 }, ALL)
    expect(a).toMatchObject({ edit: true, submit: true, remove: false })
  })

  it('pending without an engine instance: direct approve/reject + cancel', () => {
    const a = getLeaveCompActions({ status: LEAVE_COMP_STATUS.PENDING, approval_instance_id: 0 }, ALL)
    expect(a).toMatchObject({ directDecision: true, engineDecision: false, cancel: true, edit: false })
  })

  it('pending WITH a running instance: hides direct approve (backend would 400), shows engine buttons', () => {
    const a = getLeaveCompActions({ status: LEAVE_COMP_STATUS.PENDING, approval_instance_id: 7 }, ALL)
    expect(a).toMatchObject({ directDecision: false, engineDecision: true })
  })

  it('engine buttons do not depend on the approve permission (task ownership decides)', () => {
    const a = getLeaveCompActions({ status: LEAVE_COMP_STATUS.PENDING, approval_instance_id: 7 }, NONE)
    expect(a.engineDecision).toBe(true)
    expect(a.directDecision).toBe(false)
  })

  it('approved: only cancel remains', () => {
    const a = getLeaveCompActions({ status: LEAVE_COMP_STATUS.APPROVED, approval_instance_id: 0 }, ALL)
    expect(a).toEqual({
      edit: false,
      remove: false,
      submit: false,
      directDecision: false,
      engineDecision: false,
      cancel: true,
    })
  })

  it.each([LEAVE_COMP_STATUS.REJECTED, LEAVE_COMP_STATUS.CANCELLED, 99, 0])(
    'terminal or unknown status %s offers nothing',
    (status) => {
      const a = getLeaveCompActions({ status, approval_instance_id: 0 }, ALL)
      expect(Object.values(a).some(Boolean)).toBe(false)
    },
  )

  it('no permissions: nothing on a draft; undefined request: nothing', () => {
    const a = getLeaveCompActions({ status: LEAVE_COMP_STATUS.DRAFT, approval_instance_id: 0 }, NONE)
    expect(Object.values(a).some(Boolean)).toBe(false)
    expect(Object.values(getLeaveCompActions(undefined, ALL)).some(Boolean)).toBe(false)
  })
})
