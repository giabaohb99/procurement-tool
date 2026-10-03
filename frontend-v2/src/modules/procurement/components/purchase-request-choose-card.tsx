import { Ban, ListChecks, Loader2, PenLine, Undo2 } from 'lucide-react'
import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { SearchSelect } from '@/shared/ui/search-select'
import { cn } from '@/shared/utils/cn'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { useSuppliers } from '@/modules/production/hooks/use-suppliers'
import {
  useAssignPrSupplierBulk,
  useChooseOption,
  usePurchaseRequestItemOptions,
  useReopenPrOptionsLine,
  useSetPrOptionSupplier,
  useUpdateOption,
} from '../hooks/use-purchase-request-options'
import { isDispatched } from '../types/purchase-request-detail'
import type { PurchaseRequestDetail, PurchaseRequestItem } from '../types/purchase-request-detail'
import type {
  PrAssignSupplierLine,
  PurchaseRequestOption,
} from '../types/purchase-request-options'
import {
  isPrOptionStageOpen,
  PR_OPTION_SOURCE_SURVEY,
} from '../types/purchase-request-options'
import { describeBulkPriceChange, parsePriceInput } from '../utils/purchase-request-bulk-price'
import { PurchaseRequestOptionEditDialog } from './purchase-request-option-edit-dialog'

interface PurchaseRequestChooseCardProps {
  purchaseRequest: PurchaseRequestDetail
}

/** Giá trị canh gác cho ô chọn NCC — Select của shadcn cấm value rỗng. */
const NO_SUPPLIER = '__none__'

/** Danh mục NCC dùng chung cho ô chọn — cùng hình dạng với `useSuppliers().items`. */
type SupplierOption = { code: string; name: string }


/**
 * Khu "Phương án" trên màn CHI TIẾT YCMH (bao-CR-310 đợt 3b) — nửa còn lại của
 * luồng xử lý phương án, nhân khuôn khu "Kết quả khảo sát" của YCBG (CR-222):
 * NSTM gắn phương án và bấm "Chốt hoàn thành xử lý" ở màn xử lý riêng; dòng nào
 * NSTM ĐÃ CHỐT mới hiện ở đây cho NGƯỜI YÊU CẦU (hoặc người giữ quyền duyệt
 * YCMH) chọn phương án mua. Mỗi phương án là MỘT THẺ bấm chọn kiểu radio y hệt
 * bên YCBG — không dùng bảng ngang. Chọn nhầm dòng thì "Mở lại cho NSTM xử lý"
 * — cờ chốt hạ xuống, dòng quay về màn xử lý, phương án đã chọn vẫn giữ nguyên.
 *
 * Đợt 2 MỞ RỘNG (H.10.5): màn chọn có thêm TẦNG THU MUA — người giữ
 * `purchase_request:write` + `supplier:read` sửa được GIÁ của mọi phương án và
 * điền/sửa NCC trên phương án 0 / nhập tay ngay tại đây (kể cả dòng đã chốt,
 * đúng khe H.10.4), kèm khu "Áp 1 NCC cho nhiều dòng". Dòng CHỐT RỖNG nay vẫn
 * có PHƯƠNG ÁN 0 (mua đúng theo dòng yêu cầu gốc) nên không tắt query nữa.
 *
 * bao-CR-570 (02/10/2026): thẻ HIỆN MỌI DÒNG ngay khi phiếu đã điều phối — đại ca chốt
 * làm như YCBG, phương án NSTM gắn tới đâu người yêu cầu chọn tới đó, không đợi NSTM bấm
 * «Chốt hoàn thành xử lý» (người lập đơn chính là nhân sự thu mua). Dòng NSTM chưa chốt
 * mang nhãn «NSTM đang xử lý»; nút «Mở lại cho NSTM xử lý» chỉ còn ở dòng ĐÃ chốt.
 */
