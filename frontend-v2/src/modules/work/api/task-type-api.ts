import { apiGet, apiPost } from '@/core/api'
import type { PaginatedResult } from '@/shared/types/api'
import type { WorkTask, WorkTaskType } from '../types/work'

/**
 * Loại việc của Dự án (duoc-CR-656). Màn quản trị khai danh mục đi qua lớp CRUD chung
 * (`/api/work/task-types`); file này chỉ lo phần ô chọn của panel và đánh giá kết quả.
 */
export const workTaskTypeApi = {
  /** Loại đang dùng — cho ô chọn. Trần 500 là cũng là trần của backend; danh mục thực tế chỉ vài chục. */
  listActive: () =>
    apiGet<PaginatedResult<WorkTaskType>>('/api/work/task-types', {
      params: { is_active: true, page_size: 500 },
    }),

  /** Cả loại đã ngừng — bộ lọc điều kiện phải nhận ra tên loại của việc cũ. */
  listAll: () =>
    apiGet<PaginatedResult<WorkTaskType>>('/api/work/task-types', { params: { page_size: 500 } }),

  /** Người giao / quản lý dự án đánh giá việc ĐÃ XONG. `PHẢI LÀM LẠI` mở lại việc. */
  setOutcome: (taskId: number, outcome: number) =>
    apiPost<WorkTask>(`/api/work/tasks/${taskId}/outcome`, { outcome }),
}
