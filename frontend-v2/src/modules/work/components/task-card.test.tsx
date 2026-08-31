import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { TaskCardBody } from './task-card'
import type { CardFields } from '../types/view-options'
import { DEFAULT_CARD_FIELDS } from '../types/view-options'
import type { WorkAssignee, WorkLabelField, WorkTask, WorkTaskLabelValue } from '../types/work'
import {
  WORK_ASSIGNEE_KIND,
  WORK_FIELD_TYPE,
  WORK_TASK_KIND,
  WORK_TASK_STATUS,
} from '../types/work'

/**
 * Thân thẻ kanban — ô tick «xong việc» và luật "trường rỗng thì BỎ HẲN dòng".
 *
 * Vì sao có tệp này: thẻ kanban là chỗ dữ liệu bẩn nhất của phân hệ đổ về. Tên
 * việc do người dùng gõ tự do (dán cả đoạn văn, dán một chuỗi 300 ký tự không
 * dấu cách), số người phụ trách không chặn trên, nhãn tùy biến thì mỗi dự án tự
 * khai — mà thẻ phải nằm vừa một cột hẹp. Mọi khẳng định ở đây theo VAI TRÒ và
 * NỘI DUNG, không theo class Tailwind: jsdom không dựng bố cục nên đo bề rộng ở
 * đây là đo cái không có thật; phần TRÀN KHUNG phải soi bằng mắt trên trình duyệt.
 */

const NGUOI: WorkAssignee = {
  employee_id: 1,
  kind: WORK_ASSIGNEE_KIND.PIC,
  employee_name: 'Trần Minh Được',
  employee_code: 'DEGO0001',
}

function viec(over: Partial<WorkTask> = {}): WorkTask {
  return {
    id: 7,
    list_id: 1,
    section_id: 1,
    parent_id: null,
    title: 'Lên kế hoạch ngân sách quảng cáo tháng 9',
    description: '',
    status: WORK_TASK_STATUS.OPEN,
    kind: WORK_TASK_KIND.TASK,
    start_date: '',
    due_date: '',
    sort_order: 100,
    creator_employee_id: 1,
    completed_at: null,
    completed_by: null,
    created_at: '2026-08-31T02:00:00',
    updated_at: '2026-08-31T02:00:00',
    assignees: [],
    labels: [],
    subtask_done: 0,
    subtask_total: 0,
    comment_count: 0,
    ...over,
  }
}

function truong(over: Partial<WorkLabelField> = {}): WorkLabelField {
  return {
    id: 3,
    list_id: 1,
    name: 'Tag',
    sort_order: 1,
    field_type: WORK_FIELD_TYPE.SINGLE,
    system_key: '',
    value_count: 0,
    options: [{ id: 30, field_id: 3, name: 'Ngân sách', color: 'amber', sort_order: 1 }],
    ...over,
  }
}

function giaTri(over: Partial<WorkTaskLabelValue> = {}): WorkTaskLabelValue {
  return {
    field_id: 3,
    option_id: null,
    value_text: '',
    value_number: null,
    value_date: '',
    value_employee_id: null,
    value_employee_name: '',
    ...over,
  }
}

/**
 * Chỉ bật đúng những trường cần cho từng bài, cho khỏi lẫn dòng của trường khác.
 *
 * Nhãn TÙY BIẾN phải khai bằng khóa `label:{id}` mới được vẽ — ở màn thật khóa
 * ấy do `mergeCardFields` nối vào, không nằm sẵn trong `DEFAULT_CARD_FIELDS`.
 */
function chiBat(...keys: string[]): CardFields {
  const dungSan = DEFAULT_CARD_FIELDS.map((f) => ({ ...f, visible: keys.includes(f.key) }))
  const nhan = keys
    .filter((k) => k.startsWith('label:'))
    .map((k) => ({ key: k as CardFields[number]['key'], visible: true }))
  return [...dungSan, ...nhan]
}

const oTick = () => screen.getByRole('checkbox')

// ── Ô tick «xong việc» ──────────────────────────────────────────────────────────

