import { describe, expect, it } from 'vitest'

import { DOCUMENT_STATUS } from '../types/document-record'
import { buildIncomingSortGetters, documentStatusRank } from './incoming-document-sort'

const TODAY = new Date(2026, 5, 15)   // 15/06/2026

describe('documentStatusRank', () => {
  it('ranks the whole lifecycle in reading order, matching the backend table', () => {
    const rank = (status: number) =>
      documentStatusRank({ status, effective_date: null, expire_date: null }, TODAY)
    const ordered = [
      DOCUMENT_STATUS.draft,
      DOCUMENT_STATUS.returned,
      DOCUMENT_STATUS.submitted,
      DOCUMENT_STATUS.pendingIssue,
      DOCUMENT_STATUS.approved,
      DOCUMENT_STATUS.effective,
      DOCUMENT_STATUS.expired,
      DOCUMENT_STATUS.replaced,
      DOCUMENT_STATUS.revoked,
      DOCUMENT_STATUS.archived,
      DOCUMENT_STATUS.rejected,
    ].map(rank)
    expect(ordered).toEqual([...ordered].sort((a, b) => a - b))
    expect(new Set(ordered).size).toBe(ordered.length)
  })

  it('treats a unit that is effective but past its end date as "Hết hiệu lực", same rank as the expired status', () => {
    const expiredByDate = documentStatusRank(
      { status: DOCUMENT_STATUS.effective, effective_date: '2026-01-01', expire_date: '2026-06-14' },
      TODAY,
    )
    const expiredStatus = documentStatusRank(
      { status: DOCUMENT_STATUS.expired, effective_date: null, expire_date: null },
      TODAY,
    )
    expect(expiredByDate).toBe(expiredStatus)
  })

  it('keeps the boundary days inside the effective window (end date = today, start date = today)', () => {
    const live = documentStatusRank(
      { status: DOCUMENT_STATUS.effective, effective_date: '2026-06-15', expire_date: '2026-06-15' },
      TODAY,
    )
    const plain = documentStatusRank(
      { status: DOCUMENT_STATUS.effective, effective_date: null, expire_date: null },
      TODAY,
    )
    expect(live).toBe(plain)
  })

  it('puts "Chưa hiệu lực" between approved and effective and ignores garbage dates', () => {
    const notYet = documentStatusRank(
      { status: DOCUMENT_STATUS.effective, effective_date: '2026-06-16', expire_date: null },
      TODAY,
    )
    const approved = documentStatusRank({ status: DOCUMENT_STATUS.approved, effective_date: null, expire_date: null }, TODAY)
    const effective = documentStatusRank({ status: DOCUMENT_STATUS.effective, effective_date: null, expire_date: null }, TODAY)
    expect(approved).toBeLessThan(notYet)
    expect(notYet).toBeLessThan(effective)
    expect(
      documentStatusRank(
        { status: DOCUMENT_STATUS.effective, effective_date: 'khong-phai-ngay', expire_date: '' },
        TODAY,
      ),
    ).toBe(effective)
  })

  it('sends an unknown status code to the very end instead of throwing', () => {
    expect(documentStatusRank({ status: 999, effective_date: null, expire_date: null }, TODAY)).toBe(99)
  })
})

describe('buildIncomingSortGetters', () => {
  it('exposes exactly the sortable keys of the incoming table (plus id)', () => {
    expect(Object.keys(buildIncomingSortGetters(TODAY)).sort()).toEqual(
      [
        'company_name',
        'department_name',
        'display_code',
        'doc_type_name',
        'effective_date',
        'id',
        'owner_name',
        'secrecy_level',
        'status',
        'title',
      ].sort(),
    )
  })
})
