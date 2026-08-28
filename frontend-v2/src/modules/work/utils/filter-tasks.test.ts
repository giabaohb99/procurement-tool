import { describe, expect, it } from 'vitest'

import type { WorkTask } from '../types/work'
import { WORK_ASSIGNEE_KIND, WORK_TASK_STATUS } from '../types/work'
import { applyKeyword, applyScope, prepareTasks, sortTasks } from './filter-tasks'

/**
 * Lát cắt và sắp xếp của khung nhìn Công việc.
 *
 * Đây là chỗ quyết định NGƯỜI DÙNG THẤY GÌ trên bảng, mà nó chạy hoàn toàn ở
 * trình duyệt nên không bài test backend nào chạm tới. Sai ở đây là việc biến
 * mất khỏi bảng trong khi vẫn nằm nguyên dưới CSDL.
 */

function task(patch: Partial<WorkTask> = {}): WorkTask {
  return {
    id: 1,
    list_id: 1,
    section_id: 1,
    parent_id: null,
    title: 'Việc',
    description: '',
    status: WORK_TASK_STATUS.OPEN,
    priority: 0,
    start_date: '',
    due_date: '',
    sort_order: 0,
    creator_employee_id: 0,
    completed_at: null,
    completed_by: null,
    created_at: '2026-08-01T00:00:00',
    updated_at: '2026-08-01T00:00:00',
    assignees: [],
    tag_ids: [],
    labels: [],
    subtask_done: 0,
    subtask_total: 0,
    comment_count: 0,
    ...patch,
  }
}

describe('applyScope', () => {
  it('mặc định ẩn cả việc đã xong lẫn việc đã hủy, không chỉ việc đã xong', () => {
    //  Việc đã hủy không còn là việc phải làm; để lẫn vào là đếm sai "còn bao nhiêu việc".
    const rows = [
      task({ id: 1 }),
      task({ id: 2, status: WORK_TASK_STATUS.DONE }),
      task({ id: 3, status: WORK_TASK_STATUS.CANCELLED }),
    ]
    expect(applyScope(rows, 'open', 7).map((t) => t.id)).toEqual([1])
  })

  it('«việc của tôi» chỉ tính PIC, không tính người theo dõi', () => {
    const rows = [
      task({
        id: 1,
        assignees: [
          { employee_id: 7, kind: WORK_ASSIGNEE_KIND.PIC, employee_name: '', employee_code: '' },
        ],
      }),
      task({
        id: 2,
        assignees: [
          {
            employee_id: 7,
            kind: WORK_ASSIGNEE_KIND.FOLLOWER,
            employee_name: '',
            employee_code: '',
          },
        ],
      }),
    ]
    expect(applyScope(rows, 'mine', 7).map((t) => t.id)).toEqual([1])
  })

  it('tài khoản không gắn nhân sự (id 0) không nhận nhầm việc của người khác', () => {
    //  `employee_id = 0` là tài khoản kỹ thuật. Nếu so sánh lỏng thì mọi dòng
    //  `creator_employee_id = 0` (dữ liệu cũ) rơi hết vào lát cắt "tôi tạo".
    const rows = [
      task({
        id: 1,
        assignees: [
          { employee_id: 5, kind: WORK_ASSIGNEE_KIND.PIC, employee_name: '', employee_code: '' },
        ],
      }),
    ]
    expect(applyScope(rows, 'mine', 0)).toEqual([])
  })

  it('«tôi tạo» không kéo theo việc mình tạo rồi đã xong', () => {
    const rows = [
      task({ id: 1, creator_employee_id: 7 }),
      task({ id: 2, creator_employee_id: 7, status: WORK_TASK_STATUS.DONE }),
    ]
    expect(applyScope(rows, 'created', 7).map((t) => t.id)).toEqual([1])
  })

  it('danh sách rỗng thì mọi lát cắt đều trả rỗng, không nổ', () => {
    for (const scope of ['open', 'mine', 'created', 'done', 'cancelled'] as const) {
      expect(applyScope([], scope, 7)).toEqual([])
    }
  })
})

describe('applyKeyword', () => {
  it('tìm cả trong mô tả, không phân biệt hoa thường và khoảng trắng thừa', () => {
    const rows = [task({ id: 1, title: 'In tem' }), task({ id: 2, description: 'Đặt IN nhãn' })]
    expect(applyKeyword(rows, '  in  ').map((t) => t.id)).toEqual([1, 2])
  })

  it('từ khóa rỗng giữ nguyên danh sách chứ không lọc sạch', () => {
    const rows = [task({ id: 1 }), task({ id: 2 })]
    expect(applyKeyword(rows, '   ')).toHaveLength(2)
  })
})

describe('sortTasks', () => {
  it('sắp theo hạn thì việc CHƯA ĐẶT HẠN xuống cuối, không leo lên đầu', () => {
    //  Chuỗi rỗng so từ vựng bé hơn mọi ngày — để nguyên là việc chưa có hạn
    //  đứng đầu bảng "gấp nhất", ngược hẳn ý người dùng.
    const rows = [
      task({ id: 1, due_date: '' }),
      task({ id: 2, due_date: '2026-09-01' }),
      task({ id: 3, due_date: '2026-08-30' }),
    ]
    expect(sortTasks(rows, 'due').map((t) => t.id)).toEqual([3, 2, 1])
  })

  it('sắp theo ưu tiên thì P1 lên đầu và "chưa đặt" (0) xuống cuối', () => {
    const rows = [task({ id: 1, priority: 0 }), task({ id: 2, priority: 3 }), task({ id: 3, priority: 1 })]
    expect(sortTasks(rows, 'priority').map((t) => t.id)).toEqual([3, 2, 1])
  })

  it('sắp xếp không làm hỏng mảng gốc — bảng còn dùng lại nó cho khung nhìn khác', () => {
    const rows = [task({ id: 1, sort_order: 2 }), task({ id: 2, sort_order: 1 })]
    sortTasks(rows, 'manual')
    expect(rows.map((t) => t.id)).toEqual([1, 2])
  })

  it('sắp theo tiêu đề dùng thứ tự tiếng Việt, không phải mã ký tự', () => {
    const rows = [task({ id: 1, title: 'Đóng gói' }), task({ id: 2, title: 'Dán tem' })]
    //  Theo mã ký tự thì 'Đ' (U+0110) đứng SAU 'D'… nhưng cũng sau cả 'Z',
    //  nên bảng chữ cái tiếng Việt phải do `localeCompare('vi')` quyết.
    expect(sortTasks(rows, 'title').map((t) => t.id)).toEqual([2, 1])
  })
})

describe('prepareTasks', () => {
  it('lọc trước rồi mới sắp — việc đã xong không chen vào thứ tự của việc đang mở', () => {
    const rows = [
      task({ id: 1, due_date: '2026-09-10' }),
      task({ id: 2, status: WORK_TASK_STATUS.DONE, due_date: '2026-08-01' }),
      task({ id: 3, due_date: '2026-08-20' }),
    ]
    const ra = prepareTasks(rows, { scope: 'open', sort: 'due', keyword: '', myEmployeeId: 7 })
    expect(ra.map((t) => t.id)).toEqual([3, 1])
  })
})
