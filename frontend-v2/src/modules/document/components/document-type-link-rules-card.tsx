import { ArrowDown, ArrowUp, Link2, Pencil, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent } from '@/shared/ui/card'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { linkRuleToInput } from '../helpers/link-rule-input'
import { linkRuleSentence } from '../helpers/link-rule-sentence'
import {
  useDeleteDocumentLinkRule,
  useDocumentLinkRules,
  useLinkRuleOptions,
  useReorderDocumentLinkRules,
  useSaveDocumentLinkRules,
} from '../hooks/use-document-link-rules'
import { useDocumentTypes } from '../hooks/use-document-types'
import type { DocTypeLinkRuleInput } from '../types/document-link-rule'
import { DocumentLinkRuleForm } from './document-link-rule-form'

const FORM_ID = 'doc-type-link-rule-inline-form'

interface DocumentTypeLinkRulesCardProps {
  /**
   * Loại đã lưu → đọc/ghi thẳng API.
   *
   * Bỏ trống = đang TẠO loại mới, chưa có id để dòng quy tắc trỏ vào. Khi đó
   * thẻ chạy trên `pending` và trang cha gửi lên sau khi loại được lưu — cùng
   * lối với quyền / phạm vi ở trang tạo văn bản.
   */
  docTypeId?: number
  /** Bỏ trống lúc đang tạo loại mới — loại còn chưa có tên để gọi. */
  docTypeName?: string
  /** Chỉ dùng khi chưa có `docTypeId`. */
  pending?: DocTypeLinkRuleInput[]
  onPendingChange?: (rows: DocTypeLinkRuleInput[]) => void
}

/** Dòng đang khai: `null` = thêm mới · số = vị trí dòng đang sửa. */
type DeclaringState = null | number

/**
 * QUAN HỆ VỚI LOẠI KHÁC — khai ngay trên trang loại văn bản (E01).
 *
 * Đây là chỗ trả lời câu *"loại này phụ thuộc loại nào"*: Hướng dẫn công việc
 * bắt buộc hướng dẫn một Quy trình, Biểu mẫu thuộc về một Quy trình. Dòng nào
 * đánh dấu **Bắt buộc** thì lúc tạo văn bản loại này, nếu trong kho chưa có văn
 * bản đích nào còn hiệu lực, màn tạo sẽ cảnh báo (vẫn cho tạo tiếp).
 *
 * Quan hệ là **một–nhiều**: một loại phụ thuộc mấy loại cũng được, và ô "Tới
 * loại" lúc thêm mới cho tick nhiều loại một lần.
 *
 * Cùng bảng dữ liệu với trang «Quy tắc quan hệ» — trang đó xem toàn cảnh cả hệ,
 * ở đây chỉ lọc theo một loại. Cố tình KHÔNG đẻ thêm khái niệm "loại tiên
 * quyết" riêng: hai nơi mô tả cùng một việc thì sớm muộn cũng lệch nhau.
 */
