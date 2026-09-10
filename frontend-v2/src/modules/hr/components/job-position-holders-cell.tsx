import { usePermission } from '@/core/authorization/use-permission'
import {
  Avatar,
  AvatarFallback,
  AvatarGroup,
  AvatarGroupCount,
  AvatarImage,
} from '@/shared/ui/avatar'
import { departmentInitials, nameInitials } from '@/shared/utils/name-initials'
import { useJobPositionStats } from '../hooks/use-job-positions'
import type { JobPositionHolderFace } from '../types/job-position'

/**
 * Hai ô của bảng Chức vụ, cùng dùng cụm ảnh xếp chồng nhưng trả lời hai câu
 * KHÁC nhau (duoc-CR-322): «Đang giữ» xếp ảnh của NGƯỜI, «Phòng ban đang giữ»
 * xếp ảnh của PHÒNG BAN. Xếp cùng một thứ ở cả hai thì cột sau chỉ là bản chép
 * của cột trước.
 *
 * ⚠️ Cả hai đọc CÙNG một hook `useJobPositionStats`. Trông như 13 dòng gọi 13
 * lần, nhưng khóa truy vấn là một hằng nên react-query gộp thành **một** lời
 * gọi cho cả bảng — đúng lý do backend gom sẵn bằng `GROUP BY` thay vì nhét
 * `employee_count` vào serializer của từng dòng.
 *
 * ⚠️ Thiếu `employee.read` thì **không gọi và không hiện gì**. Backend không ném
 * 403 (nó lọc theo phạm vi rồi trả rỗng), nên gọi lúc thiếu quyền là mọi dòng
 * trống trơn — người đọc kết luận "chưa ai giữ chức vụ nào", sai hoàn toàn. Dấu
 * gạch «—» nói *không có thông tin*, chữ «Chưa ai giữ» nói *không có người*.
 */

//  Số ảnh xếp chồng trong một ô bảng. Quá ngần này thì các vòng tròn che nhau
//  gần hết trong ô cao 35px và không còn là gương mặt nữa, chỉ là một vệt tròn.
const FACES_IN_POSITION_CELL = 4
//  Phòng ban thì hiện nhiều hơn một chút: vòng tròn chữ viết tắt của phòng luôn
//  ĐỦ hai ký tự và không có ảnh thật chen vào, nên đọc rõ hơn cụm gương mặt.
const DEPARTMENTS_IN_CELL = 5
//  Thẻ ở khổ điện thoại xếp ít mặt hơn ô bảng: cụm ảnh ở đó đứng CÙNG DÒNG với
//  câu «N người · phòng nào», nên mỗi vòng tròn thêm vào là một mẩu chữ bị cắt.
const FACES_IN_CARD = 3

/**
 * Cụm ảnh xếp chồng + «+N» cho phần không hiện hết.
 *
 * ⚠️ `total` truyền vào là con số ĐẾM THẬT, không phải `faces.length`: backend
 * chỉ gửi vài gương mặt mẫu, lấy độ dài mảng đó làm tổng thì một phòng 40 người
 * hiện ra «+0» và cụm ảnh nói dối.
 */
function HolderAvatarStack({
  faces,
  total,
  limit,
  title,
}: {
  faces: JobPositionHolderFace[]
  total: number
  limit: number
  title: string
}) {
  const shown = faces.slice(0, limit)
  const rest = total - shown.length

  return (
    //  ⚠️ Đè ít thôi (`-space-x-1`, mặc định của `AvatarGroup` là `-space-x-2`).
    //  Vòng tròn `size-6` mà đè 8px thì chỉ còn 16px lộ ra, và phần lộ ra đó
    //  KHÔNG đủ cho hai chữ viết tắt — chúng bị cái ảnh kế tiếp cắt mất nửa
    //  phải, cả cụm đọc thành một vệt chữ dính nhau. Ảnh thật thì đè sâu vẫn
    //  đẹp, nhưng ở đây phần lớn hồ sơ CHƯA có ảnh (phải được cấp tài khoản mới
    //  có), nên trường hợp thường gặp là chữ viết tắt chứ không phải ảnh.
    <AvatarGroup title={title} className="-space-x-1">
      {shown.map((holder) => (
        <Avatar key={holder.id} size="sm" title={holder.full_name}>
          {holder.avatar && <AvatarImage src={holder.avatar} alt={holder.full_name} />}
          {/*  Nền đậm hơn `bg-muted` mặc định: vòng viền của `AvatarGroup` là
              `ring-background`, tức TRẮNG trên nền hàng trắng — không có nền
              tương phản thì các vòng tròn không có ranh giới nhìn thấy được. */}
          <AvatarFallback className="bg-primary/10 text-[10px] font-medium text-primary">
            {nameInitials(holder.full_name)}
          </AvatarFallback>
        </Avatar>
      ))}
      {rest > 0 && (
        <AvatarGroupCount className="bg-muted text-[10px] font-medium">+{rest}</AvatarGroupCount>
      )}
    </AvatarGroup>
  )
}