export function PurchaseRequestChooseCard({ purchaseRequest }: PurchaseRequestChooseCardProps) {
  const { user } = useAuth()
  const { can } = usePermission()

  const stageOpen = isPrOptionStageOpen(purchaseRequest.status)
  // Đúng gác `ensure_can_choose` của backend: người yêu cầu hoặc người giữ
  // quyền duyệt YCMH; và chỉ khi phiếu còn trong giai đoạn mở.
  const isRequester =
    !!user?.employee_id && user.employee_id === purchaseRequest.requester_id
  const canApprove = can('purchase_request', 'approve')
  const canChoose = stageOpen && (isRequester || canApprove)
  const canSeeSupplier = can('supplier', 'read')
  // Tầng THU MUA (H.10.5) — cùng cổng với backend `set_option_supplier` /
  // `assign_supplier_bulk`: write + supplier:read, phiếu còn trong giai đoạn mở.
  const canEditPurchase = stageOpen && can('purchase_request', 'write') && canSeeSupplier
  const userEmpCode = user?.emp_code ?? ''

  // Gọi TRƯỚC nhánh return null kẻo lệch thứ tự hooks giữa hai lượt render.
  const suppliersQuery = useSuppliers(
    { page_size: 1000, supplier_type: 'goods', is_active: true },
    { enabled: canEditPurchase },
  )
  const suppliers: SupplierOption[] = suppliersQuery.data?.items ?? []

  const doneLines = purchaseRequest.items.filter(
    (item): item is PurchaseRequestItem & { id: number } => !!item.id,
  )
  if (!isDispatched(purchaseRequest.status) || doneLines.length === 0) return null

  // Cùng luật `ensure_own_line` + see-all của backend: thu mua thường chỉ đụng
  // được dòng mình phụ trách, người giữ quyền duyệt đụng được mọi dòng.
  const isLineActionable = (item: PurchaseRequestItem) =>
    canApprove || (!!item.assignee && item.assignee === userEmpCode)

  // Khu áp hàng loạt chỉ nhận dòng ĐANG CHỌN một phương án còn thiếu NCC và
  // không phải phương án khảo sát — đúng các dòng backend sẽ chấp nhận.
  const bulkLines = canEditPurchase
    ? doneLines.filter(
        (item) =>
          isLineActionable(item) &&
          !!item.chosen_option &&
          item.chosen_option.source !== PR_OPTION_SOURCE_SURVEY &&
          !item.chosen_option.supplier_code &&
          !item.chosen_option.supplier_name,
      )
    : []

  return (
    <Card className="gap-4 py-4">
      {/* bao-CR-310 đợt 4 (rà lại): nút GOM và nút IN THEO NCC dời lên đầu
          trang chi tiết, nhập vào nút "Tạo đơn mua hàng" / "In phiếu" sổ xuống
          — khách góp ý 4 nút rời là quá nhiều. Thẻ này chỉ còn phần chọn. */}
      <CardHeader className="min-h-9 flex flex-row items-center gap-3 border-b px-4 pb-3!">
        <CardTitle className="flex items-center gap-2 text-base text-navy dark:text-foreground">
          <ListChecks className="size-4 text-primary" />
          Phương án — chọn phương án mua
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6 px-4">
        {canChoose ? (
          <p className="text-xs text-muted-foreground">
            Với mỗi sản phẩm, nhấn chọn 1 phương án phù hợp nhất; bấm lại phương án đang chọn để
            BỎ CHỌN. <b>Phương án 0</b> là mua đúng theo dòng yêu cầu gốc — không chọn gì thì hệ
            coi như mua theo nó. Phương án NSTM gắn thêm sẽ hiện ngay ở đây.
          </p>
        ) : (
          <p className="text-xs text-muted-foreground">
            Chỉ người yêu cầu hoặc quản lý thu mua chọn được phương án — bạn đang xem.
          </p>
        )}
        {canEditPurchase && (
          <p className="text-xs text-muted-foreground">
            Bạn thuộc thu mua: sửa được <b>giá</b> của mọi phương án và điền <b>NCC</b> cho
            phương án 0 / nhập tay ngay trên từng thẻ (kể cả dòng đã chốt).
          </p>
        )}

        {bulkLines.length > 0 && (
          <BulkAssignSupplierZone
            purchaseRequestId={purchaseRequest.id}
            lines={bulkLines}
            suppliers={suppliers}
          />
        )}

        {doneLines.map((item, index) => (
          <ChooseLineSection
            key={item.id}
            purchaseRequestId={purchaseRequest.id}
            item={item}
            lineNumber={index + 1}
            canChoose={canChoose}
            canSeeSupplier={canSeeSupplier}
            canEditOptions={canEditPurchase && isLineActionable(item)}
            suppliers={suppliers}
          />
        ))}

        {/* bao-CR-419 — KHÔNG có nút "Chốt xong lựa chọn" ở đây nữa (đại ca chốt
            17/09/2026). Người yêu cầu chọn phương án là đủ; bắt họ bấm thêm một
            nút xác nhận chỉ để đánh dấu "tôi đã xem" là dựng thêm một cửa ải cho
            một việc họ vừa làm xong ngay bên trên. Việc CHỐT MUA sẽ có chỗ riêng
            sau, nên mốc dưới DB (`options_chosen_at` / `options_chosen_by`) cùng
            đường API `/choice-done` vẫn giữ nguyên — chỉ là hiện chưa có lối bấm
            nào gọi tới. Không chỗ nào chặn việc lập đơn theo mốc này. */}
      </CardContent>
    </Card>
  )
}

