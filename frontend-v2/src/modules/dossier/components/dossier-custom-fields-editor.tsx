import { Plus } from 'lucide-react'
import { useController, type Control } from 'react-hook-form'

import type { CrudRecord } from '@/shared/crud'
import { Button } from '@/shared/ui/button'
import { MAX_DOSSIER_FIELDS } from '../types/dossier-field'
import {
  emptyCustomRow,
  type DossierCustomRow,
} from '../types/dossier-custom-row'
import { DossierCustomFieldRow } from './dossier-custom-field-row'

interface DossierCustomFieldsEditorProps {
  control: Control<CrudRecord>
  name: string
  disabled?: boolean
  /** Mã ô do LOẠI hồ sơ khai — trường riêng không được trùng vào đó. */
  typeKeys: Set<string>
}

/**
 * TRƯỜNG RIÊNG CỦA HỒ SƠ NÀY — khai tên · kiểu · bắt buộc · giá trị ngay tại chỗ.
 *
 * Khác trình khai bên màn *Loại hồ sơ* ở chỗ căn bản: cái đó sửa KHUÔN cho mọi
 * hồ sơ cùng loại, còn cái này chỉ thuộc về đúng tờ đang mở. Vì thế khai báo và
 * giá trị đứng CHUNG một hàng — người dùng nghĩ về chúng như một việc.
 *
 * ⚠️ Nối thẳng vào form của khung CRUD bằng `useController`, KHÔNG giữ state
 * riêng. Hai lý do:
 *   * màn THÊM MỚI chưa có bản ghi nên không tách ra khối lưu riêng được
 *     (`renderExtra` chỉ dựng khi đã có bản ghi);
 *   * giữ state riêng rồi đồng bộ lại là hai nguồn sự thật cho một ô, và chúng
 *     sẽ lệch nhau ở đúng lần `reset` mà không ai ngờ tới.
 *
 * ⚠️ Dữ liệu ở đây là **hình dạng của biểu mẫu**, không phải của kho: lúc gửi,
 * `buildPayload` tách một hàng thành khai báo (`custom_fields`) và giá trị
 * (`extra_fields`) — xem `dossier-custom-row.ts`.
 */
export function DossierCustomFieldsEditor({
  control,
  name,
  disabled,
  typeKeys,
}: DossierCustomFieldsEditorProps) {
  const { field } = useController({ control, name })
  const rows: DossierCustomRow[] = Array.isArray(field.value) ? field.value : []

  const setRows = (next: DossierCustomRow[]) => field.onChange(next)

  //  Hai kiểu đụng khóa, hai câu khác nhau — nói chung một câu thì người dùng
  //  không biết phải đi sửa ở đâu.
  const keys = rows.map((r) => r.key)
  const clashOf = (row: DossierCustomRow, index: number): string | undefined => {
    if (!row.key) return undefined
    if (typeKeys.has(row.key)) {
      return `«${row.key}» đã là ô sẵn có của loại hồ sơ — điền thẳng vào ô đó ở trên, hoặc đổi tên trường này.`
    }
    if (keys.indexOf(row.key) !== index) {
      return `«${row.key}» trùng với một trường riêng khác. Hai ô cùng mã thì chỉ một giá trị được lưu.`
    }
    return undefined
  }

  return (
    <section className="@container rounded-lg border bg-card">
      <header className="border-b bg-muted/30 px-3 py-2.5 sm:px-4">
        <h3 className="text-sm font-semibold">Trường riêng của hồ sơ này</h3>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Ô chỉ tờ hồ sơ này cần, không đụng tới khuôn của loại. Nhu cầu nào lặp lại ở
          nhiều hồ sơ thì nên khai ở màn <strong>Loại hồ sơ</strong> để cả công ty dùng chung.
        </p>
      </header>

      <div className="space-y-2 px-3 py-3 sm:px-4">
        {rows.length > 0 && (
          //  Tiêu đề cột CHỈ ở khổ rộng; khổ hẹp mỗi ô tự mang nhãn của nó
          //  (xem `DossierCustomFieldRow`), vì bốn cột không xếp ngang nổi
          //  trên 390px.
          <div className="hidden gap-2 px-2.5 text-xs font-medium text-muted-foreground @2xl:grid @2xl:grid-cols-[minmax(0,1fr)_130px_92px_minmax(0,1.3fr)_auto]">
            <span>Tên trường</span>
            <span>Kiểu</span>
            <span className="text-center">Bắt buộc</span>
            <span>Giá trị</span>
            <span className="w-9" />
          </div>
        )}

        {rows.length === 0 ? (
          <p className="rounded-lg border border-dashed px-3 py-5 text-center text-sm text-muted-foreground">
            Chưa có trường riêng nào. Hồ sơ này chỉ dùng các ô của loại.
          </p>
        ) : (
          rows.map((row, index) => (
            //  ⚠️ Khóa theo VỊ TRÍ, không theo `row.key`: mã đổi theo từng phím
            //  gõ ở ô «Tên trường» (nó tự gợi ý mã), nên lấy mã làm khóa là React
            //  hủy và dựng lại ô nhập sau mỗi ký tự — con trỏ nhảy về đầu ô.
            <DossierCustomFieldRow
              key={index}
              row={row}
              index={index}
              clashWith={clashOf(row, index)}
              disabled={disabled}
              onChange={(next) => setRows(rows.map((r, i) => (i === index ? next : r)))}
              onRemove={() => setRows(rows.filter((_, i) => i !== index))}
            />
          ))
        )}

        {!disabled && (
          <div className="flex flex-wrap items-center gap-3 pt-1">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={rows.length >= MAX_DOSSIER_FIELDS}
              onClick={() => setRows([...rows, emptyCustomRow()])}
            >
              <Plus />
              Thêm trường
            </Button>
            <span className="text-xs text-muted-foreground">
              {rows.length}/{MAX_DOSSIER_FIELDS} trường
            </span>
          </div>
        )}
      </div>
    </section>
  )
}
