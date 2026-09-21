import { describe, expect, it } from 'vitest'

import { DOSSIER_EXPIRY, DOSSIER_STATUS } from '@/modules/dossier/types/dossier'
import {
  DOSSIER_PROGRESS,
  type ApplicableDocLine,
  type ApplicableDossier,
} from '@/modules/dossier/types/dossier-applicability'
import {
  CHUNG_ROW_KEY,
  EXPIRY_TONE_CLASS,
  expiryTone,
  groupByLine,
  nearestExpiry,
  nearestExpiryDoc,
} from './dossier-checklist-helpers'

/** Tờ hồ sơ tối thiểu — chỉ khai những ô mà hai hàm dưới đây thật sự đọc. */
function doc(patch: Partial<ApplicableDossier> = {}): ApplicableDossier {
  return {
    id: 1,
    code: 'HS0001',
    name: 'Giấy phép',
    dossier_type_id: 1,
    dossier_type_name: 'Pháp lý',
    status: DOSSIER_STATUS.ACTIVE,
    status_label: 'Đang lưu',
    note: '',
    expiry_date: null,
    expiry_state: DOSSIER_EXPIRY.NONE,
    expiry_state_label: 'Vô thời hạn',
    expiry_days: null,
    reason: '',
    matched_lines: [],
    //  Bộ mặc định của một cặp (chứng từ × hồ sơ) CHƯA ai động tới — đúng thứ
    //  backend trả về khi `tab_dossier_progress` chưa có dòng nào.
    progress_status: DOSSIER_PROGRESS.IDLE,
    progress_status_label: 'Chưa bắt đầu',
    progress_done: false,
    required: true,
    assignee_id: 0,
    assignee_name: '',
    planned_date: null,
    progress_note: '',
    file_note: '',
    progress_saved: false,
    depends: [],
    waiting: [],
    locked: false,
    ...patch,
  }
}

describe('nearestExpiryDoc', () => {
  it('trả null khi danh sách rỗng', () => {
    expect(nearestExpiryDoc([])).toBeNull()
  })

  //  Tờ vô thời hạn có `expiry_date` rỗng. Bản đầu tiên so thẳng chuỗi nên chuỗi
  //  rỗng luôn nhỏ nhất và THẮNG mọi ngày thật — ô tổng ra một ô trống vĩnh viễn.
  it('bỏ qua tờ vô thời hạn thay vì để chuỗi rỗng thắng phép so sánh', () => {
    const undated = doc({ id: 1, expiry_date: null })
    const dated = doc({ id: 2, expiry_date: '2026-12-31' })
    expect(nearestExpiryDoc([undated, dated])?.id).toBe(2)
    expect(nearestExpiryDoc([dated, undated])?.id).toBe(2)
  })

  it('trả null khi mọi tờ đều vô thời hạn', () => {
    expect(nearestExpiryDoc([doc({ id: 1 }), doc({ id: 2 })])).toBeNull()
    expect(nearestExpiry([doc({ id: 1 })])).toBeNull()
  })

  it('lấy ngày SỚM NHẤT bất kể thứ tự trong mảng', () => {
    const list = [
      doc({ id: 1, expiry_date: '2027-01-01' }),
      doc({ id: 2, expiry_date: '2026-02-09' }),
      doc({ id: 3, expiry_date: '2026-10-05' }),
    ]
    expect(nearestExpiryDoc(list)?.id).toBe(2)
    expect(nearestExpiry(list)).toBe('2026-02-09')
  })

  //  Hai tờ cùng hạn: giữ tờ ĐẦU TIÊN, không đảo chỗ. Không chốt thì ô tổng đổi
  //  màu qua lại giữa hai lần tải chỉ vì thứ tự API trả về khác nhau.
  it('giữ tờ đầu tiên khi hai tờ cùng ngày', () => {
    const list = [
      doc({ id: 7, expiry_date: '2026-05-05' }),
      doc({ id: 8, expiry_date: '2026-05-05' }),
    ]
    expect(nearestExpiryDoc(list)?.id).toBe(7)
  })

  it('trả chính tờ đó, không chỉ ngày — ô tổng cần expiry_state để tô màu', () => {
    const list = [doc({ id: 4, expiry_date: '2026-03-03', expiry_state: DOSSIER_EXPIRY.OVER })]
    expect(nearestExpiryDoc(list)?.expiry_state).toBe(DOSSIER_EXPIRY.OVER)
  })
})

/** Dòng hàng tối thiểu của chứng từ. */
function line(no: number, label: string): ApplicableDocLine {
  return { no, label, product_code: `SP${no}`, item_group: '' }
}