function ChooseLineSection({
  purchaseRequestId,
  item,
  lineNumber,
  canChoose,
  canSeeSupplier,
  canEditOptions,
  suppliers,
}: {
  purchaseRequestId: number
  item: PurchaseRequestItem & { id: number }
  lineNumber: number
  canChoose: boolean
  canSeeSupplier: boolean
  /** Tầng thu mua trên DÒNG NÀY: sửa giá mọi phương án + điền NCC phương án 0 / nhập tay. */
  canEditOptions: boolean
  suppliers: SupplierOption[]
}) {
  // Đợt 2 MỞ RỘNG: dòng chốt rỗng vẫn có PHƯƠNG ÁN 0 (backend tự sinh) nên
  // luôn gọi API — bản cũ tắt query bằng itemId=0 là theo luật cũ "chốt rỗng
  // không mua được", nay đã bỏ.
  const optionsQuery = usePurchaseRequestItemOptions(purchaseRequestId, item.id)
  const options = optionsQuery.data?.items ?? []
  const reopenMutation = useReopenPrOptionsLine(purchaseRequestId)
  const [editingOption, setEditingOption] = useState<PurchaseRequestOption | null>(null)

  const chooseMutation = useChooseOption(purchaseRequestId)
  // `disabled={isPending}` không chặn nổi bấm đúp (state React trễ một render) —
  // chặn bằng ref đổi ngay trong tick, giống luật biểu mẫu duoc-CR-317.
  const choosingRef = useRef(false)
  const chooseOption = (option: PurchaseRequestOption) => {
    if (choosingRef.current) return
    choosingRef.current = true
    chooseMutation.mutate(
      { itemId: item.id, optionId: option.id, wasChosen: option.is_chosen },
      {
        onSettled: () => {
          choosingRef.current = false
        },
      },
    )
  }

  return (
    <section className="space-y-2.5">
      <div className="flex flex-wrap items-center gap-2">
        <h4 className="font-semibold">
          Sản phẩm {lineNumber}: {item.product_name || item.product_code || '—'}
        </h4>
        {!item.options_done && (
          <Badge variant="secondary" className="border-0 bg-warning/10 text-warning">
            NSTM đang xử lý
          </Badge>
        )}
        {canChoose && item.options_done && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={reopenMutation.isPending}
            title="Hạ cờ chốt hoàn thành để NSTM gắn thêm / sửa phương án của dòng này"
            onClick={() => reopenMutation.mutate(item.id)}
          >
            {reopenMutation.isPending ? <Loader2 className="animate-spin" /> : <Undo2 />}
            Mở lại cho NSTM xử lý
          </Button>
        )}
      </div>

      <p className="text-xs text-muted-foreground">
        Mã hàng: <b>{item.product_code || '—'}</b> · SL: <b>{formatQuantity(item.qty) || '—'}</b>{' '}
        {item.unit} · Phụ trách: <b>{item.assignee || '—'}</b>
      </p>

      {item.no_option && (
        <p className="flex items-center gap-2 rounded-lg border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
          <Ban className="size-4 shrink-0" />
          NSTM chốt rỗng: không có NCC phù hợp cho dòng hàng này — vẫn mua được theo{' '}
          <b>Phương án 0</b> (đúng dòng yêu cầu gốc) bên dưới.
        </p>
      )}

      {optionsQuery.isLoading ? (
        <p className="flex items-center gap-2 px-1 py-2 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          Đang tải phương án...
        </p>
      ) : options.length === 0 ? (
        <p className="rounded-lg border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
          Chưa có phương án nào cho dòng hàng này.
        </p>
      ) : (
        //  Cột tự lấp theo bề rộng, mỗi thẻ ghim trong khoảng 18–22rem — cùng lý
        //  do với khu Kết quả khảo sát YCBG: màn rộng xếp nhiều thẻ/hàng, dòng
        //  chỉ có MỘT phương án cũng không kéo dài nửa màn.
        <div className="grid gap-3 [grid-template-columns:repeat(auto-fill,minmax(18rem,22rem))]">
          {options.map((option) => (
            <PrOptionCard
              key={option.id}
              option={option}
              canChoose={canChoose}
              canSeeSupplier={canSeeSupplier}
              onChoose={() => chooseOption(option)}
              onEdit={canEditOptions ? () => setEditingOption(option) : undefined}
            />
          ))}
        </div>
      )}

      {/* bao-CR-583: phương án 0 và nhập tay mở hộp sửa ĐỦ thông tin (phương án 0 kèm «Khôi
          phục ban đầu»); phương án khảo sát giữ hộp chỉ sửa giá. */}
      {editingOption && editingOption.source !== PR_OPTION_SOURCE_SURVEY && (
        <PurchaseRequestOptionEditDialog
          purchaseRequestId={purchaseRequestId}
          itemId={item.id}
          option={editingOption}
          suppliers={suppliers}
          onClose={() => setEditingOption(null)}
        />
      )}
      {editingOption && editingOption.source === PR_OPTION_SOURCE_SURVEY && (
        <OptionPurchaseEditDialog
          purchaseRequestId={purchaseRequestId}
          itemId={item.id}
          option={editingOption}
          suppliers={suppliers}
          onClose={() => setEditingOption(null)}
        />
      )}
    </section>
  )
}

