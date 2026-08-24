import { ChevronDown, Plus, Search, TriangleAlert } from 'lucide-react'
import { useMemo, useState } from 'react'

import { useAuth } from '@/core/auth/use-auth'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { useRoles } from '@/modules/hr/hooks/use-roles'
import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { DatePicker } from '@/shared/ui/date-picker'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { idKhongDuocTuChan } from '../helpers/khong-tu-chan-chinh-minh'
import { SubjectChips } from './access-subject-chips'
import {
  EFFECT,
  SUBJECT_KIND,
  SUBJECT_KIND_LABELS,
  type DocumentAccessDraft,
} from '../types/document-access'

interface DocumentAccessDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  pending?: boolean
  /** Các dòng đã khai trước đó — dùng để cảnh báo khi khai chồng chiều. */
  existing?: DocumentAccessDraft[]
  /**
   * Nhận CẢ LƯỢT khai. Trang chi tiết gửi thẳng lên máy chủ; trang tạo văn bản
   * xếp hàng chờ vì lúc đó văn bản còn chưa có id.
   */
  onSubmit: (rows: DocumentAccessDraft[]) => void
}

/**
 * CHIA QUYỀN (hoặc CẤM) trên một văn bản — khai **nhiều đối tượng một lượt**.
 *
 * Chia cho cả tổ năm người mà phải mở hộp năm lần, mỗi lần khai lại y hệt hạn
 * và lý do, là việc không ai chịu làm quá hai lần. Nên ô chọn đối tượng nhận
 * nhiều lựa chọn, còn chiều tác động / quyền / hạn / lý do khai MỘT lần rồi áp
 * cho cả lượt.
 *
 * Cấp cho **bốn loại đối tượng**, không chỉ cá nhân: người · phòng ban · pháp
 * nhân · vai trò. Chia cho cả phòng mà phải chọn từng người thì người mới vào
 * phòng không có quyền còn người chuyển đi vẫn còn — hai hành vi sai mà người
 * chia không hề chọn.
 *
 * Ô **hạn** không bắt buộc nhưng nên đặt: hết ngày là tự mất quyền, không phải
 * trông vào việc có ai nhớ đi thu hồi hay không.
 */
export function DocumentAccessDialog({
  open,
  onOpenChange,
  pending = false,
  existing = [],
  onSubmit,
}: DocumentAccessDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {/* Khóa chiều cao hộp và chỉ cho THÂN cuộn: để cả hộp cuộn thì khai một
          cụm vài chục người là hàng nút Hủy / Thêm cụm / Xong trôi tuột xuống
          dưới, người dùng tưởng mất nút. Header và footer ghim tại chỗ. */}
      <DialogContent className="flex max-h-[85vh] flex-col overflow-hidden sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Chia quyền truy cập</DialogTitle>
          <DialogDescription>
            Mở thêm cho người ngoài phạm vi vai trò, hoặc chặn đích danh một người vốn đang xem
            được.
          </DialogDescription>
        </DialogHeader>

        {/* Ô nhập nằm trong component con nên đóng hộp là mọi thứ đã khai tự
            mất — mở lại là một lượt khai MỚI, khỏi phải tự dọn. */}
        <AccessForm
          pending={pending}
          existing={existing}
          onCancel={() => onOpenChange(false)}
          onSubmit={onSubmit}
        />
      </DialogContent>
    </Dialog>
  )
}

interface AccessFormProps {
  pending: boolean
  existing: DocumentAccessDraft[]
  onCancel: () => void
  onSubmit: (rows: DocumentAccessDraft[]) => void
}

/** Khóa nhận dạng một dòng: cùng loại + cùng id là cùng một đối tượng. */
function draftKey(row: DocumentAccessDraft) {
  return `${row.values.subject_kind}-${row.values.subject_id}`
}