describe('TaskCardBody — ô tick xong việc', () => {
  it('tick rồi báo ĐÚNG id và trạng thái muốn chuyển sang', () => {
    const toggle = vi.fn()
    render(
      <TaskCardBody
        task={viec()}
        labelFields={[]}
        fields={chiBat()}
        canEdit
        onToggleDone={toggle}
      />,
    )
    fireEvent.click(oTick())
    expect(toggle).toHaveBeenCalledWith(7, true)
  })

  it('việc ĐÃ XONG thì ô tick sáng sẵn, và bỏ tick là trả về chưa xong', () => {
    const toggle = vi.fn()
    render(
      <TaskCardBody
        task={viec({ status: WORK_TASK_STATUS.DONE })}
        labelFields={[]}
        fields={chiBat()}
        canEdit
        onToggleDone={toggle}
      />,
    )
    expect(oTick()).toBeChecked()
    fireEvent.click(oTick())
    expect(toggle).toHaveBeenCalledWith(7, false)
  })

  it('việc ĐÃ HỦY KHÔNG được nhìn như đã xong', () => {
    //  Hủy và xong đều là "hết việc" nhưng khác hẳn nhau về nghiệp vụ; tick sẵn
    //  ô của việc đã hủy là báo cáo sai một việc chưa ai làm.
    render(
      <TaskCardBody
        task={viec({ status: WORK_TASK_STATUS.CANCELLED })}
        labelFields={[]}
        fields={chiBat()}
        canEdit
        onToggleDone={vi.fn()}
      />,
    )
    expect(oTick()).not.toBeChecked()
  })

  it('thiếu quyền sửa thì ô tick chỉ để ĐỌC, bấm không gọi gì', () => {
    const toggle = vi.fn()
    render(
      <TaskCardBody
        task={viec({ status: WORK_TASK_STATUS.DONE })}
        labelFields={[]}
        fields={chiBat()}
        canEdit={false}
        onToggleDone={toggle}
      />,
    )
    expect(oTick()).toBeDisabled()
    //  Vẫn phải THẤY được việc đã xong hay chưa — khách xem cũng cần biết.
    expect(oTick()).toBeChecked()
    fireEvent.click(oTick())
    expect(toggle).not.toHaveBeenCalled()
  })

  it('lớp phủ lúc kéo (không truyền onToggleDone) thì ô tick chết hẳn', () => {
    //  `DragOverlay` vẽ lại chính thân thẻ này để bám con trỏ; nó không nhận
    //  thao tác nào, ô tick bấm được ở đó là bấm vào một bản sao.
    render(<TaskCardBody task={viec()} labelFields={[]} fields={chiBat()} canEdit />)
    expect(oTick()).toBeDisabled()
  })

  it('bấm ô tick KHÔNG nổi lên thẻ, nên không mở panel chi tiết', () => {
    //  Thẻ ngoài là `role="button"` mở panel + là tay nắm kéo của dnd-kit. Thiếu
    //  `stopPropagation` thì mỗi lần tick xong là panel bung ra chắn hết bảng.
    const moThe = vi.fn()
    const batDauKeo = vi.fn()
    render(
      <div onClick={moThe} onPointerDown={batDauKeo}>
        <TaskCardBody
          task={viec()}
          labelFields={[]}
          fields={chiBat()}
          canEdit
          onToggleDone={vi.fn()}
        />
      </div>,
    )
    fireEvent.pointerDown(oTick())
    fireEvent.click(oTick())
    expect(moThe).not.toHaveBeenCalled()
    expect(batDauKeo).not.toHaveBeenCalled()
  })

  it('vẫn đặt tên được cho ô tick khi việc CHƯA CÓ TÊN', () => {
    //  Tên rỗng lọt được vào DB (dòng nháp gõ nhầm phím Enter), mà nhãn cho
    //  trình đọc màn hình ghép thẳng từ tên việc.
    render(
      <TaskCardBody
        task={viec({ title: '' })}
        labelFields={[]}
        fields={chiBat()}
        canEdit
        onToggleDone={vi.fn()}
      />,
    )
    expect(oTick()).toHaveAccessibleName(/Đánh dấu hoàn thành/)
  })
})

// ── Dữ liệu cực đoan ────────────────────────────────────────────────────────────