function PrOptionCard({
  option,
  canChoose,
  canSeeSupplier,
  onChoose,
  onEdit,
}: {
  option: PurchaseRequestOption
  canChoose: boolean
  canSeeSupplier: boolean
  onChoose: () => void
  /** Có mặt = tầng thu mua trên dòng này: mở hộp sửa giá / NCC của phương án. */
  onEdit?: () => void
}) {
  const label = option.display_label || `Phương án ${option.public_id}`

  return (
    // Cả thẻ là vùng bấm chọn (không chỉ ô radio) — cùng lý do với OptionCard
    // của YCBG: thẻ cao cả trăm pixel, bắt nhắm đúng ô tròn 16px là chuốc lỗi.
    <div
      role={canChoose ? 'radio' : undefined}
      aria-checked={canChoose ? option.is_chosen : undefined}
      tabIndex={canChoose ? 0 : undefined}
      className={cn(
        'rounded-xl border-2 p-3.5 transition-colors',
        option.is_chosen ? 'border-primary bg-primary/5' : 'border-border bg-card',
        canChoose ? 'cursor-pointer hover:border-primary/50' : 'cursor-default',
        !canChoose && !option.is_chosen && 'opacity-55',
      )}
      onClick={() => canChoose && onChoose()}
      onKeyDown={(event) => {
        if (canChoose && (event.key === 'Enter' || event.key === ' ')) {
          event.preventDefault()
          onChoose()
        }
      }}
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="flex items-center gap-2 font-semibold">
          <input type="radio" checked={option.is_chosen} readOnly className="size-4" />
          {label}
        </span>
        <span className="flex items-center gap-1.5">
          {option.is_chosen && (
            <Badge variant="secondary" className="border-0 bg-success/10 text-success">
              Đã chọn
            </Badge>
          )}
          {onEdit && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="-my-1 size-7"
              //  bao-CR-583: phương án 0 / nhập tay mở hộp sửa ĐỦ thông tin.
              aria-label={
                option.source === PR_OPTION_SOURCE_SURVEY ? `Sửa giá của ${label}` : `Sửa ${label}`
              }
              title={
                option.source === PR_OPTION_SOURCE_SURVEY
                  ? 'Sửa giá của phương án (thông số là kết quả khảo sát)'
                  : 'Sửa thông tin phương án'
              }
              // Nút nằm TRONG vùng bấm chọn của thẻ — nuốt sự kiện kẻo bấm
              // Sửa lại thành chọn/bỏ chọn phương án.
              onClick={(event) => {
                event.stopPropagation()
                onEdit()
              }}
              onKeyDown={(event) => event.stopPropagation()}
            >
              <PenLine />
            </Button>
          )}
        </span>
      </div>

      <p className="mb-2 font-medium">{option.snap_product_name || '—'}</p>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
        {/* Tên NCC chỉ hiện cho người có supplier:read — người yêu cầu thường
            chọn theo thông số và giá, đúng chính sách của màn xử lý. */}
        {canSeeSupplier && (
          <OptionField label="NCC" value={option.supplier_name || option.supplier_code} />
        )}
        <OptionField label="Nguồn" value={option.source_label} />
        <OptionField label="Mã VTBB" value={option.snap_internal_code} />
        <OptionField
          label="Đơn giá"
          value={
            option.snap_price_by_volume ? `${formatUnitPrice(option.snap_price_by_volume)} đ` : ''
          }
          strong
        />
        <OptionField label="ĐVT báo giá" value={option.snap_quote_unit} />
        <OptionField label="MOQ" value={formatQuantity(option.snap_moq)} />
        <OptionField label="Khoảng SL áp giá" value={option.snap_volume_range} />
        <OptionField label="VAT" value={option.snap_vat ? `${option.snap_vat}%` : ''} />
        <OptionField label="Xuất xứ" value={option.snap_origin} />
        <OptionField label="Thời gian giao" value={option.snap_delivery_time} />
        <OptionField label="Địa điểm giao" value={option.snap_delivery_place} />
        {/* Không có phí ship KHÔNG phải là thiếu dữ liệu — là miễn phí. */}
        <OptionField
          label="Phí vận chuyển"
          value={
            option.snap_shipping_cost
              ? `${formatUnitPrice(option.snap_shipping_cost)} đ`
              : 'Miễn phí'
          }
        />
        <OptionField label="Có mẫu" value={option.snap_sample_ready ? 'Có' : 'Không'} />
        <OptionField label="Kết quả lab" value={option.snap_lab_result} />
      </dl>

      {!!option.snap_spec && (
        <p className="mt-2 border-t border-dashed pt-2 text-xs">
          <span className="text-muted-foreground">Thông số: </span>
          {option.snap_spec}
        </p>
      )}

      {!!option.nstm_note && (
        <p className="mt-2 border-t border-dashed pt-2 text-xs whitespace-pre-wrap">
          <span className="text-muted-foreground">Ghi chú NSTM: </span>
          {option.nstm_note}
        </p>
      )}
    </div>
  )
}

