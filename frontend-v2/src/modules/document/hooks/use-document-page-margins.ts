import { useCallback, useEffect, useRef } from 'react'

import { pxToMm, type PageMargins } from '@/shared/ui/rich-text-editor'
import { useSaveVersionMargins } from './use-document-versions'

/**
 * Chờ ngần này (ms) sau nhịp kéo cuối mới ghi xuống bản ghi.
 *
 * Thước kẻ báo thay đổi ở MỖI khung hình lúc rê chuột; ghi thẳng là một cú kéo
 * ngang trang giấy đẻ ra vài chục lượt PATCH. Mốc này dài hơn khoảng nghỉ giữa
 * hai khung hình rất nhiều nên chỉ còn đúng một lượt sau khi buông tay.
 */
const SAVE_DELAY = 600

/**
 * Ghi LỀ TRANG xuống phiên bản đang mở, gộp nhịp.
 *
 * Trả về đúng một hàm để cắm thẳng vào `onMarginsChange` của trình soạn thảo.
 */
export function useDocumentPageMargins(documentId: number, versionId?: number | null) {
  const save = useSaveVersionMargins(documentId, versionId)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)
  //  Giữ hàm ghi trong ref: đối tượng mutation dựng lại ở mỗi lần render, để nó
  //  vào mảng phụ thuộc là hàm trả về đổi liên tục và hẹn giờ bị dựng lại theo.
  const saveRef = useRef(save.mutate)
  useEffect(() => {
    saveRef.current = save.mutate
  })

  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current)
    },
    [],
  )

  return useCallback((margins: PageMargins) => {
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(() => {
      timer.current = null
      saveRef.current({
        margin_left_mm: pxToMm(margins.left),
        margin_right_mm: pxToMm(margins.right),
      })
    }, SAVE_DELAY)
  }, [])
}