describe('TaskCardBody — dữ liệu cực đoan', () => {
  it('tên việc dài ngoẵng vẫn ra ĐỦ chữ, không bị cắt cụt trong DOM', () => {
    //  Cắt bớt chữ ở tầng dữ liệu là mất hẳn nội dung khi copy hay khi trình đọc
    //  màn hình đọc. Việc thu gọn hai dòng là của CSS (`line-clamp-2`), phải soi
    //  bằng mắt — jsdom không dựng bố cục nên đo ở đây là đo cái không có thật.
    const dai = 'Lên kế hoạch ngân sách quảng cáo tháng 9 '.repeat(20).trim()
    render(<TaskCardBody task={viec({ title: dai })} labelFields={[]} fields={chiBat()} canEdit />)
    expect(screen.getByText(dai)).toBeInTheDocument()
  })

  it('việc KHÔNG TÊN vẫn nói ra là chưa đặt tên, không để thẻ trắng trơn', () => {
    //  Lỗ ở API (`title: str` nhận cả chuỗi trắng) nay đã vá ở `task_service`,
    //  nhưng dòng cũ trong DB thì vẫn còn — thẻ trắng nhìn như giao diện hỏng.
    for (const rong of ['', '   ']) {
      const { unmount } = render(
        <TaskCardBody task={viec({ title: rong })} labelFields={[]} fields={chiBat()} canEdit />,
      )
      expect(screen.getByText('(Chưa đặt tên)')).toBeInTheDocument()
      unmount()
    }
  })

  it('tên chỉ toàn dấu cách Ở HAI ĐẦU thì vẫn là tên thật, không rơi vào chỗ dự phòng', () => {
    render(
      <TaskCardBody
        task={viec({ title: '  Việc thật  ' })}
        labelFields={[]}
        fields={chiBat()}
        canEdit
      />,
    )
    expect(screen.getByText('Việc thật')).toBeInTheDocument()
    expect(screen.queryByText('(Chưa đặt tên)')).not.toBeInTheDocument()
  })

  it('một chuỗi 300 ký tự KHÔNG có dấu cách vẫn hiện nguyên', () => {
    //  Người dùng dán một đường link hay một mã lỗi dài — chuỗi liền mạch là
    //  ca làm vỡ khung cột kinh điển nhất.
    const lien = 'a'.repeat(300)
    render(<TaskCardBody task={viec({ title: lien })} labelFields={[]} fields={chiBat()} canEdit />)
    expect(screen.getByText(lien)).toBeInTheDocument()
  })

  it('đông người phụ trách thì chỉ vẽ 3 avatar rồi «+n»', () => {
    const dong = Array.from({ length: 12 }, (_, i) => ({
      ...NGUOI,
      employee_id: i + 1,
      employee_name: `Nhân sự ${i + 1}`,
    }))
    render(
      <TaskCardBody
        task={viec({ assignees: dong })}
        labelFields={[]}
        fields={chiBat('assignees')}
        canEdit
      />,
    )
    expect(screen.getByText('+9')).toBeInTheDocument()
  })

  it('đúng 3 người thì KHÔNG có «+0» thừa', () => {
    const ba = Array.from({ length: 3 }, (_, i) => ({ ...NGUOI, employee_id: i + 1 }))
    render(
      <TaskCardBody
        task={viec({ assignees: ba })}
        labelFields={[]}
        fields={chiBat('assignees')}
        canEdit
      />,
    )
    expect(screen.queryByText('+0')).not.toBeInTheDocument()
  })

  it('người THEO DÕI không bị đếm nhầm thành người phụ trách', () => {
    render(
      <TaskCardBody
        task={viec({ assignees: [{ ...NGUOI, kind: WORK_ASSIGNEE_KIND.FOLLOWER }] })}
        labelFields={[]}
        fields={chiBat('assignees')}
        canEdit
      />,
    )
    expect(screen.queryByText('Phụ trách')).not.toBeInTheDocument()
  })

  it('người phụ trách chưa có TÊN vẫn ra một avatar, không ra ô trống', () => {
    render(
      <TaskCardBody
        task={viec({ assignees: [{ ...NGUOI, employee_name: '' }] })}
        labelFields={[]}
        fields={chiBat('assignees')}
        canEdit
      />,
    )
    expect(screen.getByText('?')).toBeInTheDocument()
  })

  it('trường BẬT nhưng việc chưa có gì thì bỏ hẳn dòng, không vẽ «Hạn chót —»', () => {
    render(<TaskCardBody task={viec()} labelFields={[]} fields={DEFAULT_CARD_FIELDS} canEdit />)
    for (const nhan of ['Phụ trách', 'Hạn chót', 'Ngày bắt đầu', 'Việc con', 'Bình luận']) {
      expect(screen.queryByText(nhan)).not.toBeInTheDocument()
    }
  })

  it('trạng thái «Đang mở» KHÔNG vẽ dòng — mọi thẻ đều thế thì nói làm gì', () => {
    render(<TaskCardBody task={viec()} labelFields={[]} fields={chiBat('status')} canEdit />)
    expect(screen.queryByText('Trạng thái')).not.toBeInTheDocument()
  })

  it('nhãn trỏ tới một giá trị ĐÃ BỊ XÓA thì bỏ hẳn dòng, không để tên trường cụt', () => {
    //  Quản trị xóa một giá trị khỏi bộ chọn nhưng thẻ cũ còn trỏ vào nó.
    render(
      <TaskCardBody
        task={viec({ labels: [giaTri({ option_id: 999 })] })}
        labelFields={[truong()]}
        fields={chiBat('label:3')}
        canEdit
      />,
    )
    expect(screen.queryByText('Tag')).not.toBeInTheDocument()
  })

  it('nhãn của một trường ĐÃ BỊ XÓA khỏi dự án thì im lặng bỏ qua', () => {
    render(
      <TaskCardBody
        task={viec({ labels: [giaTri({ field_id: 404, option_id: 30 })] })}
        labelFields={[truong()]}
        fields={chiBat('label:3')}
        canEdit
      />,
    )
    expect(screen.queryByText('Ngân sách')).not.toBeInTheDocument()
  })

  it('trường CHỌN NHIỀU ra đủ chip, kể cả khi khai chục giá trị', () => {
    const options = Array.from({ length: 10 }, (_, i) => ({
      id: 100 + i,
      field_id: 3,
      name: `Nhãn rất dài số ${i + 1}`,
      color: 'amber',
      sort_order: i,
    }))
    render(
      <TaskCardBody
        task={viec({ labels: options.map((o) => giaTri({ option_id: o.id })) })}
        labelFields={[truong({ field_type: WORK_FIELD_TYPE.MULTI, options })]}
        fields={chiBat('label:3')}
        canEdit
      />,
    )
    expect(screen.getByText('Nhãn rất dài số 1')).toBeInTheDocument()
    expect(screen.getByText('Nhãn rất dài số 10')).toBeInTheDocument()
  })

  it('số 0 của trường SỐ vẫn hiện — 0 là một giá trị, không phải "chưa nhập"', () => {
    render(
      <TaskCardBody
        task={viec({ labels: [giaTri({ value_number: '0.0000' })] })}
        labelFields={[truong({ name: 'Chi phí', field_type: WORK_FIELD_TYPE.NUMBER })]}
        fields={chiBat('label:3')}
        canEdit
      />,
    )
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('số âm và số rất lớn không bị cắt mất chữ số nào', () => {
    render(
      <TaskCardBody
        task={viec({ labels: [giaTri({ value_number: '-1234567890123.5000' })] })}
        labelFields={[truong({ name: 'Chi phí', field_type: WORK_FIELD_TYPE.NUMBER })]}
        fields={chiBat('label:3')}
        canEdit
      />,
    )
    expect(screen.getByText('-1234567890123,5')).toBeInTheDocument()
  })

  it('việc con 0/5 phải hiện, 0/0 thì không', () => {
    const { rerender } = render(
      <TaskCardBody
        task={viec({ subtask_done: 0, subtask_total: 5 })}
        labelFields={[]}
        fields={chiBat('subtasks')}
        canEdit
      />,
    )
    expect(screen.getByText('0/5')).toBeInTheDocument()

    rerender(
      <TaskCardBody
        task={viec({ subtask_done: 0, subtask_total: 0 })}
        labelFields={[]}
        fields={chiBat('subtasks')}
        canEdit
      />,
    )
    expect(screen.queryByText('Việc con')).not.toBeInTheDocument()
  })

  it('tên trường tùy biến dài ngoẵng vẫn ra đủ chữ', () => {
    const ten = 'Kênh phân phối chính của chiến dịch quý 4 năm 2026'
    render(
      <TaskCardBody
        task={viec({ labels: [giaTri({ option_id: 30 })] })}
        labelFields={[truong({ name: ten })]}
        fields={chiBat('label:3')}
        canEdit
      />,
    )
    expect(screen.getByText(ten)).toBeInTheDocument()
  })

  it('thẻ KHÔNG có gì ngoài tên vẫn dựng được, không nổ', () => {
    render(<TaskCardBody task={viec()} labelFields={[]} fields={[]} canEdit />)
    expect(screen.getByText('Lên kế hoạch ngân sách quảng cáo tháng 9')).toBeInTheDocument()
    expect(oTick()).toBeInTheDocument()
  })
})
