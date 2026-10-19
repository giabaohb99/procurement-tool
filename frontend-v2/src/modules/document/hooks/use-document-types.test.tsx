import { renderHook } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { DocumentType } from '../types/document-type'

const rows = [
  { id: 1, code: 'CV', name: 'Công văn', is_active: true, sort_order: 1 },
  { id: 2, code: 'HDLD', name: 'Hợp đồng lao động', is_active: true, sort_order: 2 },
  { id: 3, code: 'QD', name: 'Quyết định', is_active: false, sort_order: 3 },
] as unknown as DocumentType[]

vi.mock('@tanstack/react-query', async (importOriginal) => ({
  ...(await importOriginal<Record<string, unknown>>()),
  useQuery: () => ({ data: { items: rows }, isLoading: false }),
}))

import { useActiveDocumentTypes } from './use-document-types'

describe('useActiveDocumentTypes', () => {
  it('ẩn loại hệ thống HDLD (backend từ chối tạo) và loại đã tắt', () => {
    const { result } = renderHook(() => useActiveDocumentTypes())
    expect(result.current.map((t) => t.code)).toEqual(['CV'])
  })
})
