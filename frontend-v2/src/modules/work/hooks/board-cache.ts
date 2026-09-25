import type { QueryClient, QueryKey } from '@tanstack/react-query'

import type { WorkBoard } from '../types/work'

/**
 * Cập nhật LẠC QUAN trên bảng công việc khi bảng có nhiều biến thể trong bộ nhớ
 * đệm — bao-CR-483.
 *
 * Từ CR này khóa bảng có thêm đuôi chế độ (`light` / `full`), nên một dự án có
 * thể đang giữ HAI bản trong đệm (vừa xem kanban nhẹ xong chuyển sang Gantt).
 * Ảnh lạc quan phải áp lên CẢ HAI, không thì chuyển khung nhìn là thấy thẻ nhảy
 * về chỗ cũ một nhịp cho tới khi refetch. Ba hàm này thay cho cặp
 * `getQueryData` / `setQueryData` trên một khóa duy nhất trước đây.
 */
export type BoardSnapshot = [QueryKey, WorkBoard | undefined][]

export function snapshotBoards(queryClient: QueryClient, prefix: QueryKey): BoardSnapshot {
  return queryClient.getQueriesData<WorkBoard>({ queryKey: prefix })
}

export function patchBoards(
  queryClient: QueryClient,
  prefix: QueryKey,
  update: (board: WorkBoard) => WorkBoard,
): void {
  queryClient.setQueriesData<WorkBoard>({ queryKey: prefix }, (board) =>
    board ? update(board) : board,
  )
}

export function restoreBoards(queryClient: QueryClient, snapshot: BoardSnapshot | undefined): void {
  snapshot?.forEach(([key, board]) => {
    if (board) queryClient.setQueryData(key, board)
  })
}
