import { describe, expect, it } from 'vitest'

import { INSTANCE_STATUS, TASK_STATUS } from '@/modules/approval/types/approval'
import type { ApprovalInstance, ApprovalTask } from '@/modules/approval/types/approval'

import { canWithdrawApproval } from './can-withdraw-approval'

function task(status: number): ApprovalTask {
  return {
    id: 1, instance_id: 7, node_seq: 1, node_name: 'Trưởng phòng', order_no: 1,
    assignee_employee_id: 2, assignee_name: 'A', status, status_label: '',
    due_at: null, decided_at: null,
  } as ApprovalTask
}

function instance(doi: Partial<ApprovalInstance> = {}): ApprovalInstance {
  return {
    id: 7, entity: 'document', entity_id: 1, entity_code: '', entity_title: 'X',
    flow_id: 1, flow_version: 1, flow_name: 'Luồng', status: INSTANCE_STATUS.running,
    status_label: '', current_seq: 1, started_by_name: 'Người trình',
    started_by_employee_id: 9, started_at: null, finished_at: null, finish_reason: '',
    tasks: [task(TASK_STATUS.pending)], ...doi,
  }
}

describe('canWithdrawApproval', () => {
  it('lets the submitter withdraw while nobody has approved yet', () => {
    expect(canWithdrawApproval(instance(), 9)).toBe(true)
  })

  it('hides it from everyone who is not the submitter', () => {
    expect(canWithdrawApproval(instance(), 10)).toBe(false)
  })

  //  Hồ sơ chưa gắn nhân sự: 0 === 0 KHÔNG được coi là «chính người trình»,
  //  không thì mọi tài khoản chưa gắn hồ sơ đều thấy nút trên phiếu của nhau.
  it('never matches an unlinked account (employee id 0 or missing)', () => {
    const unlinked = instance({ started_by_employee_id: 0 })
    expect(canWithdrawApproval(unlinked, 0)).toBe(false)
    expect(canWithdrawApproval(unlinked, undefined)).toBe(false)
    expect(canWithdrawApproval(instance(), null)).toBe(false)
  })

  it('is gone as soon as one approver has signed, even with other steps still pending', () => {
    const signed = instance({ tasks: [task(TASK_STATUS.approved), task(TASK_STATUS.pending)] })
    expect(canWithdrawApproval(signed, 9)).toBe(false)
  })

  //  Phiếu KẸT (không tìm được người duyệt) là lúc người trình cần rút nhất.
  it('still allows withdrawing when the approval is stuck (no approver found)', () => {
    expect(canWithdrawApproval(instance({ status: INSTANCE_STATUS.blocked }), 9)).toBe(true)
  })

  it('is gone once the approval has finished', () => {
    for (const status of [INSTANCE_STATUS.approved, INSTANCE_STATUS.rejected, INSTANCE_STATUS.returned]) {
      expect(canWithdrawApproval(instance({ status }), 9)).toBe(false)
    }
  })

  it('handles a missing instance or task list', () => {
    expect(canWithdrawApproval(null, 9)).toBe(false)
    expect(canWithdrawApproval(undefined, 9)).toBe(false)
    expect(canWithdrawApproval(instance({ tasks: undefined }), 9)).toBe(true)
  })
})
