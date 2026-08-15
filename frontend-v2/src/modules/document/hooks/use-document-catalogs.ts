import { useMemo } from 'react'

import {
  documentPartnerCollection,
  dynamicFieldCollection,
  securityLevelCollection,
} from '../store/document-catalog-stores'
import type { SecurityLevelKind } from '../types/security-level'
import {
  useCollectionActions,
  useCollectionHistory,
  useCollectionItem,
  useCollectionItems,
} from './use-collection'

/** Ba danh mục phụ của phân hệ Văn bản — cùng một khuôn hook. */

// ===== Mức mật / khẩn =====
export function useSecurityLevels() {
  return useCollectionItems(securityLevelCollection)
}

/** Mức đang bật của MỘT thang (mật hoặc khẩn), xếp theo thứ bậc tăng dần. */
export function useSecurityLevelOptions(kind: SecurityLevelKind) {
  const items = useSecurityLevels()
  return useMemo(
    () =>
      items
        .filter((item) => item.is_active && item.kind === kind)
        .sort((a, b) => a.rank - b.rank),
    [items, kind],
  )
}

export const useSecurityLevel = (id?: number) =>
  useCollectionItem(securityLevelCollection, id)
export const useSecurityLevelHistory = (id?: number) =>
  useCollectionHistory(securityLevelCollection, id)
export const useSecurityLevelActions = () => useCollectionActions(securityLevelCollection)

// ===== Đối tác =====
export function useDocumentPartners() {
  return useCollectionItems(documentPartnerCollection)
}

export function useActiveDocumentPartners() {
  const items = useDocumentPartners()
  return useMemo(() => items.filter((item) => item.is_active), [items])
}

export const useDocumentPartner = (id?: number) =>
  useCollectionItem(documentPartnerCollection, id)
export const useDocumentPartnerHistory = (id?: number) =>
  useCollectionHistory(documentPartnerCollection, id)
export const useDocumentPartnerActions = () =>
  useCollectionActions(documentPartnerCollection)

// ===== Trường thông tin động =====
export function useDynamicFields() {
  const items = useCollectionItems(dynamicFieldCollection)
  return useMemo(() => [...items].sort((a, b) => a.sort_order - b.sort_order), [items])
}

/**
 * Trường áp dụng cho MỘT loại văn bản: trường khai rỗng `document_type_ids` là
 * dùng chung cho mọi loại.
 */
export function useDynamicFieldsFor(documentTypeId?: number) {
  const fields = useDynamicFields()
  return useMemo(
    () =>
      fields.filter(
        (field) =>
          field.is_active &&
          (field.document_type_ids.length === 0 ||
            (documentTypeId !== undefined &&
              field.document_type_ids.includes(documentTypeId))),
      ),
    [fields, documentTypeId],
  )
}

export const useDynamicField = (id?: number) => useCollectionItem(dynamicFieldCollection, id)
export const useDynamicFieldHistory = (id?: number) =>
  useCollectionHistory(dynamicFieldCollection, id)
export const useDynamicFieldActions = () => useCollectionActions(dynamicFieldCollection)
