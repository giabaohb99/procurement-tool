import { describe, expect, it } from 'vitest'

import type { WorkTask } from '../types/work'
import { WORK_TASK_STATUS } from '../types/work'
import { applyKeyword, prepareTasks, sortTasks } from './filter-tasks'

/**
 * Lát cắt và sắp xếp của khung nhìn Công việc.
 *
 * Đây là chỗ quyết định NGƯỜI DÙNG THẤY GÌ trên bảng, mà nó chạy hoàn toàn ở
 * trình duyệt nên không bài test backend nào chạm tới. Sai ở đây là việc biến
 * mất khỏi bảng trong khi vẫn nằm nguyên dưới CSDL.
 */

function label(fieldId: number, optionId: number) {
  return {
    field_id: fieldId,
    option_id: optionId,
    value_text: '',
    value_number: null,
    value_date: '',
    value_employee_id: null,
    value_employee_name: '',
  }
}

function task(patch: Partial<WorkTask> = {}): WorkTask {
  return {
    id: 1,
    list_id: 1,
    section_id: 1,
    parent_id: null,
    title: 'Việc',
    description: '',
    status: WORK_TASK_STATUS.OPEN,
    start_date: '',
    due_date: '',
    sort_order: 0,
    creator_employee_id: 0,
    completed_at: null,
    completed_by: null,
    created_at: '2026-08-01T00:00:00',
    updated_at: '2026-08-01T00:00:00',
    assignees: [],
    labels: [],
    subtask_done: 0,
    subtask_total: 0,
    comment_count: 0,
    ...patch,
  }
}

describe('applyKeyword', () => {
  it('tìm cả trong mô tả, không phân biệt hoa thường và khoảng trắng thừa', () => {
    const rows = [task({ id: 1, title: 'In tem' }), task({ id: 2, description: 'Đặt IN nhãn' })]
    expect(applyKeyword(rows, '  in  ').map((t) => t.id)).toEqual([1, 2])
  })

  //  Mô tả lưu HTML từ khi ô mô tả thành trình soạn thảo rich text: tìm trên
  //  chuỗi thô thì gõ "p" khớp mọi việc có mô tả vì trúng tên thẻ `<p>`.
  it('không khớp TÊN THẺ trong mô tả HTML, nhưng vẫn khớp chữ bên trong thẻ', () => {
    const rows = [task({ id: 1, description: '<p><strong>Đặt in</strong> nhãn</p>' })]
    expect(applyKeyword(rows, 'strong')).toHaveLength(0)
    expect(applyKeyword(rows, 'đặt in').map((t) => t.id)).toEqual([1])
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

  //  Độ ưu tiên nay là một TRƯỜNG TÙY BIẾN (`label:{id}`), không còn cột cứng.
  it('sắp theo trường tùy biến: xếp theo THỨ TỰ giá trị, việc chưa chọn xuống cuối', () => {
    //  Hạng lấy từ bộ giá trị, không phải `option_id`: id 91 là bậc đầu (P1).
    const rank = new Map([
      [91, 0],
      [92, 1],
    ])
    const rows = [
      task({ id: 1 }),
      task({ id: 2, labels: [label(7, 92)] }),
      task({ id: 3, labels: [label(7, 91)] }),
    ]
    expect(sortTasks(rows, 'label:7', { optionRank: rank }).map((t) => t.id)).toEqual([3, 2, 1])
  })

  it('sắp theo trường tùy biến mà thiếu bảng hạng thì rơi về option_id, không nổ', () => {
    const rows = [task({ id: 1, labels: [label(7, 92)] }), task({ id: 2, labels: [label(7, 91)] })]
    expect(sortTasks(rows, 'label:7').map((t) => t.id)).toEqual([2, 1])
  })

  it('giá trị của TRƯỜNG KHÁC không lọt vào phép sắp xếp', () => {
    const rows = [task({ id: 1, labels: [label(9, 91)] }), task({ id: 2, labels: [label(7, 92)] })]
    //  Việc 1 không có giá trị ở trường 7 nên phải xuống cuối, dù nó có nhãn.
    expect(sortTasks(rows, 'label:7', { optionRank: new Map([[92, 0]]) }).map((t) => t.id)).toEqual([
      2, 1,
    ])
  })

  it('sắp theo ngày bắt đầu cũng đẩy việc CHƯA ĐẶT xuống cuối như hạn chót', () => {
    const rows = [
      task({ id: 1, start_date: '' }),
      task({ id: 2, start_date: '2026-09-01' }),
      task({ id: 3, start_date: '2026-08-30' }),
    ]
    expect(sortTasks(rows, 'start').map((t) => t.id)).toEqual([3, 2, 1])
  })

  //  Ba mốc "đã xảy ra" xếp NGƯỢC hai mốc "sắp tới": mới nhất lên đầu. Đảo vế
  //  rồi mới so là chuỗi rỗng thành lớn nhất, việc chưa hoàn thành chen lên trên.
  it('sắp theo ngày hoàn thành: mới nhất lên đầu, việc CHƯA xong xuống cuối', () => {
    const rows = [
      task({ id: 1, completed_at: null }),
      task({ id: 2, completed_at: '2026-08-01T00:00:00' }),
      task({ id: 3, completed_at: '2026-08-20T00:00:00' }),
    ]
    expect(sortTasks(rows, 'completed').map((t) => t.id)).toEqual([3, 2, 1])
  })

  it('sắp theo sửa gần nhất lấy updated_at, không lấy created_at', () => {
    const rows = [
      task({ id: 1, created_at: '2026-08-20T00:00:00', updated_at: '2026-08-20T00:00:00' }),
      task({ id: 2, created_at: '2026-08-01T00:00:00', updated_at: '2026-08-28T00:00:00' }),
    ]
    expect(sortTasks(rows, 'updated').map((t) => t.id)).toEqual([2, 1])
    expect(sortTasks(rows, 'created').map((t) => t.id)).toEqual([1, 2])
  })

  it('sắp theo trường tùy biến kiểu chọn-nhiều lấy giá trị ĐẦU TIÊN, việc trống xuống cuối', () => {
    //  Tag nay chính là một trường như thế (`label:{fieldId}`), không còn tiêu
    //  chí «Tag» riêng nữa.
    const rank = new Map([
      [91, 0],
      [94, 1],
    ])
    const rows = [
      task({ id: 1, labels: [] }),
      task({ id: 2, labels: [label(6, 94)] }),
      task({ id: 3, labels: [label(6, 91), label(6, 94)] }),
    ]
    expect(sortTasks(rows, 'label:6', { optionRank: rank }).map((t) => t.id)).toEqual([3, 2, 1])
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
  it('lọc theo TỪ KHÓA trước rồi mới sắp, và KHÔNG còn ẩn ngầm việc đã xong', () => {
    //  Lát cắt cố định "chỉ việc chưa xong" đã bỏ: ẩn ngầm thì lọc «trạng thái
    //  = Hoàn thành» ở nút «Bộ lọc» sẽ ra bảng trống.
    const rows = [
      task({ id: 1, title: 'In tem', due_date: '2026-09-10' }),
      task({ id: 2, title: 'In nhãn', status: WORK_TASK_STATUS.DONE, due_date: '2026-08-01' }),
      task({ id: 3, title: 'Đóng gói', due_date: '2026-08-20' }),
    ]
    expect(prepareTasks(rows, { sort: 'due', keyword: '' }).map((t) => t.id)).toEqual([2, 3, 1])
    expect(prepareTasks(rows, { sort: 'due', keyword: 'in ' }).map((t) => t.id)).toEqual([2, 1])
  })
})
