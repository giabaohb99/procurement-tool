import { useState, type DragEvent } from 'react'

/**
 * Nhận PAYLOAD NGOÀI CÂY (kéo từ khung khác thả vào một dòng cây) — tách khỏi
 * kéo thả NỘI BỘ (`use-tree-row-drop-zone.ts`) vì hai nguồn khác hẳn nhau: nội
 * bộ theo dõi qua state React (`dragSourceId` giữ ở nơi gọi `TreeView`), còn
 * payload ngoài chỉ biết được qua `dataTransfer.types` lúc `dragover`/`drop` —
 * `getData()` luôn trả rỗng ở `dragover` (giới hạn bảo mật của trình duyệt),
 * `types` thì đọc được ngay nên dùng nó để nhận diện MIME đang kéo qua.
 */
export function useTreeRowExternalDrop(mimeType: string | undefined, accepts: boolean) {
  const [hover, setHover] = useState(false)
  const enabled = Boolean(mimeType) && accepts

  function isPayload(event: DragEvent): boolean {
    return enabled && Boolean(event.dataTransfer?.types.includes(mimeType as string))
  }

  return { hover, setHover, isPayload }
}