function AccessForm({ pending, existing, onCancel, onSubmit }: AccessFormProps) {
  const [subjectKind, setSubjectKind] = useState(String(SUBJECT_KIND.employee))
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  //  Danh sách khai được trong CHÍNH lần mở hộp này: cho phép một cụm, cấm một
  //  cụm, rồi mới đóng — thay vì đóng mở lại hộp cho mỗi chiều tác động.
  const [drafts, setDrafts] = useState<DocumentAccessDraft[]>([])
  const [effect, setEffect] = useState(String(EFFECT.allow))
  const [canWrite, setCanWrite] = useState(false)
  const [canDelete, setCanDelete] = useState(false)
  const [validTo, setValidTo] = useState('')
  const [reason, setReason] = useState('')

  const { user } = useAuth()
  const { data: employees } = useEmployees({ page_size: 1000, is_active: true })
  const { data: departments } = useDepartments({ page_size: 500 })
  const { data: companies } = useCompanies({ page_size: 200, is_active: true })
  const { data: roles } = useRoles()

  const optionsTatCa = useMemo(() => {
    switch (Number(subjectKind)) {
      case SUBJECT_KIND.department:
        return (departments?.items ?? [])
          .filter((item) => item.is_active)
          .map((item) => ({ id: item.id, label: item.name }))
      case SUBJECT_KIND.company:
        return (companies?.items ?? []).map((item) => ({ id: item.id, label: item.name }))
      case SUBJECT_KIND.role:
        return (roles ?? []).map((item) => ({ id: item.id, label: item.name }))
      default:
        return (employees?.items ?? []).map((item) => ({ id: item.id, label: item.full_name }))
    }
  }, [subjectKind, employees, departments, companies, roles])

  /** Dựng các dòng từ phần đang chọn trên màn hình. */
  function buildRows(): DocumentAccessDraft[] {
    const label = new Map(options.map((option) => [option.id, option.label]))
    return selectedIds.map((id) => ({
      subjectLabel: label.get(id) ?? '',
      values: {
        subject_kind: Number(subjectKind),
        subject_id: id,
        effect: Number(effect),
        //  Cho phép mà không cho đọc là vô nghĩa; cấm mà không chặn đọc thì
        //  cũng chẳng cấm được gì. Nên `can_read` luôn bật.
        can_read: true,
        can_write: canWrite,
        can_delete: canDelete,
        valid_from: null,
        valid_to: validTo || null,
        reason: reason.trim(),
      },
    }))
  }

  /** Gộp vào danh sách, dòng mới của cùng một đối tượng thì thay dòng cũ. */
  function merge(current: DocumentAccessDraft[], added: DocumentAccessDraft[]) {
    const replaced = new Set(added.map(draftKey))
    return [...current.filter((row) => !replaced.has(draftKey(row))), ...added]
  }

  /** Khai xong một cụm thì cất vào danh sách và ở lại hộp để khai cụm kế. */
  function addToList() {
    setDrafts(merge(drafts, buildRows()))
    //  Chỉ xóa phần CHỌN ĐỐI TƯỢNG; chiều tác động và bộ quyền giữ nguyên vì
    //  người dùng hay khai tiếp một cụm gần giống cụm vừa rồi.
    setSelectedIds([])
  }

  function handleSubmit() {
    //  Chọn xong mà bấm thẳng "Xong" thì coi như đã thêm — không bắt bấm hai
    //  nút mới lưu được một cụm.
    onSubmit(selectedIds.length > 0 ? merge(drafts, buildRows()) : drafts)
  }

  const isDeny = Number(effect) === EFFECT.deny
  const kindLabel = SUBJECT_KIND_LABELS[Number(subjectKind)].toLowerCase()

  //  TỰ CHẶN CHÍNH MÌNH — luật nằm ở `idKhongDuocTuChan`, đọc chú thích ở đó.
  const idTuChan = idKhongDuocTuChan(Number(subjectKind), user, isDeny)
  const tenTuChan = optionsTatCa.find((option) => option.id === idTuChan)?.label ?? ''
  //  Bỏ khỏi DANH SÁCH CHỌN luôn, không chỉ báo lỗi sau khi bấm: chọn được rồi
  //  mới bị mắng là bắt người ta làm lại một việc lẽ ra không nên mời họ làm.
  const options = optionsTatCa.filter((option) => option.id !== idTuChan)

  const selectedOptions = options.filter((option) => selectedIds.includes(option.id))
  const allowDrafts = drafts.filter((row) => row.values.effect === EFFECT.allow)
  const denyDrafts = drafts.filter((row) => row.values.effect === EFFECT.deny)
  const total = drafts.length + selectedIds.length

  //  Cùng một người vừa cho phép vừa cấm là mâu thuẫn người khai hay mắc khi
  //  khai nhiều cụm liên tiếp. Không chặn (dòng mới thay dòng cũ), nhưng phải
  //  nói ra trước khi bấm — nhất là vì CẤM thắng mọi dòng cho phép.
  const opposite = [...existing, ...drafts].filter((row) => row.values.effect !== Number(effect))
  const conflicts = selectedOptions.filter((option) =>
    opposite.some(
      (row) =>
        row.values.subject_kind === Number(subjectKind) && row.values.subject_id === option.id,
    ),
  )

  return (
    <>
      {/* `-mx-6 px-6`: thanh cuộn chạy sát mép hộp thay vì thụt vào giữa nội
          dung, nhìn ra ngay là cả thân đang cuộn chứ không phải một ô nào đó. */}
      <div className="-mx-6 min-h-0 flex-1 space-y-4 overflow-y-auto px-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Loại đối tượng</Label>
            <Select
              value={subjectKind}
              onValueChange={(value) => {
                setSubjectKind(value)
                //  Đổi loại là danh sách khác hẳn — giữ lại lựa chọn cũ thì
                //  những id đó chỉ sang bản ghi khác cùng số.
                setSelectedIds([])
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(SUBJECT_KIND_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>
              Chọn {kindLabel}
              <span className="text-destructive"> *</span>
            </Label>
            <SubjectMultiSelect
              options={options}
              value={selectedIds}
              onChange={setSelectedIds}
              kindLabel={kindLabel}
            />
          </div>
        </div>

        {/*  Nói RA vì sao thiếu: lọc lặng lẽ thì người dùng tìm tên mình mãi
             không thấy rồi tưởng danh sách hỏng. */}
        {isDeny && tenTuChan && (
          <p className="flex items-start gap-2 rounded-md border border-sky-300 bg-sky-50 px-3 py-2 text-xs text-sky-900">
            <TriangleAlert className="mt-0.5 size-3.5 shrink-0" />
            <span>
              Không chặn được chính mình — <span className="font-medium">{tenTuChan}</span> đã được
              bỏ khỏi danh sách. Tự chặn thì văn bản vừa lập xong bạn không mở lại được, mà cũng
              không còn đường vào để gỡ.
            </span>
          </p>
        )}

        {conflicts.length > 0 && (
          <p className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-900">
            <TriangleAlert className="mt-0.5 size-3.5 shrink-0" />
            <span>
              {conflicts.map((option) => option.label).join(', ')} đang nằm ở cụm{' '}
              {isDeny ? 'cho phép' : 'không cho phép'}. Khai tiếp thì dòng cũ bị thay bằng dòng này.
            </span>
          </p>
        )}

        {/* Chọn xong thì thấy NGAY mình đang khai cho những ai — nhãn "+2" trên
            ô select không đủ để rà lại trước khi bấm. */}
        {selectedOptions.length > 0 && (
          <SubjectChips
            items={selectedOptions.map((option) => ({
              key: String(option.id),
              label: option.label,
            }))}
            onRemove={(key) => setSelectedIds(selectedIds.filter((id) => String(id) !== key))}
          />
        )}

        <div className="space-y-2">
          <Label>Chiều tác động</Label>
          <RadioGroup value={effect} onValueChange={setEffect} className="sm:flex sm:gap-4">
            <label className="flex items-center gap-2 text-sm">
              <RadioGroupItem value={String(EFFECT.allow)} />
              Cho phép
            </label>
            <label className="flex items-center gap-2 text-sm">
              <RadioGroupItem value={String(EFFECT.deny)} />
              {/*  Gọi ĐÚNG MỘT TÊN ở mọi chỗ: nút chọn ở đây, tiêu đề cụm bên
                   ngoài, câu giải thích. Trước 24/08/2026 chỗ này ghi «Cấm» còn
                   cụm bên ngoài ghi «Không cho phép» — người dùng phải tự đoán
                   hai chữ đó là một. */}
              Không cho phép
            </label>
          </RadioGroup>
          <p className="text-xs text-muted-foreground">
            {isDeny
              ? '«Không cho phép» thắng mọi dòng cho phép và thắng cả phạm vi vai trò — người bị chặn không còn thấy văn bản này trong danh sách.'
              : 'Người được chia sẽ thấy và mở được văn bản này kể cả khi nó nằm ngoài phạm vi vai trò của họ.'}
          </p>
        </div>

        <div className="space-y-2">
          <Label>Được làm gì</Label>
          <div className="flex flex-wrap gap-4">
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <Checkbox checked disabled />
              Xem {isDeny && '(chặn cả việc nhìn thấy)'}
            </label>
            <label className="flex items-center gap-2 text-sm">
              <Checkbox
                checked={canWrite}
                onCheckedChange={(value) => setCanWrite(value === true)}
              />
              Sửa
            </label>
            <label className="flex items-center gap-2 text-sm">
              <Checkbox
                checked={canDelete}
                onCheckedChange={(value) => setCanDelete(value === true)}
              />
              Xóa
            </label>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Hết hạn</Label>
            <DatePicker value={validTo} onChange={setValidTo} />
            <p className="text-xs text-muted-foreground">Trống = không đặt hạn.</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="access-reason">Lý do</Label>
            <Input
              id="access-reason"
              placeholder="VD: Phối hợp rà soát quy chế"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
            />
          </div>
        </div>

        {drafts.length > 0 && (
          <div className="max-h-56 space-y-3 overflow-y-auto rounded-md border bg-muted/30 p-3">
            <p className="text-xs font-medium">Đã khai trong lượt này</p>
            <DraftGroup
              title="Cho phép"
              rows={allowDrafts}
              onRemove={(row) => setDrafts(drafts.filter((item) => item !== row))}
            />
            <DraftGroup
              title="Không cho phép"
              rows={denyDrafts}
              onRemove={(row) => setDrafts(drafts.filter((item) => item !== row))}
            />
          </div>
        )}
      </div>

      <DialogFooter className="shrink-0 border-t pt-4">
        <Button type="button" variant="ghost" onClick={onCancel}>
          Hủy
        </Button>
        {/* Hai nút: một để khai tiếp cụm nữa (hộp ở lại), một để chốt cả lượt. */}
        <Button
          type="button"
          variant="outline"
          onClick={addToList}
          disabled={selectedIds.length === 0}
        >
          <Plus className="size-4" />
          {isDeny ? 'Thêm cụm không cho phép' : 'Thêm cụm cho phép'}
        </Button>
        <Button type="button" onClick={handleSubmit} disabled={total === 0 || pending}>
          Xong{total > 0 && ` (${total})`}
        </Button>
      </DialogFooter>
    </>
  )
}

interface SubjectOption {
  id: number
  label: string
}

interface SubjectMultiSelectProps {
  options: SubjectOption[]
  value: number[]
  onChange: (ids: number[]) => void
  /** "người" · "phòng ban" … — dùng cho chữ gợi ý và ô tìm. */
  kindLabel: string
}

/**
 * Ô chọn NHIỀU đối tượng, nhìn y hệt một ô select thường.
 *
 * Cố ý giữ đúng hình dáng ô select: đây vẫn là "chọn ai" như trước, chỉ khác ở
 * chỗ nhận được nhiều lựa chọn — đổi hẳn sang danh sách bày sẵn thì hộp thoại
 * phình gấp đôi cho một việc thường chỉ chọn một, hai người.
 */
function SubjectMultiSelect({ options, value, onChange, kindLabel }: SubjectMultiSelectProps) {
  const [open, setOpen] = useState(false)
  const [keyword, setKeyword] = useState('')

  const matches = useMemo(() => {
    const needle = keyword.trim().toLowerCase()
    if (!needle) return options
    return options.filter((option) => option.label.toLowerCase().includes(needle))
  }, [options, keyword])

  const selected = options.filter((option) => value.includes(option.id))
  //  Hiện tên người đầu tiên + đếm phần còn lại: liệt kê hết thì ô select bị
  //  kéo dài ra, mà cắt cụt giữa chừng thì không biết còn bao nhiêu.
  const label =
    selected.length === 0
      ? `Chưa chọn`
      : selected.length === 1
        ? selected[0].label
        : `${selected[0].label} +${selected.length - 1}`

  function toggle(id: number) {
    onChange(value.includes(id) ? value.filter((item) => item !== id) : [...value, id])
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={cn(
            'flex h-9 w-full items-center justify-between gap-2 rounded-md border bg-transparent px-3 py-2 text-sm shadow-xs transition-colors',
            'focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none',
            selected.length === 0 && 'text-muted-foreground',
          )}
        >
          <span className="truncate">{label}</span>
          <ChevronDown className="size-4 shrink-0 opacity-50" />
        </button>
      </PopoverTrigger>

      <PopoverContent align="start" className="w-(--radix-popover-trigger-width) p-0">
        <div className="relative border-b">
          <Search className="absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            autoFocus
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            placeholder={`Tìm ${kindLabel}…`}
            className="border-0 pl-8 shadow-none focus-visible:ring-0"
          />
        </div>

        <ul className="max-h-56 overflow-y-auto p-1">
          {matches.length === 0 ? (
            <li className="px-2 py-6 text-center text-xs text-muted-foreground">
              Không có {kindLabel} nào khớp.
            </li>
          ) : (
            matches.map((option) => {
              const checked = value.includes(option.id)
              return (
                <li key={option.id}>
                  {/* Không tự đóng sau mỗi lần bấm — chọn nhiều mà đóng ngay
                      thì lại thành chọn một, mở lại từ đầu. */}
                  <button
                    type="button"
                    onClick={() => toggle(option.id)}
                    className={cn(
                      'flex w-full items-center gap-2.5 rounded-sm px-2 py-1.5 text-left text-sm transition-colors',
                      'hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
                      checked && 'bg-accent/60 font-medium',
                    )}
                  >
                    <Checkbox checked={checked} className="pointer-events-none" />
                    <span className="truncate">{option.label}</span>
                  </button>
                </li>
              )
            })
          )}
        </ul>

        <div className="flex items-center justify-between gap-2 border-t bg-muted/40 px-2 py-1.5">
          <span className="text-xs text-muted-foreground tabular-nums">
            Đã chọn {value.length} / {options.length}
          </span>
          {value.length > 0 && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-xs"
              onClick={() => onChange([])}
            >
              Bỏ chọn hết
            </Button>
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}

interface DraftGroupProps {
  title: string
  rows: DocumentAccessDraft[]
  onRemove: (row: DocumentAccessDraft) => void
}

/** Một cụm vừa khai trong lượt này — chip xóa được, không tô màu. */
function DraftGroup({ title, rows, onRemove }: DraftGroupProps) {
  if (rows.length === 0) return null

  return (
    <div className="space-y-1.5">
      <p className="text-xs font-medium">
        {title}
        <span className="ml-1.5 font-normal text-muted-foreground">({rows.length})</span>
      </p>
      <SubjectChips
        items={rows.map((row) => ({
          key: draftKey(row),
          label: row.subjectLabel || '(chưa rõ tên)',
        }))}
        onRemove={(key) => {
          const row = rows.find((item) => draftKey(item) === key)
          if (row) onRemove(row)
        }}
      />
    </div>
  )
}