/** Ai đang giữ chức vụ này — gộp cả công ty (trong phạm vi dữ liệu người xem). */
export function JobPositionHolderCount({ positionId }: { positionId: number }) {
  const { can } = usePermission()
  const allowed = can('employee', 'read')
  const { data, isLoading } = useJobPositionStats(allowed)

  if (!allowed) return <span className="text-muted-foreground/50">—</span>
  if (isLoading) return <span className="text-muted-foreground/50">…</span>

  const stat = data?.get(positionId)
  const total = stat?.total ?? 0
  if (!total) return <span className="text-sm text-muted-foreground/50">Chưa ai giữ</span>

  return (
    <HolderAvatarStack
      faces={stat?.holders ?? []}
      total={total}
      limit={FACES_IN_POSITION_CELL}
      title={`${total} người đang giữ chức vụ này`}
    />
  )
}

/**
 * MỘT DÒNG gộp cả «ai giữ» lẫn «phòng nào» — dành cho thẻ ở khổ điện thoại.
 *
 * Thẻ không có tiêu đề cột nên hai cụm ảnh xếp cạnh nhau sẽ đọc thành một dãy
 * vòng tròn vô nghĩa; ở đây gộp lại và **gọi tên phòng bằng CHỮ đầy đủ**, thứ
 * mà ô bảng rộng 170px không chứa nổi nên mới phải viết tắt.
 *
 * ⚠️ Thiếu quyền `employee.read` thì trả về `null`, KHÔNG trả dấu «—» như ô
 * bảng: trong bảng dấu gạch nằm dưới tiêu đề «Đang giữ» nên đọc ra *chưa có
 * thông tin*, còn trên thẻ nó là một gạch ngang trơ trọi giữa hai dòng chữ,
 * không nói được gì cả.
 */
export function JobPositionHoldersLine({ positionId }: { positionId: number }) {
  const { can } = usePermission()
  const allowed = can('employee', 'read')
  const { data, isLoading } = useJobPositionStats(allowed)

  if (!allowed || isLoading) return null

  const stat = data?.get(positionId)
  const total = stat?.total ?? 0
  //  «Chưa ai giữ» là thứ ĐÁNG nhặt ra ở màn này (chức vụ khai rồi mà bỏ không),
  //  nên vẫn nói thành lời chứ không im lặng như hai ca trên.
  if (!total) return <span className="block">Chưa ai giữ</span>

  const departments = stat?.departments ?? []

  return (
    <span className="flex items-center gap-1.5">
      <HolderAvatarStack
        faces={stat?.holders ?? []}
        total={total}
        limit={FACES_IN_CARD}
        title={`${total} người đang giữ chức vụ này`}
      />
      <span className="truncate">
        {total} người
        {departments.length > 0 && ` · ${departments.map((d) => d.name).join(', ')}`}
      </span>
    </span>
  )
}

/**
 * Những PHÒNG BAN đang có người giữ chức vụ này — mỗi phòng MỘT vòng tròn mang
 * chữ viết tắt tên phòng, đông người nhất đứng trước.
 *
 * ⚠️ Đây là ảnh của **phòng ban**, không phải của người trong phòng. Bản trước
 * xếp ảnh từng nhân viên theo phòng, và trên cùng một dòng nó lặp lại đúng nhóm
 * gương mặt của cột «Đang giữ» ngay bên cạnh — hai cột nói cùng một điều, cột
 * này mất hẳn phần trả lời câu hỏi của chính nó là *phòng nào*.
 *
 * Tên phòng đầy đủ nằm ở `title` (rê chuột) và ở tab «Người đang giữ».
 */
export function JobPositionDepartments({ positionId }: { positionId: number }) {
  const { can } = usePermission()
  const allowed = can('employee', 'read')
  const { data, isLoading } = useJobPositionStats(allowed)

  if (!allowed || isLoading) return <span className="text-muted-foreground/50">—</span>

  const departments = data?.get(positionId)?.departments ?? []
  if (departments.length === 0) return <span className="text-muted-foreground/50">—</span>

  const shown = departments.slice(0, DEPARTMENTS_IN_CELL)
  const rest = departments.length - shown.length

  return (
    <AvatarGroup
      className="-space-x-1"
      title={departments.map((d) => `${d.name} (${d.count})`).join(' · ')}
    >
      {shown.map((dept) => (
        <Avatar key={dept.id} size="sm" title={`${dept.name} — ${dept.count} người`}>
          {/*  Không có `AvatarImage`: phòng ban không có ảnh đại diện, vòng tròn
              LUÔN là chữ viết tắt. Tông khác cột người bên cạnh để hai cụm ảnh
              trên cùng một dòng không đọc thành một dãy. */}
          <AvatarFallback className="bg-secondary text-[10px] font-medium text-secondary-foreground">
            {departmentInitials(dept.name)}
          </AvatarFallback>
        </Avatar>
      ))}
      {rest > 0 && (
        <AvatarGroupCount className="bg-muted text-[10px] font-medium">+{rest}</AvatarGroupCount>
      )}
    </AvatarGroup>
  )
}
