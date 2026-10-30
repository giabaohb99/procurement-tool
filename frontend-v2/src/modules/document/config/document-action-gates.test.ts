import { describe, expect, it } from 'vitest'

import { resolveDocumentActionGates } from './document-action-gates'

const everything = () => true

describe('resolveDocumentActionGates', () => {
  it('văn bản thường: theo backend và quyền vai trò', () => {
    const g = resolveDocumentActionGates({ read: true, write: true, delete: true }, everything, false)
    expect(g).toMatchObject({ isArchive: false, canApprove: true, canCreate: true, canWrite: true, canDelete: true })
    expect(g.showSharingAndWorkflow).toBe(true)
  })

  it('bản lưu trữ, người ghi HĐLĐ: sửa được nhưng không duyệt / sao chép / chia sẻ / xóa', () => {
    const g = resolveDocumentActionGates({ read: true, write: true, delete: false, is_archive: true }, everything, false)
    expect(g.canWrite).toBe(true)
    expect(g.canDelete).toBe(false)
    expect(g.canApprove).toBe(false)
    expect(g.canCreate).toBe(false)
    expect(g.showSharingAndWorkflow).toBe(false)
  })

  it('bản lưu trữ, người chỉ đọc HĐLĐ: không sửa được', () => {
    const g = resolveDocumentActionGates({ read: true, write: false, delete: false, is_archive: true }, everything, false)
    expect(g.canWrite).toBe(false)
    expect(g.showSharingAndWorkflow).toBe(false)
  })

  it('mở bằng liên kết chỉ-đọc: tắt hết', () => {
    const g = resolveDocumentActionGates({ read: true, write: true, delete: true }, everything, true)
    expect(g).toMatchObject({ canWrite: false, canDelete: false, canApprove: false, canCreate: false })
  })

  //  duoc-CR-659: nút "Ban hành" của bản lưu trữ = ký HĐ gốc — chỉ khi backend bật cờ VÀ có id HĐ.
  it('bản lưu trữ được ban hành: trả id HĐ gốc để gọi đường ký', () => {
    const g = resolveDocumentActionGates(
      { read: true, write: true, delete: false, is_archive: true, archive_contract_id: 14, can_issue_archive: true },
      everything,
      false,
    )
    expect(g.issueArchiveContractId).toBe(14)
  })

  it('không bày nút Ban hành khi backend tắt cờ, thiếu id HĐ, mở bằng liên kết hay văn bản thường', () => {
    const base = { read: true, write: true, delete: false }
    expect(
      resolveDocumentActionGates({ ...base, is_archive: true, archive_contract_id: 14, can_issue_archive: false }, everything, false)
        .issueArchiveContractId,
    ).toBe(0)
    expect(
      resolveDocumentActionGates({ ...base, is_archive: true, can_issue_archive: true }, everything, false).issueArchiveContractId,
    ).toBe(0)
    expect(
      resolveDocumentActionGates({ ...base, is_archive: true, archive_contract_id: 14, can_issue_archive: true }, everything, true)
        .issueArchiveContractId,
    ).toBe(0)
    expect(
      resolveDocumentActionGates({ ...base, archive_contract_id: 14, can_issue_archive: true }, everything, false)
        .issueArchiveContractId,
    ).toBe(0)
  })

  it('chưa tải quyền: mọi cờ ghi tắt', () => {
    expect(resolveDocumentActionGates(undefined, everything, false)).toMatchObject({ canWrite: false, isArchive: false })
  })
})
