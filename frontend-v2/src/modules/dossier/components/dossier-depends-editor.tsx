import { useQuery } from '@tanstack/react-query'
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form'
import { useParams } from 'react-router-dom'

import { apiGet } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { queryKeys } from '@/shared/constants/query-keys'
import { CollapsibleSection } from '@/shared/ui/collapsible-section'
import { MultiPicker } from '@/shared/ui/multi-picker'
import { MAX_DOSSIER_DEPENDS, type Dossier } from '../types/dossier'

interface DossierDependsEditorProps<T extends FieldValues> {
  control: Control<T>
  name: Path<T>
  disabled?: boolean
}

/** Bộ trường vừa đủ cho ô chọn — không kéo cả hồ sơ về. */
type Candidate = Pick<Dossier, 'id' | 'code' | 'name' | 'dossier_type_name'>

/**
 * KHAI HỒ SƠ TIÊN QUYẾT — *«tờ này chỉ làm được sau khi mấy tờ kia xong»*.
 *
 * ⚠️ **Khai MỘT lần cho cả kho, ở đây.** Trình tự giấy tờ của công ty là một:
 * đơn mua hàng chỉ phát hành sau khi hợp đồng ký xong, ở mọi thương vụ. Thẻ
 * *Hồ sơ cần hoàn thành* trên các trang chứng từ chỉ ĐỌC ràng buộc này để vẽ
 * ổ khóa — bên đó không khai được, và không nên khai được.
 *
 * ⚠️ Nhưng **«xong» thì vẫn theo từng phiếu**, nên một tờ đang khóa ở phiếu A
 * có thể đã mở ở phiếu B. Ràng buộc dùng chung, trạng thái riêng.
 *
 * ⚠️ **Vòng lặp do BACKEND chặn**, ở đây không dò lại (`depends_service.py`).
 * Hai bản luật sẽ lệch nhau, và bản lệch cho lọt một vòng thì cả cụm khóa vĩnh
 * viễn trên MỌI phiếu — không riêng một tờ phiếu như bản theo-phiếu trước đây.
 *
 * ⚠️ Dùng `MultiPicker` chứ KHÔNG tự dựng danh sách tick tại chỗ. Bản đầu đổ
 * thẳng cả 40+ tờ vào một ô cuộn cao 13rem nằm giữa biểu mẫu: cuộn-trong-cuộn,
 * dòng trên cùng luôn bị cắt ngang, và chiều cao đó chiếm chỗ ngay cả khi
 * không khai gì. Ô chọn nhiều mục dùng chung đã giải xong mấy chuyện đó (tìm
 * có bỏ dấu, chip gộp «+n», trần số dòng) và giống hệt mọi ô khác trong app.
 */
export function DossierDependsEditor<T extends FieldValues>({
  control,
  name,
  disabled,
}: DossierDependsEditorProps<T>) {
  const { can } = usePermission()
  //  ⚠️ Id lấy từ URL (`/dossier/list/:id`), KHÔNG lấy từ giá trị biểu mẫu:
  //  biểu mẫu không có ô `id` nên `values.id` là `undefined`, và khi đó chính
  //  tờ đang sửa vẫn nằm trong danh sách — tick được «chờ chính mình» rồi ăn
  //  400 ở lượt lưu. Trang TẠO MỚI có `id = 'new'` → `NaN` → `0`, đúng ý.
  const { id } = useParams()
  const currentId = Number(id) || 0

  //  Kho hồ sơ cỡ trăm dòng nên kéo một lượt rồi lọc tại chỗ — rẻ hơn và mượt
  //  hơn gọi lại theo từng ký tự gõ. Tự tắt khi thiếu quyền đọc, kẻo mở biểu
  //  mẫu là ăn một toast 403.
  const { data } = useQuery({
    queryKey: queryKeys.dossier.candidates(),
    queryFn: () =>
      apiGet<{ items: Candidate[] }>(
        '/api/dossiers?page=1&page_size=500&sort_by=name&sort_dir=asc',
      ),
    enabled: can('dossier', 'read'),
  })

  const options = (data?.items ?? [])
    .filter((item) => item.id !== currentId)
    .map((item) => ({ id: item.id, label: item.name, hint: item.dossier_type_name }))

  return (
    <Controller
      control={control}
      name={name}
      render={({ field }) => {
        const picked: number[] = Array.isArray(field.value) ? field.value : []
        return (
          <CollapsibleSection
            title="Hồ sơ tiên quyết"
            description="Tờ hồ sơ này chỉ làm được sau khi những tờ chọn dưới đây hoàn thành ở chính chứng từ đó. Khai một lần, dùng chung cho mọi chứng từ."
            summary={picked.length > 0 ? `chờ ${picked.length} hồ sơ` : 'không có'}
            storageKey="dossier.depends"
            //  ⚠️ Chưa khai gì thì GẬP SẴN, cùng lẽ với khối «Điều kiện áp
            //  dụng»: phần lớn hồ sơ không có tiên quyết, mở sẵn một khối rỗng
            //  ở mọi tờ là bắt tất cả cuộn qua thứ hầu hết không dùng.
            defaultOpen={picked.length > 0}
          >
            <MultiPicker
              value={picked}
              //  Chạm trần thì cắt bớt thay vì chặn im: người dùng vừa bấm một
              //  dòng mà không có gì xảy ra là thứ họ báo là lỗi. Backend cũng
              //  chặn ở `check_depends`, đây chỉ là gác sớm cho đỡ mất công.
              onChange={(ids) => field.onChange(ids.slice(0, MAX_DOSSIER_DEPENDS))}
              options={options}
              placeholder="Chọn hồ sơ phải xong trước…"
              searchPlaceholder="Tìm theo tên hoặc loại…"
              emptyMessage="Kho chưa có hồ sơ nào khác."
              disabled={disabled}
              //  ⚠️ Bỏ «Chọn tất cả»: chọn mọi tờ trong kho làm tiên quyết cho
              //  một tờ thì tờ đó khóa gần như vĩnh viễn, mà nút lại nằm đúng
              //  chỗ dễ bấm nhầm nhất — ngay trên mục đầu tiên. Ở đây người
              //  dùng chọn một hai tờ, không bao giờ chọn hết.
              hideSelectAll
              //  ⚠️ Chip NẰM TRONG khung, không rải thành dải riêng bên dưới.
              //  Dải riêng làm ô này cao hai hàng cho đúng một lựa chọn, mà
              //  hàng trên chỉ ghi «Đã chọn 1» — phải nhìn xuống hàng dưới mới
              //  biết chọn tờ nào. Ở đây thường chỉ một hai tờ nên chip vừa
              //  khung, và khung tự giãn khi nhiều hơn.
              chipsInTrigger
              //  Dấu X «bỏ hết» vào luôn trong khung, cùng lý do gộp hàng.
              clearInTrigger
              //  Nhãn hồ sơ dài («Hợp đồng mua bán / hợp đồng nguyên tắc»), ô
              //  mặc định `w-80` là cụt ngay ở dòng đầu.
              contentClassName="w-[28rem]"
            />
          </CollapsibleSection>
        )
      }}
    />
  )
}