export function DocumentTypeLinkRulesCard({
  docTypeId,
  docTypeName,
  pending = [],
  onPendingChange,
}: DocumentTypeLinkRulesCardProps) {
  //  `undefined` = hộp thoại đóng.
  const [dangKhai, setDangKhai] = useState<DeclaringState | undefined>(undefined)

  const { data, isLoading } = useDocumentLinkRules(docTypeId, Boolean(docTypeId))
  const { items: docTypes } = useDocumentTypes()
  const { data: options } = useLinkRuleOptions()
  const save = useSaveDocumentLinkRules()
  const reorder = useReorderDocumentLinkRules()
  const remove = useDeleteDocumentLinkRule()

  //  Hai nguồn, một dạng hiển thị: dòng đã lưu mang thêm `id`, dòng xếp hàng thì
  //  không. Mọi thứ còn lại (nhãn quan hệ, tên loại đích) đều tra từ danh mục
  //  chứ không đọc `*_name` của bản ghi — dòng xếp hàng chưa có mấy trường đó.
  const rows = docTypeId
    ? (data?.items ?? []).map((rule) => ({ id: rule.id, values: linkRuleToInput(rule) }))
    : pending.map((values) => ({ id: undefined, values }))

  function relationName(relation: number) {
    return options?.relations.find((item) => item.value === relation)?.label ?? String(relation)
  }

  /** `undefined` = quy tắc không kén loại đích — câu mô tả đọc khác hẳn. */
  function targetTypeName(targetTypeId: number | null) {
    if (!targetTypeId) return undefined
    return docTypes.find((type) => type.id === targetTypeId)?.name ?? 'Không rõ'
  }

  /** Ghi kết quả hộp thoại: có id thì gọi API, chưa có thì xếp vào `pending`. */
  function luu(newRows: DocTypeLinkRuleInput[]) {
    const index = dangKhai

    //  Dòng thêm mới xuống CUỐI, đánh số tiếp theo dòng cuối đang có. Dòng đang
    //  sửa giữ nguyên chỗ của nó.
    const assignNumber = (row: DocTypeLinkRuleInput, i: number) =>
      typeof index === 'number' ? row : { ...row, sort_order: rows.length + i + 1 }

    if (!docTypeId) {
      const withSource = newRows.map((row, i) => ({ ...assignNumber(row, i), source_type_id: 0 }))
      onPendingChange?.(
        typeof index === 'number'
          ? pending.map((row, i) => (i === index ? withSource[0] : row))
          : [...pending, ...withSource],
      )
      setDangKhai(undefined)
      return
    }

    save.mutate(
      {
        id: typeof index === 'number' ? data?.items[index]?.id : undefined,
        rows: newRows.map((row, i) => ({ ...assignNumber(row, i), source_type_id: docTypeId })),
      },
      {
        //  Còn dòng hỏng (thường là trùng với quy tắc đã có) thì GIỮ hộp thoại:
        //  đóng đi là người dùng mất luôn phần đã tick và phải tick lại từ đầu
        //  để sửa đúng một dòng.
        onSuccess: ({ failed }) => {
          if (failed.length === 0) setDangKhai(undefined)
        },
      },
    )
  }

  function xoa(index: number) {
    const id = data?.items[index]?.id
    if (docTypeId && id) remove.mutate(id)
    else onPendingChange?.(pending.filter((_, i) => i !== index))
  }

  /** Đổi chỗ một dòng với dòng liền kề. `huong` = -1 lên, +1 xuống. */
  function swap(index: number, huong: -1 | 1) {
    const target = index + huong
    if (target < 0 || target >= rows.length) return

    const reordered = [...rows]
    ;[reordered[index], reordered[target]] = [reordered[target], reordered[index]]

    if (!docTypeId) {
      //  Đánh số lại luôn thay vì chỉ hoán vị mảng: mấy dòng này lát nữa gửi
      //  lên theo lô, mà `sort_order` mới là thứ backend đọc — mảng đúng thứ tự
      //  nhưng số cũ thì tải lại trang là về chỗ cũ.
      onPendingChange?.(reordered.map((row, i) => ({ ...row.values, sort_order: i + 1 })))
      return
    }
    reorder.mutate(reordered.map((row) => ({ id: row.id as number, values: row.values })))
  }

  return (
    <Card>
      <CardContent className="space-y-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="flex items-center gap-2 text-sm font-medium">
              <Link2 className="size-4 text-primary" />
              Quan hệ với loại văn bản khác
            </p>
            <p className="text-sm text-muted-foreground">
              Quy định văn bản thuộc loại này phải gắn với văn bản nào khác. Quy tắc <b>bắt buộc</b>{' '}
              sẽ chặn gửi duyệt khi còn thiếu, và cảnh báo ngay lúc tạo nếu chưa có văn bản để gắn.
            </p>
          </div>

          <Button type="button" variant="outline" onClick={() => setDangKhai(null)}>
            <Plus className="size-4" />
            Thêm quy tắc
          </Button>
        </div>

        {docTypeId && isLoading ? (
          <p className="text-sm text-muted-foreground">Đang tải…</p>
        ) : rows.length === 0 ? (
          <div className="rounded-md border border-dashed px-3 py-8 text-center">
            <p className="text-sm font-medium">Chưa có quy tắc quan hệ nào</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Văn bản thuộc loại này đứng độc lập, không cần gắn với văn bản nào khác.
            </p>
          </div>
        ) : (
          <ul className="divide-y rounded-md border">
            {rows.map((row, index) => (
              <li key={row.id ?? `pending-${index}`} className="flex items-start gap-3 px-3 py-3">
                {/*  Số thứ tự đứng đầu dòng: đây là thứ trả lời câu "trước C
                     phải có A rồi B" — không có số thì danh sách chỉ là một
                     đống quan hệ không biết cái nào trước. */}
                <span className="mt-0.5 w-5 shrink-0 text-sm font-medium text-muted-foreground tabular-nums">
                  {index + 1}.
                </span>

                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={row.values.is_required ? 'default' : 'secondary'}>
                      {row.values.is_required ? 'Bắt buộc' : 'Tùy chọn'}
                    </Badge>
                    {/*  Dòng đã tắt vẫn hiện: nó vẫn giải thích những quan hệ đã
                         khai trên văn bản cũ, giấu đi thì không ai bật lại được. */}
                    {!row.values.is_active && <Badge variant="outline">Ngừng áp dụng</Badge>}
                  </div>

                  {/*  Cả dòng đọc thành MỘT CÂU. Bốn cột rời của bảng quy tắc
                       (quan hệ · loại đích · bắt buộc · số lượng) bày ra thành
                       một hàng chip thì người đọc phải tự ghép lại mới hiểu, mà
                       ghép sai cũng không có gì báo. */}
                  <p className="text-sm">
                    {linkRuleSentence({
                      rule: row.values,
                      relationLabel: relationName(row.values.relation),
                      targetTypeName: targetTypeName(row.values.target_type_id),
                      sourceTypeName: docTypeName,
                    })}
                  </p>
                </div>

                <div className="flex shrink-0 items-center">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    title="Đưa lên trước"
                    aria-label="Đưa lên trước"
                    disabled={index === 0 || reorder.isPending}
                    onClick={() => swap(index, -1)}
                  >
                    <ArrowUp />
                  </Button>

                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    title="Đưa xuống sau"
                    aria-label="Đưa xuống sau"
                    disabled={index === rows.length - 1 || reorder.isPending}
                    onClick={() => swap(index, 1)}
                  >
                    <ArrowDown />
                  </Button>

                  {/* Vạch ngăn: hai nút trái đổi THỨ TỰ, hai nút phải đổi NỘI
                      DUNG — bốn nút liền nhau thì dễ bấm nhầm nhóm. */}
                  <span className="mx-1 h-5 w-px bg-border" />

                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    title="Sửa quy tắc"
                    aria-label="Sửa quy tắc"
                    onClick={() => setDangKhai(index)}
                  >
                    <Pencil />
                  </Button>

                  <ConfirmIconButton
                    icon={Trash2}
                    title="Xóa quy tắc"
                    destructive
                    confirmTitle="Xóa quy tắc quan hệ?"
                    confirmDescription="Từ nay văn bản thuộc loại này không khai thêm quan hệ đó được nữa. Các quan hệ đã khai trên văn bản cũ vẫn giữ nguyên."
                    confirmLabel="Xóa quy tắc"
                    onConfirm={() => xoa(index)}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}

        {/*  Nói rõ mấy dòng này chưa nằm trong cơ sở dữ liệu: người khai bỏ trang
             giữa chừng thì mất, và họ có quyền biết điều đó trước. */}
        {!docTypeId && rows.length > 0 && (
          <p className="text-xs text-muted-foreground">
            Các quy tắc trên được lưu cùng lúc với loại văn bản khi bạn bấm <b>Lưu</b>.
          </p>
        )}
      </CardContent>

      <Dialog
        open={dangKhai !== undefined}
        onOpenChange={(open) => {
          if (!open) setDangKhai(undefined)
        }}
      >
        <DialogContent className="flex max-h-[85vh] flex-col overflow-hidden sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {typeof dangKhai === 'number' ? 'Sửa quy tắc quan hệ' : 'Thêm quy tắc quan hệ'}
            </DialogTitle>
            <DialogDescription>
              Quy định văn bản thuộc loại {docTypeName ? `«${docTypeName}»` : 'này'} phải gắn với
              loại văn bản nào, bắt buộc hay tùy chọn, và được gắn bao nhiêu văn bản.
            </DialogDescription>
          </DialogHeader>

          {/*  Chỉ phần giữa cuộn, hàng nút đứng yên ở đáy: để cả hộp thoại cuộn
               thì nút Lưu bị đẩy khỏi tầm nhìn ngay khi mở, người dùng phải cuộn
               xuống mới thấy thứ mình cần bấm. */}
          <div className="-mx-1 flex-1 overflow-y-auto px-1">
            <DocumentLinkRuleForm
              //  `key` đổi theo dòng đang khai: form giữ state nội bộ, không có
              //  key thì mở dòng thứ hai vẫn thấy giá trị của dòng thứ nhất.
              key={dangKhai ?? 'new'}
              formId={FORM_ID}
              initial={typeof dangKhai === 'number' ? rows[dangKhai]?.values : undefined}
              lockedSourceTypeId={docTypeId}
              sourceTypeName={docTypeName}
              //  Thêm mới cho tick nhiều loại đích một lần — loại này phụ thuộc
              //  mấy loại cũng khai được trong một lượt. Sửa thì đúng dòng đó.
              allowMultipleTargets={dangKhai === null}
              onSubmit={luu}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setDangKhai(undefined)}>
              Hủy
            </Button>
            {/* Nút Lưu nằm ngoài form, nối vào bằng `form=` (xem `FORM_ID`). */}
            <Button type="submit" form={FORM_ID} disabled={save.isPending}>
              Lưu quy tắc
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
