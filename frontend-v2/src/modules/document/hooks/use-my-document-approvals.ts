import { useMemo } from 'react'

import { useMyDecisions, useMyTasks } from '@/modules/approval/hooks/use-approvals'
import type { MyTask } from '@/modules/approval/types/approval'

/**
 * VIỆC DUYỆT VĂN BẢN đang chờ chính người đăng nhập.
 *
 * Lọc tại chỗ từ hộp việc CHUNG (`useMyTasks()` không tham số) thay vì gọi
 * `useMyTasks('document')`: nút hộp việc trên thanh trên đã nạp sẵn truy vấn
 * chung ở mọi trang, nên dùng lại là **không thêm một vòng mạng nào** — trong
 * khi hỏi riêng theo `entity` sẽ đẻ ra một khóa truy vấn thứ hai chạy song song
 * với cái đã có, ở mọi màn của phân hệ Văn bản.
 *
 * Đổi lại phải chấp nhận một điều: hộp việc chung không phân trang, nên nếu sau
 * này nó phân trang thì chỗ này phải quay lại hỏi riêng theo `entity`.
 */
export function useMyDocumentTasks() {
  const { data, isLoading } = useMyTasks()
  //  `useMemo` không phải để tiết kiệm phép lọc (danh sách vài chục dòng) mà để
  //  giữ NGUYÊN THAM CHIẾU giữa các lần render: chỗ gọi đưa mảng này vào mảng
  //  phụ thuộc của `useMemo` khác (cột bảng danh sách), lọc mới mỗi lần render
  //  là các memo phía sau hỏng hết.
  const items = useMemo(
    () => (data?.items ?? []).filter((row) => row.entity === 'document'),
    [data?.items],
  )
  return { items, isLoading }
}

/**
 * Việc duyệt của TÔI trên đúng một văn bản — `null` nghĩa là không phải lượt
 * tôi (hoặc tôi không nằm trong luồng của văn bản này).
 *
 * Trả nguyên `MyTask` chứ không phải một cờ boolean vì hộp thoại duyệt cần đủ
 * bối cảnh của việc: bấm thay ai theo ủy quyền, hạn duyệt, ai trình.
 */
export function useMyDocumentTask(documentId: number): MyTask | null {
  const { items } = useMyDocumentTasks()
  return items.find((row) => row.entity_id === documentId) ?? null
}

/**
 * VĂN BẢN TÔI ĐÃ DUYỆT trong `ngay` ngày gần nhất.
 *
 * Khác `useMyDocumentTasks` ở chỗ hỏi thẳng backend theo `entity` — danh sách
 * này không có sẵn ở đâu cả, và nó cũng không phải thứ mở ở mọi màn nên một
 * truy vấn riêng là đúng chỗ.
 */
export function useMyDocumentDecisions(ngay: number) {
  const { data, isLoading } = useMyDecisions('document', ngay)
  return { items: data?.items ?? [], isLoading }
}
