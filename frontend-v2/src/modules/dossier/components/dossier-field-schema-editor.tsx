import { Loader2, Plus, Save } from 'lucide-react'
import { useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { useCrudSave } from '@/shared/crud'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { DossierFieldRow } from './dossier-field-row'
import {
  MAX_DOSSIER_FIELDS,
  emptyDossierField,
  type DossierFieldDef,
} from '../types/dossier-field'
import type { DossierType } from '../types/dossier-type'

/**
 * TRÌNH KHAI BỘ TRƯỜNG của một loại hồ sơ — phần «metadata» nhìn thấy được.
 *
 * Đây là chỗ người dùng tự định nghĩa biểu mẫu: khai ô nào ở đây thì màn lập hồ
 * sơ của loại đó mọc ra ô ấy, không phải chờ ai sửa mã nguồn.
 *
 * ⚠️ **NÚT LƯU RIÊNG, cửa API riêng** — component này nằm NGOÀI biểu mẫu CRUD
 * của loại hồ sơ (`CrudConfig.renderExtra` dựng nó ngoài thẻ `<form>`). Cùng
 * khuôn với hai bảng con của hồ sơ nhân sự. Nhét vào trong form chung thì Enter
 * ở một ô con sẽ submit form CHA, và người dùng lưu nhầm thứ khác rồi được báo
 * *thành công*.
 *
 * ⚠️ Chỉ hiện khi loại hồ sơ **đã tồn tại**. Khung CRUD không dựng `renderExtra`
 * ở chế độ tạo mới, và đó là đúng: chưa có id thì không PATCH vào đâu được.
 */
export function DossierFieldSchemaEditor({ type }: { type: DossierType }) {
  const { can } = usePermission()
  const canEdit = can('dossier_type', 'write')
  const once = useSingleFlight()
  const saveMutation = useCrudSave<DossierType>('/api/dossier-types', 'bộ trường')

  const [fields, setFields] = useState<DossierFieldDef[]>(type.field_schema ?? [])

  //  ⚠️ Nạp lại khi bản ghi về — chỉnh state NGAY TRONG LƯỢT VẼ, không dùng
  //  `useEffect`. Effect chạy SAU khi commit, nên nó vẽ một lượt bằng dữ liệu
  //  cũ rồi mới sửa: người dùng thấy bộ trường nhấp nháy đổi. ESLint
  //  (`react-hooks/set-state-in-effect`) cũng chặn đúng khuôn đó — xem cùng bài
  //  học ở `usePageResetOnFilterChange`.
  //
  //  So theo THAM CHIẾU của `type.field_schema` chứ không theo `type`: khung
  //  CRUD làm mới cả bản ghi mỗi lần lưu bất kỳ ô nào của loại hồ sơ, và nạp
  //  lại lúc đó là xóa sạch những ô người dùng đang gõ dở ở đây.
  const [loadedFrom, setLoadedFrom] = useState(type.field_schema)
  if (loadedFrom !== type.field_schema) {
    setLoadedFrom(type.field_schema)
    setFields(type.field_schema ?? [])
  }

  //  Mã trùng là ca hỏng NGẦM nhất: biểu mẫu vẫn hiện đủ hai ô, người dùng gõ
  //  hai giá trị, và chỉ một cái sống sót trong `extra_fields`. Backend chặn ở
  //  schema; ở đây chỉ tô đỏ sớm để họ thấy trước khi bấm Lưu.
  const keys = fields.map((f) => f.key)
  const duplicates = new Set(keys.filter((k) => k && keys.filter((x) => x === k).length > 1))
  const blank = fields.some((f) => !f.label.trim() || !f.key)
  const emptySelect = fields.some((f) => f.type === 'select' && f.options.length === 0)
  const invalid = duplicates.size > 0 || blank || emptySelect

  const move = (from: number, to: number) => {
    setFields((prev) => {
      const next = [...prev]
      const [row] = next.splice(from, 1)
      next.splice(to, 0, row)
      return next
    })
  }

  const remove = async (index: number) => {
    const field = fields[index]
    //  ⚠️ Nói rõ hậu quả: bỏ ô KHÔNG xóa dữ liệu ngay (backend cố ý giữ khóa
    //  không còn khai), nhưng nó làm giá trị cũ thành vô hình — không ô nào
    //  hiện nó nữa, và không còn lời giải nghĩa `so_gp` từng là gì.
    const ok = await confirm({
      message:
        `Bỏ ô «${field.label || field.key}» khỏi loại này? Hồ sơ đang giữ giá trị của ô đó ` +
        'vẫn còn dữ liệu dưới cơ sở dữ liệu, nhưng sẽ không màn hình nào hiện ra nữa.',
    })
    if (ok) setFields((prev) => prev.filter((_, i) => i !== index))
  }

  const save = () =>
    once(async () => {
      await saveMutation.mutateAsync({ id: type.id, values: { field_schema: fields } })
    })

  return (
    <Card className="@container gap-4 p-3 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold">Bộ trường của loại hồ sơ</h3>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Các ô riêng mà biểu mẫu lập hồ sơ sẽ mọc ra khi chọn loại này. Để trống cũng
            được — nhiều loại giấy tờ chỉ cần mã, tên và hạn.
          </p>
        </div>

        {canEdit && (
          <Button
            type="button"
            size="sm"
            onClick={save}
            disabled={saveMutation.isPending || invalid}
          >
            {saveMutation.isPending ? (
              <Loader2 className="animate-spin" />
            ) : (
              <Save />
            )}
            Lưu bộ trường
          </Button>
        )}
      </div>

      {fields.length === 0 ? (
        <p className="rounded-lg border border-dashed px-3 py-6 text-center text-sm text-muted-foreground">
          Chưa khai ô nào. Hồ sơ loại này chỉ có các ô dùng chung.
        </p>
      ) : (
        <div className="space-y-3">
          {fields.map((field, index) => (
            //  ⚠️ Khóa theo VỊ TRÍ, không theo `field.key`: mã trường đổi theo
            //  từng phím gõ ở ô «Tên ô» (nó tự gợi ý mã), nên lấy mã làm khóa là
            //  React hủy và dựng lại ô nhập sau mỗi ký tự — con trỏ nhảy về đầu
            //  ô và người dùng không gõ nổi một chữ. Dòng ở đây xáo trộn bằng
            //  nút Lên/Xuống chứ không bằng thứ tự dữ liệu, nên khóa vị trí an toàn.
            <DossierFieldRow
              key={index}
              field={field}
              index={index}
              total={fields.length}
              duplicateKey={Boolean(field.key) && duplicates.has(field.key)}
              disabled={!canEdit}
              onChange={(next) =>
                setFields((prev) => prev.map((f, i) => (i === index ? next : f)))
              }
              onMove={move}
              onRemove={() => void remove(index)}
            />
          ))}
        </div>
      )}

      {canEdit && (
        <div className="flex flex-wrap items-center gap-3">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={fields.length >= MAX_DOSSIER_FIELDS}
            onClick={() => setFields((prev) => [...prev, emptyDossierField()])}
          >
            <Plus />
            Thêm ô
          </Button>
          <span className="text-xs text-muted-foreground">
            {fields.length}/{MAX_DOSSIER_FIELDS} ô
          </span>
          {/*  Nói LÝ DO nút Lưu đang xám. Nút mờ không giải thích là người dùng
               bấm mấy lần rồi đi tìm lỗi ở chỗ khác. */}
          {invalid && (
            <span className="text-xs text-destructive">
              {duplicates.size > 0
                ? 'Có mã trường trùng nhau.'
                : blank
                  ? 'Còn ô chưa đặt tên.'
                  : 'Ô chọn phải có ít nhất một mục.'}
            </span>
          )}
        </div>
      )}
    </Card>
  )
}
