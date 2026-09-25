import { render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { EFFECT, SUBJECT_KIND, type DocumentAccess } from '../types/document-access'
import { DocumentShareAccessList } from './document-share-access-list'

function row(overrides: Partial<DocumentAccess>): DocumentAccess {
  return {
    id: 1,
    document_id: 17,
    subject_kind: SUBJECT_KIND.employee,
    subject_kind_label: 'Người',
    subject_id: 1,
    subject_name: 'Người A',
    effect: EFFECT.allow,
    effect_label: 'Cho phép',
    can_read: true,
    can_write: false,
    can_delete: false,
    valid_from: null,
    valid_to: null,
    reason: '',
    is_active: true,
    revoked_at: '',
    revoked_by_name: '',
    revoke_reason: '',
    granted_by_name: 'Dego Admin',
    created_at: '2026-09-25T00:00:00Z',
    ...overrides,
  }
}

function renderList(rows: DocumentAccess[], canWrite = true) {
  render(
    <DocumentShareAccessList rows={rows} canWrite={canWrite} onEdit={vi.fn()} onRevoke={vi.fn()} />,
  )
}

describe('DocumentShareAccessList', () => {
  it('says plainly that nobody has a named grant instead of rendering an empty box', () => {
    renderList([])
    expect(screen.getByText('Chưa chia riêng cho ai')).toBeInTheDocument()
  })

  it('a list holding only revoked rows is still "nobody" — history belongs on the detail page', () => {
    renderList([row({ is_active: false })])
    expect(screen.getByText('Chưa chia riêng cho ai')).toBeInTheDocument()
    expect(screen.queryByText('Người A')).not.toBeInTheDocument()
  })

  it('puts deny rows first even when granted later, because deny beats every allow', () => {
    renderList([
      row({ id: 1, subject_name: 'Được xem', can_write: true }),
      row({ id: 2, subject_name: 'Bị chặn', effect: EFFECT.deny }),
    ])
    const items = screen.getAllByRole('listitem')
    expect(within(items[0]).getByText('Bị chặn')).toBeInTheDocument()
    expect(within(items[0]).getByText('Chặn')).toBeInTheDocument()
    expect(within(items[1]).getByText('Xem, Sửa')).toBeInTheDocument()
  })

  it('read-only viewers get no action menu on any row', () => {
    renderList([row({})], false)
    expect(screen.queryByRole('button', { name: /Thao tác với quyền/ })).not.toBeInTheDocument()
  })
})
