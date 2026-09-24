import { Plus } from 'lucide-react'
import { useState } from 'react'
import { useController, type Control } from 'react-hook-form'

import type { CrudRecord } from '@/shared/crud'
import { Button } from '@/shared/ui/button'
import { CollapsibleSection } from '@/shared/ui/collapsible-section'
import { MAX_DOSSIER_FIELDS, type DossierFieldDef } from '../types/dossier-field'
import {
  emptyCustomRow,
  reseedFromType,
  type DossierCustomRow,
} from '../types/dossier-custom-row'
import { DossierCustomFieldRow } from './dossier-custom-field-row'
import { firstProblem, problemOf } from './dossier-custom-fields-problem'

interface DossierCustomFieldsEditorProps {
  control: Control<CrudRecord>
  name: string
  disabled?: boolean
  /** Loại đang chọn — đổi số này là đổ lại khuôn. `0` = chưa chọn. */
  typeId: number
  /** Bộ trường KHUÔN của một loại. Tra được cả loại VỪA BỎ chọn, xem `reseedFromType`. */
  defsOfType: (typeId: number) => DossierFieldDef[]
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
  typeId,
  defsOfType,
}: DossierCustomFieldsEditorProps) {
  //  ⚠️ **CHẶN SUBMIT, không chỉ tô đỏ.** Cảnh báo suông thì người dùng vẫn bấm
  //  được «Tạo hồ sơ» và nhận một câu 422 của backend — cùng nội dung nhưng ở
  //  dạng toast, rời khỏi đúng cái hàng đang sai. Gắn luật vào `useController`
  //  thì react-hook-form giữ form lại và câu nhắc nằm ngay dưới hàng đó.
  const { field, fieldState } = useController({
    control,
    name,
    rules: {
      validate: (value) => firstProblem(Array.isArray(value) ? value : []) ?? true,
    },
  })
  const rows: DossierCustomRow[] = Array.isArray(field.value) ? field.value : []

  const setRows = (next: DossierCustomRow[]) => field.onChange(next)

  //  ⚠️ **ĐỔ KHUÔN khi đổi loại** — chỉnh state NGAY TRONG LƯỢT VẼ, không dùng
  //  `useEffect`. Effect chạy sau khi commit nên bảng vẽ một lượt với khuôn CŨ
  //  rồi mới đổi: người dùng thấy các dòng nhấp nháy thay nhau. ESLint
  //  (`react-hooks/set-state-in-effect`) cũng chặn đúng khuôn đó.
  //
  //  ⚠️ `seededFor` khởi tạo bằng CHÍNH `typeId` hiện tại, không phải `0`. Lúc
  //  MỞ MỘT HỒ SƠ CŨ, `typeId` đã có sẵn từ bản ghi — khởi tạo `0` thì lượt vẽ
  //  đầu tưởng người dùng vừa đổi loại và **đổ khuôn đè lên bộ trường đã lưu**,
  //  xóa sạch những dòng mà tờ đó đã cố tình sửa khác khuôn.
  const [seededFor, setSeededFor] = useState(typeId)
  if (seededFor !== typeId) {
    setSeededFor(typeId)
    setRows(reseedFromType(rows, defsOfType(seededFor), defsOfType(typeId)))
  }

  const clashOf = (row: DossierCustomRow, index: number) => problemOf(row, index, rows)

  return (
    <CollapsibleSection
      title="Trường riêng của hồ sơ này"
      description={
        <>
          Ô chỉ tờ hồ sơ này cần, không đụng tới khuôn của loại. Nhu cầu nào lặp lại ở
          nhiều hồ sơ thì nên khai ở màn <strong>Loại hồ sơ</strong> để cả công ty dùng chung.
        </>
      }
      summary={rows.length === 0 ? 'chưa có trường nào' : `${rows.length} trường`}
      storageKey="dossier.custom-fields"
      //  ⚠️ Có ô sai thì ÉP MỞ. Câu báo lỗi nằm trong khối đang gập thì người
      //  dùng bấm Lưu và không thấy gì xảy ra — react-hook-form chặn submit
      //  trong im lặng tuyệt đối (bẫy thứ nhất của duoc-CR-317).
      forceOpen={Boolean(fieldState.error)}
    >
      <div className="px-3 py-3 sm:px-4">
        {rows.length === 0 ? (
          <p className="rounded-lg border border-dashed px-3 py-5 text-center text-sm text-muted-foreground">
            Chưa có trường riêng nào. Hồ sơ này chỉ dùng các ô của loại.
          </p>
        ) : (
          //  Khổ rộng: các hàng dính liền nhau như một bảng, phân định bằng
          //  đường kẻ của chính từng hàng. Khổ hẹp: mỗi hàng là một thẻ rời,
          //  nên phải có khoảng hở giữa chúng.
          <div className="space-y-2 @2xl:space-y-0">
            {/*  Tiêu đề cột CHỈ ở khổ rộng; khổ hẹp mỗi ô tự mang nhãn của nó
                 (xem `DossierCustomFieldRow`), vì bốn cột không xếp ngang nổi
                 trên 390px.
                 ⚠️ Bề rộng cột ở đây phải KHỚP TỪNG SỐ với lưới của
                 `DossierCustomFieldRow` — lệch một con số là tiêu đề trỏ nhầm
                 cột, mà không có gì đỏ lên để báo. */}
            <div className="hidden gap-2 border-b border-border/60 pb-1.5 text-xs font-medium text-muted-foreground @2xl:grid @2xl:grid-cols-[minmax(0,1fr)_184px_84px_minmax(0,1fr)_36px]">
              <span>Tên trường</span>
              <span>Kiểu</span>
              <span className="text-center">Bắt buộc</span>
              <span>Giá trị</span>
              <span />
            </div>

            {rows.map((row, index) => (
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
            ))}
          </div>
        )}

        {!disabled && (
          <div className="flex flex-wrap items-center gap-3 pt-3">
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
            {/*  ⚠️ Nói LÝ DO không lưu được, ngay cạnh nút. Không có dòng này
                 thì bấm «Tạo hồ sơ» là **không có gì xảy ra** — react-hook-form
                 chặn submit trong im lặng tuyệt đối (bẫy thứ nhất của
                 duoc-CR-317), và câu nhắc của từng hàng thì có thể đang nằm
                 ngoài tầm mắt nếu danh sách dài. */}
            {fieldState.error?.message && (
              <span className="text-xs text-destructive">
                {fieldState.error.message}
              </span>
            )}
          </div>
        )}
      </div>
    </CollapsibleSection>
  )
}
