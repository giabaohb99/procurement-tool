import { ACTION_TONE_CLASS } from '@/shared/ui/action-tone'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { formatMoney } from '@/shared/utils/format-money'
import type { ImportCostSummaryBySupplier } from '../types/purchase-order-detail'

interface PurchaseOrderImportCostSupplierPaymentCardsProps {
  groups: ImportCostSummaryBySupplier[]
  /** Dòng tổng — cộng sẵn ở thẻ cha từ chính các nhóm đang bày. */
  totals: { count: number; base: number; paid: number; remaining: number }
  onCreatePaymentRequest: (payableIds: number[]) => void
}

/** Ba con số Phải trả · Đã chi · Còn lại, cùng màu với ba cột trên bảng. */
function MoneyTriplet({ base, paid, remaining }: { base: number; paid: number; remaining: number }) {
  return (
    //  Tự xuống 2 cột khi số tới hàng tỷ — 3 cột cứng thì "1.234.567.890 đ" tràn mép.
    <dl className="grid grid-cols-[repeat(auto-fit,minmax(6.5rem,1fr))] gap-2 text-xs">
      <div>
        <dt className="text-muted-foreground">Phải trả</dt>
        <dd className="font-medium tabular-nums">{formatMoney(base)} đ</dd>
      </div>
      <div>
        <dt className="text-muted-foreground">Đã chi</dt>
        <dd className="font-medium tabular-nums text-success">{formatMoney(paid)} đ</dd>
      </div>
      <div>
        <dt className="text-muted-foreground">Còn lại</dt>
        <dd
          className={cn(
            'font-semibold tabular-nums',
            remaining > 0.01 ? 'text-destructive' : 'text-muted-foreground',
          )}
        >
          {formatMoney(remaining)} đ
        </dd>
      </div>
    </dl>
  )
}

/**
 * Bảng "Thanh toán chi phí theo nhà cung cấp" ở khổ điện thoại: mỗi NCC một
 * thẻ, tên NCC lên đầu, mã màu sky; nút *Tạo YCTT* đứng ngay đầu thẻ như cột cuối
 * của bảng. Dòng *Tổng cộng* của chân bảng giữ lại thành một khối cuối danh sách.
 *
 * Thẻ KHÔNG có vùng chạm: bảng gốc cũng không mở gì khi bấm vào dòng, việc duy
 * nhất là nút Tạo YCTT.
 */
export function PurchaseOrderImportCostSupplierPaymentCards({
  groups,
  totals,
  onCreatePaymentRequest,
}: PurchaseOrderImportCostSupplierPaymentCardsProps) {
  return (
    <div className="divide-y">
      {groups.map((group) => {
        const settled = group.remaining <= 0.01
        return (
          <div key={group.supplier_code || '__empty__'} className="space-y-2 px-3 py-2.5">
            <div className="flex items-start gap-2">
              <div className="min-w-0 flex-1 space-y-0.5">
                {group.supplier_code ? (
                  <>
                    <p className="line-clamp-2 text-sm font-medium">
                      {group.supplier_name || group.supplier_code}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      <span className="font-medium text-sky-600 dark:text-sky-400">
                        {group.supplier_code}
                      </span>
                      <span> · {group.count} khoản</span>
                    </p>
                  </>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    (chưa chọn NCC — chưa thành công nợ) · {group.count} khoản
                  </p>
                )}
              </div>
              {settled ? (
                <Badge variant="outline" className="shrink-0">
                  Đã chi đủ
                </Badge>
              ) : (
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className={cn('shrink-0', ACTION_TONE_CLASS.accent)}
                  disabled={group.unpaid_payable_ids.length === 0}
                  onClick={() => onCreatePaymentRequest(group.unpaid_payable_ids)}
                >
                  Tạo YCTT
                </Button>
              )}
            </div>
            <MoneyTriplet base={group.base_amount} paid={group.paid_amount} remaining={group.remaining} />
          </div>
        )
      })}

      <div className="space-y-2 bg-muted/40 px-3 py-2.5">
        <p className="text-sm font-semibold">
          Tổng cộng <span className="font-normal text-muted-foreground">· {totals.count} khoản</span>
        </p>
        <MoneyTriplet base={totals.base} paid={totals.paid} remaining={totals.remaining} />
      </div>
    </div>
  )
}
