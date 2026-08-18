import { AlertTriangle } from 'lucide-react'
import { useState } from 'react'

import { useActiveDocumentTypes } from '@/modules/document/hooks/use-document-types'
import { useDocuments } from '@/modules/document/hooks/use-documents'
import { Label } from '@/shared/ui/label'
import { MultiPicker } from '@/shared/ui/multi-picker'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import {
  buildScopeCondition,
  laDieuKienNangCao,
  parseScope,
  SCOPE_LABELS,
  type FlowScopeKind,
} from '../helpers/flow-scope'

interface FlowScopePickerProps {
  /** Chuỗi điều kiện đang lưu trên luồng. */
  condition: string
  onChange: (condition: string) => void
  /** Luồng của loại chứng từ khác văn bản thì chưa có bộ chọn riêng. */
  entity: string
}

/**
 * "Luồng này áp cho phiếu nào" — **thay cho ô gõ JSON**.
 *
 * Người khai luồng là người làm nghiệp vụ, không phải người viết mã. Bắt họ gõ
 * `[{"field":"doc_type_id","op":"in","value":[3]}]` là bắt họ học một thứ chỉ
 * dùng đúng một lần, và gõ sai một dấu ngoặc thì luồng im lặng không chạy.
 *
 * Ba lựa chọn, dừng ở ba. Điều kiện phức tạp hơn (theo số tiền, theo pháp nhân)
 * khai ở phần **rẽ nhánh của từng bước** — chỗ đó mới thật sự cần.
 */
export function FlowScopePicker({ condition, onChange, entity }: FlowScopePickerProps) {
  const daLuu = parseScope(condition)
  const nangCao = laDieuKienNangCao(condition)

  //  Kiểu đang chọn giữ ở state RIÊNG, không suy thẳng từ chuỗi điều kiện.
  //  Chuỗi chỉ mang được lựa chọn ĐÃ ĐỦ: chọn «một số loại văn bản» mà chưa tick
  //  loại nào thì `buildScopeCondition` trả chuỗi rỗng, đọc ngược lại ra «tất
  //  cả» — nên bộ chọn bật lại về dòng đầu và ô tick không bao giờ hiện ra.
  const [kind, setKind] = useState<FlowScopeKind>(daLuu.kind)
  const ids = daLuu.kind === kind ? daLuu.ids : []

  const docTypes = useActiveDocumentTypes()
  //  Chỉ nạp danh sách văn bản khi người dùng thật sự chọn tới lựa chọn đó —
  //  đây là bảng lớn nhất của phân hệ.
  const { data: documents } = useDocuments(
    kind === 'document' ? { page_size: 200 } : { page_size: 1 },
  )

  const laVanBan = entity === 'document'

  function doiKieu(kindMoi: FlowScopeKind) {
    setKind(kindMoi)
    onChange(buildScopeCondition({ kind: kindMoi, ids: kindMoi === kind ? ids : [] }))
  }

  if (!laVanBan) {
    //  Loại chứng từ khác chưa có bộ chọn riêng — nói thẳng thay vì bày một ô
    //  chọn rỗng không giải thích được.
    return (
      <div className="space-y-2">
        <Label>Áp cho phiếu nào</Label>
        <p className="text-sm text-muted-foreground">
          Loại chứng từ này chưa có bộ chọn riêng — luồng áp cho <b>mọi phiếu</b> của loại
          đó. Cần lọc hẹp hơn thì khai điều kiện ở phần rẽ nhánh của từng bước.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <Label>Áp cho phiếu nào</Label>

      {/*  Điều kiện gõ tay từ trước KHÔNG được lặng lẽ ghi đè — người khai
           trước có thể đã viết đúng một điều kiện mà bộ chọn chưa hiểu. */}
      {nangCao ? (
        <div className="space-y-1.5 rounded-md border border-amber-300 bg-amber-50 px-3 py-2">
          <p className="flex items-start gap-2 text-sm text-amber-900">
            <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
            <span>
              Luồng này đang dùng một điều kiện <b>khai tay</b>, phức tạp hơn thứ bộ chọn
              diễn tả được. Giữ nguyên để không làm hỏng luồng đang chạy.
            </span>
          </p>
          <p className="font-mono text-xs break-all text-amber-900">{condition}</p>
          <button
            type="button"
            className="text-xs underline underline-offset-2"
            onClick={() => onChange('')}
          >
            Bỏ điều kiện này và chọn lại
          </button>
        </div>
      ) : (
        <>
          <Select value={kind} onValueChange={(value) => doiKieu(value as FlowScopeKind)}>
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(SCOPE_LABELS).map(([ma, nhan]) => (
                <SelectItem key={ma} value={ma}>
                  {nhan}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {kind === 'doc_type' && (
            <MultiPicker
              value={ids}
              onChange={(ids) => onChange(buildScopeCondition({ kind: 'doc_type', ids }))}
              options={docTypes.map((type) => ({
                id: type.id,
                label: type.name,
                hint: type.code,
              }))}
              placeholder="Chọn loại văn bản…"
            />
          )}

          {kind === 'document' && (
            <MultiPicker
              value={ids}
              onChange={(ids) => onChange(buildScopeCondition({ kind: 'document', ids }))}
              options={(documents?.items ?? []).map((row) => ({
                id: row.id,
                label: row.title,
                hint: row.display_code,
              }))}
              placeholder="Chọn văn bản…"
            />
          )}

          {/*  Chọn kiểu hẹp mà chưa tick gì thì luồng vẫn đang áp cho TẤT CẢ —
               nói ra, đừng để người khai tưởng mình đã giới hạn được. */}
          {kind !== 'all' && ids.length === 0 ? (
            <p className="text-xs text-amber-700">
              Chưa chọn mục nào nên luồng vẫn áp cho <b>mọi văn bản</b>.
            </p>
          ) : (
            <p className="text-xs text-muted-foreground">
              {kind === 'all'
                ? 'Đây là luồng MẶC ĐỊNH của văn bản. Nhiều luồng cùng loại thì luồng có điều kiện được xét trước.'
                : 'Phiếu không khớp sẽ dùng luồng mặc định, hoặc đi đường duyệt cũ nếu chưa có luồng mặc định.'}
            </p>
          )}
        </>
      )}
    </div>
  )
}
