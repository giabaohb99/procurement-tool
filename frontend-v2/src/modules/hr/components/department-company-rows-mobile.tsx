import type { ReactNode } from 'react'

/** Một dòng «pháp nhân áp dụng» đã dựng sẵn năm ô điều khiển. */
export interface DepartmentCompanyRowView {
  key: string
  /** Dòng của pháp nhân GỐC — không bỏ, không tắt được. */
  isPrimary: boolean
  company: ReactNode
  manager: ReactNode
  issueCode: ReactNode
  active: ReactNode
  /** `null` khi người xem không có quyền sửa. */
  remove: ReactNode
}

/**
 * Bảng «Pháp nhân áp dụng» ở khổ ĐIỆN THOẠI — mỗi dòng thành một khối xếp dọc.
 *
 * ⚠️ **Đây là bảng SỬA ĐƯỢC, nên không cuộn ngang được như bảng chỉ-đọc.** Năm
 * cột khai bề rộng tối thiểu cộng lại **856px**; trên máy 390px thì mỗi ô điều
 * khiển chỉ ló ra một mẩu, mà chúng lại là ô chọn và ô nhập — người dùng phải
 * cuộn ngang để bấm trúng, rồi cuộn ngược lại để đọc xem mình vừa sửa dòng nào.
 * Bảng chỉ-đọc còn cuộn ngang tạm được; bảng nhập liệu thì không.
 *
 * ⚠️ **Mỗi ô phải có NHÃN.** Trong bảng, tiêu đề cột giải nghĩa cho cả cột; xếp
 * dọc là mất tiêu đề đó, và ba ô chọn liên tiếp không nhãn thì không cách nào
 * biết ô nào là pháp nhân, ô nào là trưởng bộ phận. Cùng lý do `QuickFilterField`
 * bắt buộc có nhãn trong tờ trượt lọc.
 *
 * ⚠️ Dòng GỐC vẫn dựng đủ ô nhưng chúng tự khóa (do phía gọi truyền `disabled`),
 * và mang huy hiệu «Gốc» — giấu bớt ô của riêng dòng này thì hai dòng cạnh nhau
 * có hình dạng khác nhau, đọc ra như một lỗi vẽ chứ không ra một luật.
 */
export function DepartmentCompanyRowsMobile({
  rows,
  emptyMessage,
}: {
  rows: DepartmentCompanyRowView[]
  emptyMessage: ReactNode
}) {
  if (rows.length === 0) {
    return <div className="py-8 text-center text-sm text-muted-foreground">{emptyMessage}</div>
  }

  return (
    <div className="space-y-3">
      {rows.map((row) => (
        <div key={row.key} className="space-y-2.5 rounded-lg border p-3">
          <Field label="Pháp nhân">{row.company}</Field>
          <Field label="Trưởng bộ phận tại pháp nhân">{row.manager}</Field>
          <Field label="Mã phòng ban riêng">{row.issueCode}</Field>

          {/*  Hàng chân: công tắc «Áp dụng» bên trái, nút bỏ dòng dạt hẳn sang
               phải — cùng khuôn với chân một hộp thoại, để thao tác PHÁ nằm xa
               thao tác thường dùng. */}
          <div className="flex items-center justify-between gap-2 border-t pt-2.5">
            <label className="flex items-center gap-2 text-sm">
              {row.active}
              <span>Áp dụng</span>
            </label>
            {row.remove}
          </div>
        </div>
      ))}
    </div>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-1.5">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      {children}
    </div>
  )
}
