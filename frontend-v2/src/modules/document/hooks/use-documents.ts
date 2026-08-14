import { useCallback } from 'react'

import { documentRecordCollection } from '../store/document-record-store'
import { bookYearOf, buildDocumentCode, nextBookNo } from '../helpers/document-number'
import type { DocumentDirection, DocumentRecordInput } from '../types/document-record'
import {
  useCollectionActions,
  useCollectionHistory,
  useCollectionItem,
  useCollectionItems,
} from './use-collection'
import { useDocumentTypes } from './use-document-types'

export function useDocuments() {
  return useCollectionItems(documentRecordCollection)
}

export const useDocument = (id?: number) => useCollectionItem(documentRecordCollection, id)
export const useDocumentHistory = (id?: number) =>
  useCollectionHistory(documentRecordCollection, id)

/**
 * Lưu / xóa văn bản.
 *
 * Lúc TẠO MỚI, hàm `save` tự vào sổ: cấp số thứ tự theo (luồng × năm ban hành)
 * rồi ghép số hiệu theo tiền tố của loại văn bản. Sửa thì GIỮ NGUYÊN số cũ —
 * số đã vào sổ mà đổi thì mọi giấy tờ đã phát hành thành sai.
 */
export function useDocumentActions() {
  const records = useDocuments()
  const { items: documentTypes } = useDocumentTypes()
  const { save: persist, remove } = useCollectionActions(documentRecordCollection)

  /**
   * Ghi riêng phần NỘI DUNG SOẠN THẢO.
   *
   * Tách khỏi `save` vì trình soạn thảo gọi liên tục theo nhịp tự động lưu: chỉ
   * đụng đúng trường `content`, và không ghi lịch sử (`silent`) để sổ nhật ký
   * không ngập những dòng "Cập nhật" cách nhau vài giây.
   */
  const saveContent = useCallback(
    (id: number, content: string, options?: { silent?: boolean }) => {
      const current = records.find((record) => record.id === id)
      if (!current) return
      persist({ ...current, content }, id, { silent: options?.silent ?? true })
    },
    [persist, records],
  )

  const save = useCallback(
    (values: DocumentRecordInput, id?: number) => {
      if (id) return persist(values, id)

      const year = bookYearOf(values.issued_date)
      const bookNo = nextBookNo(records, values.direction, year)
      const typeCode =
        documentTypes.find((type) => type.id === values.document_type_id)?.code ?? ''

      return persist({
        ...values,
        book_no: bookNo,
        book_year: year,
        // Người dùng gõ số riêng thì tôn trọng — nhiều đơn vị đã có cách đánh
        // số của họ; bỏ trống mới ghép số theo tiền tố loại văn bản.
        code: values.code.trim() || buildDocumentCode(typeCode, year, bookNo),
      })
    },
    [persist, records, documentTypes],
  )

  return { save, saveContent, remove }
}

/**
 * Số hiệu mà hệ SẼ cấp nếu người dùng để trống ô "Số văn bản".
 *
 * Chỉ để làm placeholder gợi ý, không ghi vào form: tính lại theo (sổ × năm)
 * đang chọn nên đổi sổ hay đổi ngày ban hành là số gợi ý đổi theo.
 */
export function useNextDocumentCode(
  direction: DocumentDirection,
  issuedDate: string,
  documentTypeId: number,
): string {
  const records = useDocuments()
  const { items: documentTypes } = useDocumentTypes()

  const year = bookYearOf(issuedDate)
  const typeCode = documentTypes.find((type) => type.id === documentTypeId)?.code ?? ''
  return buildDocumentCode(typeCode, year, nextBookNo(records, direction, year))
}
