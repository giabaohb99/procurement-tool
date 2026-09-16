import { ArrowLeft, Printer, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { ErrorState } from '@/shared/ui/error-state'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatMoney } from '@/shared/utils/format-money'
import { usePurchaseRequest } from '../hooks/use-purchase-request'
import { usePurchaseRequestPrintWarehouses } from '../hooks/use-purchase-request-support'
import type { PurchaseRequestDetail, SupplierCluster } from '../types/purchase-request-detail'
import {
  buildSupplierPrintPlan,
  type SupplierPrintGroup,
} from '../utils/purchase-request-print-options'
// In LẠI ĐÚNG tờ phiếu đề xuất của bản A, kể cả khuôn CSS — khách chốt 15/09/2026.
import {
  PrintToggle,
  PURCHASE_REQUEST_PRINT_STYLES,
  PurchaseRequestPrintSheet,
} from './purchase-request-print-page'

/**
 * bao-CR-310 đợt 4 — BẢN B (H.6 doc 03): in phiếu YCMH TÁCH THEO NHÀ CUNG CẤP.
 *
 * Mỗi trang là MỘT TỜ PHIẾU ĐỀ XUẤT y mẫu 003/BM/PKT (bản A), chỉ khác hai chỗ:
 * bảng hàng chỉ còn dòng đã chọn phương án của NCC đó, và ô "NHÀ CUNG CẤP DO BỘ
 * PHẬN ĐỀ XUẤT" điền sẵn tên NCC đó. Tick NCC nào trên thanh công cụ thì in tờ
 * đó; dòng chưa có NCC dồn vào tờ cuối.
 *
 * Ba vòng trước bản này là một BỐ CỤC RIÊNG ("Bảng hàng theo nhà cung cấp") và
 * khách bác cả ba lần vì không theo mẫu chung. Luật rút ra: đừng thiết kế biến
 * thể của tờ phiếu, chỉ đổi DỮ LIỆU đổ vào tờ phiếu.
 *
 * Đây là BẢN LƯU/KÝ nên dòng đã nằm trên ĐMH vẫn in — tạo đơn xong phải in lại
 * được (góp ý khách 15/09); chống tạo trùng là việc của nút gom, không phải của
 * tờ in.
 *
 * Gác N-17: bản in lộ tên NCC nên đường vào đòi `supplier:read` — thiếu quyền
 * thì chặn cả trang (dữ liệu NCC phía backend cũng đã bị che, đây là lớp nói
 * thành lời). Route nằm ngoài ModuleLayout như các bản in khác.
 */
export function PurchaseRequestSupplierPrintPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { can } = usePermission()
  const canSeeSupplier = can('supplier', 'read')
  const { data: purchaseRequest, isLoading, isError } = usePurchaseRequest(
    canSeeSupplier ? Number(id) : 0,
  )
  const { data: warehouses } = usePurchaseRequestPrintWarehouses()
  // Tick mặc định TẤT CẢ các NCC; lưu tập BỎ tick để không phải chờ dữ liệu về.
  const [unchecked, setUnchecked] = useState<ReadonlySet<string>>(new Set())
  const [taxMode, setTaxMode] = useState(false)
  const [showSignature, setShowSignature] = useState(true)

  const plan = useMemo(
    () => buildSupplierPrintPlan(purchaseRequest?.items ?? []),
    [purchaseRequest?.items],
  )
  const printedGroups = plan.groups.filter((group) => !unchecked.has(group.key))

  const warehouseCodes = useMemo(
    () => new Map((warehouses?.items ?? []).map((warehouse) => [warehouse.name, warehouse.code])),
    [warehouses?.items],
  )

  useEffect(() => {
    if (!purchaseRequest?.code) return
    const previousTitle = document.title
    document.title = `${purchaseRequest.code} - Phiếu đề xuất theo nhà cung cấp`
    return () => {
      document.title = previousTitle
    }
  }, [purchaseRequest?.code])

  if (!canSeeSupplier) {
    return (
      <ErrorState
        title="Không mở được bản in theo nhà cung cấp"
        description="Bản in này ghi tên nhà cung cấp nên cần quyền xem nhà cung cấp (supplier:read). Liên hệ quản trị nếu bạn cần quyền này."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.procurement.purchaseRequests)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  if (isLoading) {
    return (
      <main className="min-h-[100dvh] bg-slate-200 p-5">
        <Skeleton className="mx-auto mb-3 h-10 max-w-[210mm]" />
        <Skeleton className="mx-auto h-[297mm] max-w-[210mm] bg-white" />
      </main>
    )
  }

  if (isError || !purchaseRequest) {
    return (
      <ErrorState
        title="Không mở được bản in"
        description="Phiếu có thể đã bị xóa, hoặc ngoài phạm vi dữ liệu bạn được xem."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.procurement.purchaseRequests)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  const skippedNotes: string[] = []
  if (plan.skipped.noChosen > 0) {
    skippedNotes.push(`${plan.skipped.noChosen} dòng không chọn phương án`)
  }
  if (plan.skipped.cancelled > 0) {
    skippedNotes.push(`${plan.skipped.cancelled} dòng đã hủy`)
  }

  const toggleGroup = (key: string) => {
    setUnchecked((current) => {
      const next = new Set(current)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  return (
    <main className="pr-print-root prs-print-root min-h-[100dvh] bg-slate-200 p-5 text-slate-950">
      <style>{PURCHASE_REQUEST_PRINT_STYLES}</style>
      <style>{MULTI_SHEET_STYLES}</style>

      <div className="pr-print-toolbar">
        <div className="pr-print-toolbar-actions">
          <Button onClick={() => window.print()} disabled={printedGroups.length === 0}>
            <Printer />
            In / Lưu PDF ({printedGroups.length} trang)
          </Button>
          <Button variant="outline" onClick={() => window.close()}>
            <X />
            Đóng
          </Button>
          {skippedNotes.length > 0 && (
            <span className="text-[12.5px] text-warning">
              Không in: {skippedNotes.join(' · ')}.
            </span>
          )}
        </div>

        <div className="pr-print-toolbar-options">
          {!taxMode && (
            <PrintToggle
              options={[
                { value: true, label: 'Có chữ ký' },
                { value: false, label: 'Không chữ ký' },
              ]}
              value={showSignature}
              onChange={setShowSignature}
            />
          )}
          <PrintToggle
            options={[
              { value: false, label: 'Mẫu thường' },
              { value: true, label: 'Mẫu thuế' },
            ]}
            value={taxMode}
            onChange={setTaxMode}
          />
        </div>
      </div>

      {/* Bảng tick NCC (H.6): mỗi NCC một dòng, tick NCC nào in tờ phiếu của NCC đó. */}
      <div className="prs-print-suppliers">
        {plan.groups.map((group) => (
          <label
            key={group.key || NO_SUPPLIER_KEY}
            className="flex cursor-pointer items-center gap-2 rounded-lg border bg-card px-3 py-1.5 text-[13px]"
          >
            <Checkbox
              checked={!unchecked.has(group.key)}
              onCheckedChange={() => toggleGroup(group.key)}
            />
            <span className="font-medium">{supplierTitle(group)}</span>
            <span className="text-muted-foreground">
              {group.lines.length} dòng · {formatMoney(group.total)}
            </span>
          </label>
        ))}
        {plan.groups.length === 0 && (
          <span className="text-[13px] text-muted-foreground">
            Chưa có dòng nào in được — phiếu chưa chọn phương án cho dòng nào.
          </span>
        )}
      </div>

      {printedGroups.map((group) => (
        <PurchaseRequestPrintSheet
          key={group.key || NO_SUPPLIER_KEY}
          purchaseRequest={purchaseRequest}
          items={group.lines.map((line) => line.item)}
          supplier={supplierClusterOf(purchaseRequest, group)}
          warehouseCode={(name) => warehouseCodes.get(name) || name}
          taxMode={taxMode}
          showSignature={showSignature}
        />
      ))}
    </main>
  )
}

const NO_SUPPLIER_KEY = '__no_supplier__'

function supplierTitle(group: SupplierPrintGroup): string {
  if (!group.key) return 'Chưa có nhà cung cấp'
  return group.supplierName || group.supplierCode
}

/**
 * Thông tin điền vào ô "NHÀ CUNG CẤP DO BỘ PHẬN ĐỀ XUẤT" của tờ phiếu.
 *
 * Phương án khảo sát chỉ chụp MÃ và TÊN nhà cung cấp, không chụp mã số thuế /
 * liên hệ — hai ô đó chỉ có ở hai cụm NCC nhập trên phiếu. Trùng tên thì mượn,
 * không trùng thì để trống chứ không đoán: in nhầm mã số thuế của NCC khác lên
 * tờ phiếu ký tay là sai lệch hồ sơ. Nhóm chưa có NCC để tên rỗng, tờ phiếu tự
 * in dòng mặc định "Nhà cung cấp tối ưu nhất" y bản A.
 */
function supplierClusterOf(
  purchaseRequest: PurchaseRequestDetail,
  group: SupplierPrintGroup,
): SupplierCluster {
  const name = group.key ? group.supplierName || group.supplierCode : ''
  const known = [purchaseRequest.supplier_pur, purchaseRequest.supplier_req].find(
    (cluster) => name !== '' && cluster.name === name,
  )
  return {
    name,
    tax_code: known?.tax_code ?? '',
    contact: known?.contact ?? '',
  }
}

/*  Trang này xếp NHIỀU tờ phiếu chồng nhau nên phải nói thêm ba điều mà khuôn
    một-tờ của bản A không cần:
    - trên màn hình: chừa khoảng cách giữa các tờ;
    - khi in: mỗi tờ ăn trọn một trang giấy, tờ cuối không đẻ trang trắng;
    - dòng chữ chân trang: bản A để `position: fixed` khi in (một tờ thì đúng),
      nhiều tờ thì trình duyệt lặp nó lên MỌI trang, chồng N dòng lên nhau —
      trả về `absolute` để nó nằm đúng chân tờ của nó. */
const MULTI_SHEET_STYLES = `
  .prs-print-suppliers {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    width: 210mm;
    max-width: calc(100vw - 48px);
    margin: 0 auto 16px;
  }

  .prs-print-root .pr-print-doc {
    margin: 0 auto 16px;
  }

  @media print {
    .prs-print-suppliers {
      display: none !important;
    }

    .prs-print-root .pr-print-doc {
      min-height: 297mm !important;
      margin: 0 auto !important;
      break-after: page;
      page-break-after: always;
    }

    .prs-print-root .pr-print-doc:last-of-type {
      break-after: auto;
      page-break-after: auto;
    }

    .prs-print-root .pr-print-note {
      position: absolute !important;
      right: 12mm !important;
      bottom: 7mm !important;
    }
  }

  @media screen and (max-width: 850px) {
    .prs-print-suppliers {
      min-width: 210mm;
      max-width: none;
    }
  }
`