/**
 * Hộp SỬA GIÁ / NCC của một phương án — tầng thu mua trên màn chọn (H.10.5).
 * Phương án từ KHẢO SÁT chỉ sửa được giá (NCC là danh tính của kết quả khảo
 * sát, backend từ chối đổi); phương án 0 / nhập tay sửa được cả hai. Có NCC thì
 * đi đường `setSupplier` (kèm giá nếu đổi), không thì PATCH giá đơn thuần —
 * đường PATCH này backend cho chạy cả sau chốt (price-only, khe H.10.4).
 */
function OptionPurchaseEditDialog({
  purchaseRequestId,
  itemId,
  option,
  suppliers,
  onClose,
}: {
  purchaseRequestId: number
  itemId: number
  option: PurchaseRequestOption
  suppliers: SupplierOption[]
  onClose: () => void
}) {
  const canEditNcc = option.source !== PR_OPTION_SOURCE_SURVEY
  const [supplierCode, setSupplierCode] = useState(option.supplier_code || NO_SUPPLIER)
  // Chỉ đổ tên vào ô gõ tay khi NCC hiện tại là NCC ngoài danh mục (không mã) —
  // NCC trong danh mục đã nằm ở ô chọn, đổ cả hai là gửi trùng.
  const [supplierName, setSupplierName] = useState(
    option.supplier_code ? '' : option.supplier_name,
  )
  const [priceRaw, setPriceRaw] = useState(
    option.snap_price_by_volume ? String(option.snap_price_by_volume) : '',
  )

  const setSupplierMutation = useSetPrOptionSupplier(purchaseRequestId)
  const updateMutation = useUpdateOption(purchaseRequestId)
  const submittingRef = useRef(false)

  const label = option.display_label || `Phương án ${option.public_id}`

  const submit = () => {
    if (submittingRef.current) return
    const code = supplierCode === NO_SUPPLIER ? '' : supplierCode
    const name = supplierName.trim()
    const price = parsePriceInput(priceRaw)
    const priceChanged = price !== undefined && price !== option.snap_price_by_volume

    const callbacks = {
      onSuccess: onClose,
      onSettled: () => {
        submittingRef.current = false
      },
    }
    if (canEditNcc && (code || name)) {
      submittingRef.current = true
      setSupplierMutation.mutate(
        {
          itemId,
          optionId: option.id,
          payload: {
            supplier_code: code,
            supplier_name: name,
            ...(priceChanged ? { snap_price_by_volume: price } : {}),
          },
        },
        callbacks,
      )
    } else if (priceChanged) {
      submittingRef.current = true
      updateMutation.mutate(
        { itemId, optionId: option.id, payload: { snap_price_by_volume: price } },
        callbacks,
      )
    } else {
      toast.error('Chưa có thay đổi nào để lưu')
    }
  }

  const pending = setSupplierMutation.isPending || updateMutation.isPending
  const supplierOptions = [
    { value: NO_SUPPLIER, label: '— Không chọn —' },
    ...suppliers.map((supplier) => ({
      value: supplier.code,
      label: `${supplier.code} — ${supplier.name}`,
    })),
  ]

  return (
    //  bao-CR-570: dựng lại cho gọn — một cột, ô nào cũng chiếm hết bề ngang hộp (bản cũ để
    //  ô chọn + ô gõ tay w-64 cạnh nhau, rớt dòng lệch nhau, nhãn «Đơn giá» chen ngang ô).
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Sửa giá / NCC — {label}</DialogTitle>
          <DialogDescription>
            {canEditNcc
              ? 'Chọn nhà cung cấp và đơn giá cho phương án này.'
              : 'Phương án từ khảo sát: nhà cung cấp theo kết quả khảo sát, chỉ sửa được đơn giá.'}
          </DialogDescription>
        </DialogHeader>

        {/* `min-w-0`: `DialogContent` là lưới, cột tự giãn theo chữ dài nhất. Tên NCC dài trong ô
            chọn (vd «NCCKS030 — Cty TNHH Thương Mại Dịch Vụ Và Phát Triển Thiên An Phát») đẩy cả
            khối tràn ra ngoài khung trắng — ô sản phẩm phía trên lòi một mảng xám ở mép phải. */}
        <div className="min-w-0 space-y-4">
          <div className="rounded-lg border bg-muted/40 px-3 py-2 text-sm">
            <p className="font-medium leading-snug">{option.snap_product_name || '—'}</p>
            <p className="text-xs text-muted-foreground">
              Đơn giá hiện tại:{' '}
              <b>
                {option.snap_price_by_volume
                  ? `${formatUnitPrice(option.snap_price_by_volume)} đ`
                  : '—'}
              </b>
              {!canEditNcc && !!(option.supplier_name || option.supplier_code) && (
                <> · NCC: <b>{option.supplier_name || option.supplier_code}</b></>
              )}
            </p>
          </div>

          {canEditNcc && (
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Nhà cung cấp</label>
              <SearchSelect
                className="w-full"
                value={supplierCode}
                onChange={(value) => {
                  setSupplierCode(value)
                  //  Hai ô loại trừ nhau: chọn NCC trong danh mục thì bỏ tên gõ tay.
                  if (value !== NO_SUPPLIER) setSupplierName('')
                }}
                placeholder="Chọn NCC trong danh mục"
                searchPlaceholder="Tìm NCC theo mã / tên…"
                options={supplierOptions}
              />
              <Input
                value={supplierName}
                placeholder="Hoặc gõ tên NCC ngoài danh mục"
                onChange={(event) => {
                  setSupplierName(event.target.value)
                  if (event.target.value.trim()) setSupplierCode(NO_SUPPLIER)
                }}
              />
            </div>
          )}

          <div className="space-y-1.5">
            <label htmlFor={`option-price-${option.id}`} className="text-sm font-medium">
              Đơn giá
            </label>
            <div className="relative">
              <Input
                id={`option-price-${option.id}`}
                type="number"
                min={0}
                inputMode="decimal"
                className="pr-8 text-right tabular-nums"
                value={priceRaw}
                onChange={(event) => setPriceRaw(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    event.preventDefault()
                    submit()
                  }
                }}
              />
              <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-sm text-muted-foreground">
                đ
              </span>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            Hủy
          </Button>
          <Button type="button" disabled={pending} onClick={submit}>
            {pending && <Loader2 className="animate-spin" />}
            Lưu
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/**
 * Khu "ÁP 1 NCC CHO NHIỀU DÒNG" (H.10.5): các dòng đang chọn một phương án còn
 * thiếu NCC (thường là phương án 0) — tick dòng, chọn MỘT NCC, sửa giá theo
 * dòng nếu cần, áp một phát. Cả gói ăn theo nhau: một dòng không hợp lệ là
 * backend hủy nguyên lô, không có chuyện áp được một nửa.
 */
function BulkAssignSupplierZone({
  purchaseRequestId,
  lines,
  suppliers,
}: {
  purchaseRequestId: number
  lines: (PurchaseRequestItem & { id: number })[]
  suppliers: SupplierOption[]
}) {
  const [checkedItemIds, setCheckedItemIds] = useState<number[]>([])
  const [supplierCode, setSupplierCode] = useState(NO_SUPPLIER)
  const [supplierName, setSupplierName] = useState('')
  const [priceByItem, setPriceByItem] = useState<Record<number, string>>({})
  const assignMutation = useAssignPrSupplierBulk(purchaseRequestId)
  const submittingRef = useRef(false)

  const submit = () => {
    if (submittingRef.current) return
    const code = supplierCode === NO_SUPPLIER ? '' : supplierCode
    const name = supplierName.trim()
    if (!code && !name) {
      toast.error('Phải chọn hoặc gõ tên nhà cung cấp để áp')
      return
    }
    if (checkedItemIds.length === 0) {
      toast.error('Chưa tick dòng nào để áp NCC')
      return
    }
    const items: PrAssignSupplierLine[] = checkedItemIds.map((itemId) => {
      const price = parsePriceInput(priceByItem[itemId] ?? '')
      return price === undefined ? { item_id: itemId } : { item_id: itemId, snap_price_by_volume: price }
    })
    submittingRef.current = true
    assignMutation.mutate(
      { supplier_code: code, supplier_name: name, items },
      {
        onSuccess: () => {
          setCheckedItemIds([])
          setPriceByItem({})
        },
        onSettled: () => {
          submittingRef.current = false
        },
      },
    )
  }

  const allChecked = lines.length > 0 && checkedItemIds.length === lines.length
  const toggleAll = (checked: boolean) =>
    setCheckedItemIds(checked ? lines.map((item) => item.id) : [])
  const hasSupplier = supplierCode !== NO_SUPPLIER || !!supplierName.trim()

  return (
    //  bao-CR-570: dựng lại cho gọn — thanh NCC + nút áp một hàng ở TRÊN, bên dưới là bảng
    //  nhỏ (chọn tất cả · sản phẩm · giá hiện tại · giá mới). Bản cũ trải mỗi dòng một khung
    //  rộng hết màn, ô giá trôi tận mép phải, ô NCC nằm tách rời ở đáy.
    //  bao-CR-576 (đại ca chọn phương án C, 03/10/2026): khối KHÔNG trải hết màn nữa — cột tên
    //  hàng chiếm hết phần còn lại nên trên màn rộng giá bị đẩy ra tận mép phải, cách tên gần
    //  cả màn hình, người ta dễ bỏ qua. Thu về `max-w-4xl` cho giá đứng sát tên hàng.
    <div className="max-w-4xl overflow-hidden rounded-lg border">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b bg-muted/40 px-3 py-2">
        <p className="mr-auto text-sm font-medium">
          Áp 1 NCC cho nhiều dòng
          <span className="ml-1.5 text-xs font-normal text-muted-foreground">
            ({lines.length} dòng đang chọn phương án chưa có NCC)
          </span>
        </p>
        <SearchSelect
          className="w-60"
          value={supplierCode}
          onChange={(value) => {
            setSupplierCode(value)
            if (value !== NO_SUPPLIER) setSupplierName('')
          }}
          placeholder="Chọn NCC trong danh mục"
          searchPlaceholder="Tìm NCC theo mã / tên…"
          options={[
            { value: NO_SUPPLIER, label: '— Không chọn —' },
            ...suppliers.map((supplier) => ({
              value: supplier.code,
              label: `${supplier.code} — ${supplier.name}`,
            })),
          ]}
        />
        <Input
          className="w-60"
          value={supplierName}
          placeholder="Hoặc tên NCC ngoài danh mục"
          onChange={(event) => {
            setSupplierName(event.target.value)
            if (event.target.value.trim()) setSupplierCode(NO_SUPPLIER)
          }}
        />
        <Button
          type="button"
          size="sm"
          disabled={assignMutation.isPending || checkedItemIds.length === 0 || !hasSupplier}
          onClick={submit}
        >
          {assignMutation.isPending && <Loader2 className="animate-spin" />}
          Áp cho {checkedItemIds.length} dòng
        </Button>
      </div>

      <div className="grid grid-cols-[2rem_minmax(0,1fr)_7rem_9rem] items-center gap-x-3 border-b px-3 py-1.5 text-xs font-medium text-muted-foreground">
        <Checkbox
          checked={allChecked}
          onCheckedChange={(checked) => toggleAll(checked === true)}
          aria-label="Chọn tất cả dòng"
        />
        <span>Sản phẩm</span>
        <span className="text-right">Giá hiện tại</span>
        <span className="text-right">Giá mới (tùy chọn)</span>
      </div>
      <ul className="divide-y">
        {lines.map((item) => {
          const chosen = item.chosen_option
          const chosenLabel = chosen ? chosen.display_label || `Phương án ${chosen.public_id}` : '—'
          //  bao-CR-576: dòng có giá mới KHÁC giá cũ thì tô nổi, gạch giá cũ và nói rõ đổi bao nhiêu.
          const priceChange = describeBulkPriceChange(
            chosen?.snap_price_by_volume,
            priceByItem[item.id] ?? '',
          )
          return (
            <li
              key={item.id}
              className={cn(
                'grid grid-cols-[2rem_minmax(0,1fr)_7rem_9rem] items-center gap-x-3 px-3 py-1.5',
                priceChange && 'bg-warning/10',
              )}
            >
              <Checkbox
                id={`bulk-ncc-line-${item.id}`}
                checked={checkedItemIds.includes(item.id)}
                onCheckedChange={(checked) =>
                  setCheckedItemIds((prev) =>
                    checked === true ? [...prev, item.id] : prev.filter((id) => id !== item.id),
                  )
                }
              />
              <label htmlFor={`bulk-ncc-line-${item.id}`} className="min-w-0 cursor-pointer text-sm">
                <span className="block truncate font-medium" title={item.product_name}>
                  {item.product_name || item.product_code || '—'}
                </span>
                {priceChange ? (
                  <span className="block text-xs font-medium text-warning">
                    {chosenLabel} · Đổi giá:{' '}
                    {chosen?.snap_price_by_volume
                      ? `${formatUnitPrice(chosen.snap_price_by_volume)} đ`
                      : '—'}{' '}
                    → {formatUnitPrice(priceChange.next)} đ
                  </span>
                ) : (
                  <span className="block text-xs text-muted-foreground">{chosenLabel}</span>
                )}
              </label>
              <span
                className={cn(
                  'text-right text-sm tabular-nums',
                  priceChange && 'text-muted-foreground line-through',
                )}
              >
                {chosen?.snap_price_by_volume
                  ? `${formatUnitPrice(chosen.snap_price_by_volume)} đ`
                  : '—'}
              </span>
              <Input
                type="number"
                min={0}
                inputMode="decimal"
                className="h-8 text-right tabular-nums"
                aria-label={`Đơn giá mới cho ${item.product_name || item.product_code}`}
                placeholder="Giữ nguyên"
                value={priceByItem[item.id] ?? ''}
                onChange={(event) => {
                  const raw = event.target.value
                  setPriceByItem((prev) => ({ ...prev, [item.id]: raw }))
                  //  bao-CR-576: giá mới chỉ áp cho dòng ĐÃ TICK — gõ giá mà quên tick là giá bị
                  //  bỏ qua im lặng. Gõ giá thì tự tick dòng đó; bỏ tick vẫn làm tay được.
                  if (raw.trim())
                    setCheckedItemIds((prev) => (prev.includes(item.id) ? prev : [...prev, item.id]))
                }}
              />
            </li>
          )
        })}
      </ul>
    </div>
  )
}

function OptionField({
  label,
  value,
  strong = false,
}: {
  label: string
  value: string
  strong?: boolean
}) {
  //  Nhãn + giá trị nằm CÙNG DÒNG "Nhãn: giá trị" như thẻ phương án YCBG — tách
  //  hai dòng làm thẻ cao gấp đôi. Giá trị rỗng hiện "—" kẻo nhãn lửng lơ.
  return (
    <div className="break-words">
      <dt className="inline text-muted-foreground">{label}: </dt>
      <dd className={cn('inline', strong && 'font-semibold')}>{value || '—'}</dd>
    </div>
  )
}
