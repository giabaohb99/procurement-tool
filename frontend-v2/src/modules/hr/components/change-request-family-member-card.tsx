import { FAMILY_COLUMNS } from '../config/employee-family-columns'
import type { ChangeRequestFamilyRow } from '../types/employee-change-request'
import { formatPeopleCell } from '../utils/format-people-cell'

interface ChangeRequestFamilyMemberCardProps {
  member: ChangeRequestFamilyRow
  /** Vị trí trong danh sách (đếm từ 0) — in ra thành STT như cột đầu của bảng. */
  index: number
}

/**
 * Một người trong bảng hộ gia đình của màn duyệt sửa hồ sơ, ở khổ điện thoại — xem
 * `DataTableProps.mobileCard` và `ChangeRequestFamiliesDiff`.
 *
 * ⚠️ **Nghĩa "cũ → mới" nằm ở KHUNG, không ở thẻ.** Ba khối Lúc gửi / Hiện tại / Đề nghị vẫn
 * xếp dọc theo đúng thứ tự đó, mỗi khối có tiêu đề + số người; thẻ chỉ thay cho DÒNG trong khối.
 * Không so từng thẻ với thẻ cùng vị trí ở khối kia: đề nghị THAY CẢ danh sách và dòng không có
 * khóa chung, thêm một người ở đầu là mọi dòng lệch chỗ — tô "đã đổi" theo vị trí sẽ nói sai.
 *
 * ⚠️ **Ô trống vẫn in thành "—", không bỏ dòng.** Ở màn so sánh, "khối cũ trống CCCD, khối mới có
 * CCCD" chính là thay đổi người duyệt cần thấy; bỏ dòng thì hai thẻ trông khác nhau về hình dạng
 * mà không nói khác ở đâu. Mọi thẻ cùng một khuôn nhãn nên mắt dò được theo hàng.
 *
 * Trường lấy từ `FAMILY_COLUMNS` (cùng nguồn với bảng, ô nhập và bản in) — thêm cột ở đó là thẻ
 * tự có, không phải nhớ sửa hai nơi.
 */
export function ChangeRequestFamilyMemberCard({ member, index }: ChangeRequestFamilyMemberCardProps) {
  const detailColumns = FAMILY_COLUMNS.filter((col) => col.key !== 'full_name')

  return (
    <div className="flex items-start gap-2">
      {/*  STT là cột riêng, `leading-5` cho hộp dòng cao bằng dòng tên — để chung dòng tên thì mép
           trái của thẻ thành răng cưa. */}
      <span className="shrink-0 text-xs leading-5 tabular-nums text-muted-foreground">{index + 1}.</span>

      <div className="min-w-0 flex-1 space-y-1">
        <p className="truncate font-medium text-foreground">
          {member.full_name || <span className="text-muted-foreground italic">(chưa khai tên)</span>}
        </p>

        <dl className="grid grid-cols-[auto_minmax(0,1fr)] gap-x-3 gap-y-0.5 text-xs">
          {detailColumns.map((col) => (
            <div key={col.key} className="contents">
              <dt className="text-muted-foreground">{col.label}</dt>
              <dd className="truncate text-foreground tabular-nums">
                {formatPeopleCell(col.kind, member[col.key as keyof ChangeRequestFamilyRow]) || '—'}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  )
}
