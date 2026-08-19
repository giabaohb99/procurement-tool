import { useCallback, useEffect, useRef } from 'react'

import { pxToMm, type PageMargins } from '@/shared/ui/rich-text-editor'
import { useSaveVersionMargins } from './use-document-versions'

/**
 * Ghi LỀ TRANG xuống phiên bản đang mở.
 *
 * Ghi NGAY khi người dùng buông tay khỏi thước, KHÔNG hẹn giờ gom nhịp.
 *
 * Bản đầu có hẹn 600ms để gộp các nhịp rê chuột — hỏng theo hai đường, cả hai
 * đều gặp thật:
 *
 *  1. Kéo lề xong bấm ngay «In / Xuất PDF» thì tab bản in mở ra và đọc bản ghi
 *     **trước khi** lượt hẹn kịp bay đi → in ra lề cũ.
 *  2. Kéo lề rồi chuyển tab (hoặc rời trang) trong khoảng đó thì hàm dọn dẹp
 *     hủy luôn hẹn giờ → mất hẳn thay đổi, không có gì báo.
 *
 * Nay thước chỉ báo ra MỘT LẦN mỗi cú chỉnh (`EditorRuler.onCommit`) nên không
 * còn gì để gom: mỗi lần buông tay là đúng một lượt ghi.
 */
export function useDocumentPageMargins(documentId: number, versionId?: number | null) {
  const save = useSaveVersionMargins(documentId, versionId)
  const saveRef = useRef(save.mutate)
  useEffect(() => {
    saveRef.current = save.mutate
  })

  const luu = useCallback((margins: PageMargins) => {
    saveRef.current({
      margin_left_mm: pxToMm(margins.left),
      margin_right_mm: pxToMm(margins.right),
    })
  }, [])

  //  `dangLuu` để nơi gọi khóa nút mở bản in trong lúc lượt ghi chưa xong —
  //  chặn nốt khe hở cuối: bấm In đúng lúc yêu cầu còn đang bay.
  return { luu, dangLuu: save.isPending }
}