describe('groupByLine', () => {
  const chungA = doc({ id: 1, matched_lines: [] })
  const chungB = doc({ id: 2, matched_lines: [] })
  const rieng1 = doc({ id: 3, matched_lines: [1] })
  const rieng2 = doc({ id: 4, matched_lines: [2] })
  const lines = [line(1, 'Cốc đong'), line(2, 'Chai HDPE')]

  //  Lỗi thật, bắt được trên phiếu 2931: bản trước nhân bản cả bộ hồ sơ chung
  //  xuống mọi dòng hàng, nên ba dòng đều ghi y hệt `6/15 · 40%` và dòng TỔNG
  //  của bảng đếm một tờ giấy bốn lần.
  it('không nhân bản hồ sơ chung xuống từng dòng hàng', () => {
    const groups = groupByLine([chungA, chungB, rieng1, rieng2], lines)
    const tongDong = groups.reduce((sum, g) => sum + g.docs.length, 0)
    expect(tongDong).toBe(4)
    expect(groups.find((g) => g.key === 'line-1')?.docs.map((d) => d.id)).toEqual([3])
    expect(groups.find((g) => g.key === 'line-2')?.docs.map((d) => d.id)).toEqual([4])
  })

  it('gom hồ sơ chung vào đúng một dòng, đứng đầu bảng', () => {
    const groups = groupByLine([chungA, rieng1], lines)
    expect(groups[0].key).toBe(CHUNG_ROW_KEY)
    expect(groups[0].docs.map((d) => d.id)).toEqual([1])
  })

  //  Dòng hàng chưa có tờ giấy nào khớp vẫn phải hiện — đó đúng là dòng cần chú ý.
  it('giữ dòng hàng rỗng thay vì bỏ khỏi bảng', () => {
    const groups = groupByLine([rieng1], lines)
    expect(groups.map((g) => g.key)).toEqual(['line-1', 'line-2'])
    expect(groups.find((g) => g.key === 'line-2')?.docs).toEqual([])
  })

  //  Phiếu chưa có dòng nào: vẫn phải bày được bộ hồ sơ chung, không để trắng.
  it('không có dòng hàng nào thì vẫn dựng dòng Chung', () => {
    const groups = groupByLine([chungA], [])
    expect(groups).toHaveLength(1)
    expect(groups[0].key).toBe(CHUNG_ROW_KEY)
  })

  it('không có gì cả thì vẫn dựng dòng Chung rỗng, không trả mảng rỗng', () => {
    const groups = groupByLine([], [])
    expect(groups).toHaveLength(1)
    expect(groups[0].docs).toEqual([])
  })

  //  `matched_lines` rỗng = CHUNG, khác hẳn «không khớp dòng nào». Tờ khớp
  //  nhiều dòng thì hiện ở mọi dòng nó khớp — không phải nhân bản, nó đúng là
  //  hồ sơ của từng dòng đó.
  it('tờ khớp nhiều dòng hiện ở mọi dòng nó khớp', () => {
    const caHai = doc({ id: 9, matched_lines: [1, 2] })
    const groups = groupByLine([caHai], lines)
    expect(groups.find((g) => g.key === 'line-1')?.docs.map((d) => d.id)).toEqual([9])
    expect(groups.find((g) => g.key === 'line-2')?.docs.map((d) => d.id)).toEqual([9])
    //  Không có tờ chung nào thì KHÔNG dựng dòng Chung rỗng cho chật bảng.
    expect(groups.some((g) => g.key === CHUNG_ROW_KEY)).toBe(false)
  })

  //  Số thứ tự dòng bắt đầu từ 1; `no = 0` là dòng thật chứ không phải «chưa
  //  gắn». Lấy 0 làm mốc rỗng là đúng bẫy duoc-CR-322.
  it('nhận dòng số 0 như một dòng hàng thật', () => {
    const doc0 = doc({ id: 5, matched_lines: [0] })
    const groups = groupByLine([doc0], [line(0, 'Dòng 0')])
    expect(groups.find((g) => g.key === 'line-0')?.docs.map((d) => d.id)).toEqual([5])
  })
})

describe('expiryTone', () => {
  it('hết hạn ra đỏ, sắp hết ra vàng', () => {
    expect(expiryTone(DOSSIER_EXPIRY.OVER)).toBe('overdue')
    expect(expiryTone(DOSSIER_EXPIRY.NEAR)).toBe('soon')
  })

  //  Vô thời hạn và còn hạn đều là tin TỐT — cùng về xám, không tô cảnh báo.
  it('vô thời hạn và còn hạn đều ra xám', () => {
    expect(expiryTone(DOSSIER_EXPIRY.NONE)).toBe('normal')
    expect(expiryTone(DOSSIER_EXPIRY.VALID)).toBe('normal')
  })

  //  Backend thêm mã mới mà quên sửa bên này thì phải ra XÁM, đừng ra undefined:
  //  `EXPIRY_TONE_CLASS[undefined]` cho ra chuỗi rỗng → viên ngày mất cả nền.
  it('mã lạ rơi về xám chứ không rơi ra ngoài bảng màu', () => {
    for (const state of [-1, 4, 99]) {
      expect(expiryTone(state)).toBe('normal')
      expect(EXPIRY_TONE_CLASS[expiryTone(state)]).toBeTruthy()
    }
  })

  it('mọi mức khẩn đều có một lớp màu trong bảng', () => {
    expect(Object.keys(EXPIRY_TONE_CLASS).sort()).toEqual(['normal', 'overdue', 'soon'])
  })
})
