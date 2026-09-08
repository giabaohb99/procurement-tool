import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { TaskAssigneePicker } from './task-assignee-picker'
import type { WorkAssignee, WorkMember } from '../types/work'
import { WORK_ASSIGNEE_KIND, WORK_ROLE } from '../types/work'

/**
 * Ô «Người phụ trách» — dáng CỤM AVATAR CHỒNG NHAU (CR-256).
 *
 * Bản trước là một dải chip, mỗi người một viên mang họ tên đầy đủ: ba người là
 * tràn sang hàng thứ hai và hàng này cao gấp đôi mọi hàng thuộc tính khác. Bài
 * này ghim ba thứ dễ hỏng lặng lẽ:
 *   - đếm sai «N người» (đếm cả người THEO DÕI vào),
 *   - quá 3 người thì phần dư phải dồn vào «+N», không kéo dài mãi,
 *   - chỉ xem thì KHÔNG được dựng nút bấm — nút không ăn gì là lừa người dùng.
 */

//  `kind: number` chứ không để suy ra từ giá trị mặc định: TS sẽ chốt kiểu
//  thành đúng hằng `1` và không nhận nổi `FOLLOWER`.
function nguoi(id: number, ten: string, kind: number = WORK_ASSIGNEE_KIND.PIC): WorkAssignee {
  return { employee_id: id, kind, employee_name: ten, employee_code: `NV${id}` }
}

function thanhVien(id: number, ten: string): WorkMember {
  return {
    id,
    employee_id: id,
    role: WORK_ROLE.MEMBER,
    department_id: null,
    employee_name: ten,
    employee_code: `NV${id}`,
  }
}

const MOI_NGUOI = [
  thanhVien(1, 'Trần Minh Được'),
  thanhVien(2, 'Mộc'),
  thanhVien(3, 'Vũ Kinh Doanh'),
]

function ve(assignees: WorkAssignee[], disabled = false) {
  render(
    <TaskAssigneePicker
      assignees={assignees}
      members={MOI_NGUOI}
      disabled={disabled}
      onChange={vi.fn()}
    />,
  )
}

describe('TaskAssigneePicker — dáng đầy đủ (panel chi tiết)', () => {
  it('MỘT người thì hiện TÊN họ, không phải «1 người phụ trách»', () => {
    //  Đọc tên thẳng vẫn nhanh hơn phải bấm ra xem là ai.
    ve([nguoi(1, 'Trần Minh Được')])
    expect(screen.getByText('Trần Minh Được')).toBeInTheDocument()
  })

  it('NHIỀU người thì gom thành «N người phụ trách»', () => {
    ve([nguoi(1, 'Trần Minh Được'), nguoi(2, 'Mộc')])
    expect(screen.getByText('2 người phụ trách')).toBeInTheDocument()
  })

  it('KHÔNG đếm người theo dõi vào con số phụ trách', () => {
    //  Hai vai khác hẳn nhau; gộp là báo sai ai đang chịu trách nhiệm.
    ve([nguoi(1, 'Trần Minh Được'), nguoi(2, 'Mộc', WORK_ASSIGNEE_KIND.FOLLOWER)])
    expect(screen.getByText('Trần Minh Được')).toBeInTheDocument()
    expect(screen.queryByText('2 người phụ trách')).not.toBeInTheDocument()
  })

  it('chưa ai phụ trách thì mời gán, và đó là một nút bấm được', () => {
    ve([])
    expect(screen.getByRole('button', { name: 'Gán người phụ trách' })).toBeInTheDocument()
  })

  it('CHỈ XEM mà chưa ai thì nói rõ, KHÔNG dựng nút', () => {
    ve([], true)
    expect(screen.getByText('Chưa gán ai')).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('CHỈ XEM mà có người thì vẫn đọc được, vẫn KHÔNG có nút', () => {
    ve([nguoi(1, 'Trần Minh Được'), nguoi(2, 'Mộc')], true)
    expect(screen.getByText('2 người phụ trách')).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('quá 3 người thì dồn phần dư vào «+N», không vẽ mãi', () => {
    //  Việc giao cho cả phòng: 8 avatar liền nhau là tràn hết hàng.
    ve(Array.from({ length: 8 }, (_, i) => nguoi(i + 1, `Nhân sự ${i + 1}`)))
    expect(screen.getByText('+5')).toBeInTheDocument()
    expect(screen.getByText('8 người phụ trách')).toBeInTheDocument()
  })

  it('đúng 3 người thì KHÔNG có «+0» thừa', () => {
    ve([nguoi(1, 'A Một'), nguoi(2, 'B Hai'), nguoi(3, 'C Ba')])
    expect(screen.queryByText('+0')).not.toBeInTheDocument()
  })

  it('người CHƯA CÓ TÊN vẫn ra một avatar, không ra ô trống', () => {
    //  Hồ sơ nhân sự thiếu tên vẫn lọt vào được.
    ve([nguoi(7, '')])
    expect(screen.getByText('?')).toBeInTheDocument()
  })

  it('cả cụm là MỘT nút duy nhất — không có nút «+» riêng bên cạnh', () => {
    //  Hai chỗ bấm cho cùng một việc chỉ tổ bắt người dùng chọn.
    ve([nguoi(1, 'Trần Minh Được'), nguoi(2, 'Mộc')])
    expect(screen.getAllByRole('button')).toHaveLength(1)
  })

  it('tên nút nói rõ đang có ai và bấm để làm gì', () => {
    ve([nguoi(1, 'Trần Minh Được')])
    expect(
      screen.getByRole('button', { name: /Người phụ trách: Trần Minh Được.*đổi/i }),
    ).toBeInTheDocument()
  })
})
