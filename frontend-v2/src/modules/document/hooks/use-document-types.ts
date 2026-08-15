import { useCallback, useMemo } from 'react'

import { documentTypeCollection } from '../store/document-type-store'
import type { DocumentType } from '../types/document-type'
import {
  useCollectionActions,
  useCollectionHistory,
  useCollectionItem,
  useCollectionItems,
} from './use-collection'

/** Danh sách loại văn bản, lọc theo mã / tên / tiền tố. */
export function useDocumentTypes(keyword = '') {
  const items = useCollectionItems(documentTypeCollection)

  const filtered = useMemo(() => {
    const needle = keyword.trim().toLowerCase()
    if (!needle) return items
    return items.filter((item) =>
      [item.code, item.name, item.prefix].some((field) =>
        field.toLowerCase().includes(needle),
      ),
    )
  }, [items, keyword])

  return { items: filtered, total: items.length }
}

/** Loại văn bản đang bật — dùng cho ô chọn loại khi tạo văn bản. */
export function useActiveDocumentTypes(): DocumentType[] {
  const items = useCollectionItems(documentTypeCollection)
  return useMemo(() => items.filter((item) => item.is_active), [items])
}

export function useDocumentType(id?: number) {
  return useCollectionItem(documentTypeCollection, id)
}

export function useDocumentTypeHistory(id?: number) {
  return useCollectionHistory(documentTypeCollection, id)
}

/**
 * Lưu / xóa loại văn bản, kèm `isCodeTaken` để form chặn trùng mã ngay trên ô
 * nhập — mã đi vào số hiệu văn bản nên bắt buộc duy nhất.
 */
export function useDocumentTypeActions() {
  const items = useCollectionItems(documentTypeCollection)
  const { save, remove } = useCollectionActions(documentTypeCollection)

  const isCodeTaken = useCallback(
    (code: string, id?: number) =>
      items.some(
        (item) => item.id !== id && item.code.toLowerCase() === code.trim().toLowerCase(),
      ),
    [items],
  )

  return { save, remove, isCodeTaken }
}
