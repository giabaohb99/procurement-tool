import { ArrowLeft, Printer, X } from 'lucide-react'
import { Fragment, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { ErrorState } from '@/shared/ui/error-state'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import type { PurchaseOrderPrintData } from '../api/purchase-order-api'
import { usePurchaseOrderPrintData } from '../hooks/use-purchase-order'
import {
  DEFAULT_CURRENCY,
  type ImportCostAllocation,
  type ImportCostSummary,
  type PurchaseOrderImportCost,
} from '../types/purchase-order-detail'
import { costBaseAmount, lineBaseAmount } from '../utils/purchase-order-import-cost'

/**
 * bao-CR-319 P4 — bản in ĐƠN MUA HÀNG NHẬP KHẨU, bốn khối:
 *   A. Hàng hóa (VAT dòng hàng luôn 0, có cột kg; in cả nguyên tệ lẫn quy đổi)
 *   B. Chi phí lô hàng, lồng hai tầng theo LOẠI chi phí, kèm NCC của từng khoản
 *   C. Phải trả theo từng NHÀ CUNG CẤP (NCC bán hàng + từng NCC dịch vụ / thuế)
 *   D. Chi phí chia về từng dòng hàng — chỉ để xem, backend chia, không lưu, không vào kho
 *
 * Hai bản in thường (Đơn đặt hàng / Đơn mua hàng) giữ nguyên. Mọi con số ở B/C/D
 * đều ĐÃ QUY ĐỔI về VNĐ.
 */
export function PurchaseOrderImportPrintPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const purchaseOrderId = Number(id)
  const { data, isLoading, isError } = usePurchaseOrderPrintData(purchaseOrderId)

  useEffect(() => {
    if (!data?.code) return
    const previousTitle = document.title
    document.title = `${data.code}-NK - Đơn mua hàng nhập khẩu`
    return () => {
      document.title = previousTitle
    }
  }, [data?.code])

  if (isLoading) {
    return (
      <main className="min-h-[100dvh] bg-slate-200 p-5">
        <Skeleton className="mx-auto mb-3 h-10 max-w-[210mm]" />
        <Skeleton className="mx-auto h-[280mm] max-w-[210mm] bg-white" />
      </main>
    )
  }

  if (isError || !data) {
    return (
      <ErrorState
        title="Không mở được bản in"
        description="Đơn có thể đã bị xóa, hoặc bạn không có quyền in đơn này."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.procurement.purchaseOrders)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  return (
    <main className="po-print-root min-h-[100dvh] bg-slate-200 p-6 text-slate-950">
      <style>{PRINT_STYLES}</style>

      <div className="no-print mx-auto mb-3 flex max-w-[210mm] flex-wrap items-center gap-2">
        <Button onClick={() => window.print()}>
          <Printer />
          In / Lưu PDF
        </Button>
        <Button variant="outline" onClick={() => window.close()}>
          <X />
          Đóng
        </Button>
      </div>

      <PurchaseOrderImportPrintDocument data={data} />
    </main>
  )
}

const EMPTY_SUMMARY: ImportCostSummary = {
  goods_base_total: 0,
  cost_total: 0,
  paid_total: 0,
  remaining_total: 0,
  landed_total: 0,
  by_type: [],
  by_supplier: [],
}

const EMPTY_ALLOCATION: ImportCostAllocation = {
  lines: [],
  goods_base_total: 0,
  cost_total: 0,
  landed_total: 0,
  warnings: [],
}

interface CostGroup {
  label: string
  rows: PurchaseOrderImportCost[]
  total: number
}

/** Khối B lồng theo loại: mỗi loại một dòng tổng, bên dưới là từng khoản; loại to nhất lên đầu. */
function groupCostsByType(costs: PurchaseOrderImportCost[]): CostGroup[] {
  const groups: CostGroup[] = []
  for (const cost of costs) {
    const label = cost.cost_type_label || 'Khác'
    let group = groups.find((candidate) => candidate.label === label)
    if (!group) {
      group = { label, rows: [], total: 0 }
      groups.push(group)
    }
    group.rows.push(cost)
    group.total += cost.base_amount ?? costBaseAmount(cost)
  }
  return groups.sort((a, b) => b.total - a.total)
}

function percentOf(part: number, whole: number): string {
  // Ô rỗng thì để TRỐNG, không vẽ dấu gạch (khách 09/09/2026).
  if (!(whole > 0)) return ''
  return `${((part / whole) * 100).toFixed(1)}%`
}

function formatRatio(ratio: number): string {
  return `${(Number(ratio || 0) * 100).toFixed(2)}%`
}

function PurchaseOrderImportPrintDocument({ data }: { data: PurchaseOrderPrintData }) {
  const company = data.company ?? {}
  const supplier = data.supplier ?? {}
  const items = data.items ?? []
  const costs = data.import_costs ?? []
  const summary = data.import_cost_summary ?? EMPTY_SUMMARY
  const allocation = data.import_cost_allocation ?? EMPTY_ALLOCATION
  const currency = (data.currency || DEFAULT_CURRENCY).trim().toUpperCase()
  const exchangeRate = Number(data.exchange_rate) || 1

  // bao-CR-319 P5: tiền hàng đã trả = tổng "Đã trả theo dòng"; chi phí đã chi lấy từ summary.
  const goodsPaid = items.reduce((sum, item) => sum + (Number(item.paid_total) || 0), 0)
  const goodsForeign = items.reduce((sum, item) => sum + (Number(item.order_total) || 0), 0)
  const goodsRemaining = Math.max(summary.goods_base_total - goodsPaid, 0)
  const totalPaid = goodsPaid + summary.paid_total
  const totalRemaining = Math.max(summary.landed_total - totalPaid, 0)

  const costGroups = groupCostsByType(costs)
  const hasFallbackAllocation = allocation.lines.some((line) =>
    line.costs.some((share) => share.effective_method !== share.allocation_method),
  )

  return (
    <article className="po-print-doc po-print-doc--portrait">
      <div className="border-b-2 border-navy-solid pb-1.5">
        <p className="text-[13px] font-bold">{company.name}</p>
        <p className="text-[10.5px] italic">Địa chỉ: {company.address}</p>
      </div>

      <h1 className="mt-3 text-center text-[17px] font-bold">ĐƠN MUA HÀNG NHẬP KHẨU</h1>
      <p className="mb-2 text-center text-[10.5px] italic">
        Kèm bảng chi phí lô hàng và chi phí phân bổ theo dòng hàng (chỉ để tham khảo, không phải
        giá vốn)
      </p>

      <div className="flex justify-between text-[11.5px] leading-7">
        <div className="flex-1">
          <p>
            <b>Nhà cung cấp:</b> {supplier.name || data.supplier_name}
          </p>
          <p>
            <b>Địa chỉ:</b> {supplier.address}
          </p>
          <p>
            <b>Mã số thuế:</b> {supplier.tax_code}
          </p>
          <p>
            <b>Nhân viên mua hàng:</b> {data.nspt}
          </p>
          <p>
            <b>Diễn giải:</b> {data.note}
          </p>
        </div>
        <div className="w-[250px] pl-3">
          <p>
            <b>Ngày:</b> {formatDate(data.order_date)}
          </p>
          <p>
            <b>Số:</b> {data.misa_code || data.code}
          </p>
          <p>
            <b>Loại tiền:</b> {currency}
            {currency !== DEFAULT_CURRENCY ? ` — tỷ giá ${formatUnitPrice(exchangeRate)}` : ''}
          </p>
          <p>
            <b>Tờ khai hải quan:</b> {data.customs_decl_no || '..........'}
            {data.customs_decl_date ? ` ngày ${formatDate(data.customs_decl_date)}` : ''}
          </p>
        </div>
      </div>

      {/* A. Hàng hóa */}
      <section className="po-print-block">
        <h2 className="po-print-block-title">A. HÀNG HÓA</h2>
        <table className="po-print-table">
          <thead>
            <tr>
              <th>STT</th>
              <th>Mã hàng</th>
              <th>Tên hàng</th>
              <th>ĐVT</th>
              <th>SL đặt</th>
              <th>KL (kg)</th>
              <th>Đơn giá ({currency})</th>
              <th>Thành tiền ({currency})</th>
              <th>Quy đổi (VNĐ)</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={item.id ?? index}>
                <td className="text-center">{index + 1}</td>
                <td>{item.product_code}</td>
                <td>
                  {item.product_name}
                  {item.spec && <div className="text-[9.5px] italic">{item.spec}</div>}
                </td>
                <td className="text-center">{item.unit}</td>
                <td className="text-right">{formatQuantity(item.qty_order)}</td>
                <td className="text-right">
                  {item.weight_kg ? formatQuantity(item.weight_kg) : ''}
                </td>
                <td className="text-right">{formatUnitPrice(item.price)}</td>
                <td className="text-right">{formatUnitPrice(item.order_total)}</td>
                <td className="text-right">
                  {formatMoney(item.base_amount ?? lineBaseAmount(item, data))}
                </td>
              </tr>
            ))}
            <tr>
              <td className="font-bold" colSpan={7}>
                Tổng tiền hàng (VAT dòng hàng = 0, thuế nhập khẩu / GTGT hàng nhập khai ở khối
                B):
              </td>
              <td className="text-right font-bold">{formatUnitPrice(goodsForeign)}</td>
              <td className="text-right font-bold">{formatMoney(summary.goods_base_total)}</td>
            </tr>
          </tbody>
        </table>
      </section>

      {/* B. Chi phí lô hàng */}
      <section className="po-print-block">
        <h2 className="po-print-block-title">B. CHI PHÍ LÔ HÀNG</h2>
        <table className="po-print-table">
          {/*
            Ghim bề rộng từng cột: để trình duyệt tự chia thì cột Nhà cung cấp phình
            ra rất rộng còn tên NCC vẫn xuống ba dòng, nhìn thưa thớt (khách báo
            09/09/2026). Cột "Cách chia" bỏ hẳn theo yêu cầu — số chia đã có ở khối D.
          */}
          <colgroup>
            <col className="w-[32%]" />
            <col className="w-[24%]" />
            <col className="w-[15%]" />
            <col className="w-[13%]" />
            <col className="w-[6%]" />
            <col className="w-[10%]" />
          </colgroup>
          <thead>
            <tr>
              <th>Loại / Diễn giải</th>
              <th>Nhà cung cấp</th>
              <th>Số HĐ</th>
              <th>Số tiền (nguyên tệ)</th>
              <th>VAT</th>
              <th>Quy đổi gồm VAT (VNĐ)</th>
            </tr>
          </thead>
          <tbody>
            {costGroups.map((group) => (
              <Fragment key={group.label}>
                <tr className="po-print-row--group">
                  <td className="font-bold" colSpan={5}>
                    {group.label} ({group.rows.length} khoản)
                  </td>
                  <td className="text-right font-bold">{formatMoney(group.total)}</td>
                </tr>
                {group.rows.map((cost, index) => (
                  <tr key={cost.id ?? `${group.label}-${index}`}>
                    <td className="pl-4!">{cost.description}</td>
                    <td>{cost.supplier_name || cost.supplier_code}</td>
                    <td>
                      {cost.invoice_no}
                      {cost.invoice_date ? ` (${formatDate(cost.invoice_date)})` : ''}
                    </td>
                    <td className="text-right">
                      {formatUnitPrice(cost.amount)} {cost.currency || currency}
                    </td>
                    <td className="text-center">
                      {Number(cost.vat) ? `${formatQuantity(cost.vat)}%` : ''}
                    </td>
                    <td className="text-right">
                      {formatMoney(cost.base_amount ?? costBaseAmount(cost))}
                    </td>
                  </tr>
                ))}
              </Fragment>
            ))}
            {costs.length === 0 && (
              <tr>
                <td className="text-center italic" colSpan={6}>
                  Chưa khai chi phí nào cho lô hàng này
                </td>
              </tr>
            )}
            <tr>
              <td className="font-bold" colSpan={5}>
                Tổng chi phí lô hàng:
              </td>
              <td className="text-right font-bold">{formatMoney(summary.cost_total)}</td>
            </tr>
            <tr>
              <td className="font-bold" colSpan={5}>
                TỔNG GIÁ TRỊ LÔ HÀNG (tiền hàng + chi phí):
              </td>
              <td className="text-right font-bold">{formatMoney(summary.landed_total)}</td>
            </tr>
          </tbody>
        </table>
      </section>

      {/* C. Phải trả theo từng NCC */}
      <section className="po-print-block">
        <h2 className="po-print-block-title">C. PHẢI TRẢ THEO TỪNG NHÀ CUNG CẤP</h2>
        <table className="po-print-table">
          <thead>
            <tr>
              <th>STT</th>
              <th>Nhà cung cấp</th>
              <th>Nội dung</th>
              <th>Số khoản</th>
              <th>Phải trả (VNĐ)</th>
              <th>Đã chi (VNĐ)</th>
              <th>Còn lại (VNĐ)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="text-center">1</td>
              <td>{supplier.name || data.supplier_name}</td>
              <td>Tiền hàng ({currency})</td>
              <td className="text-center">{items.length} dòng</td>
              <td className="text-right">{formatMoney(summary.goods_base_total)}</td>
              <td className="text-right">{formatMoney(goodsPaid)}</td>
              <td className="text-right">{formatMoney(goodsRemaining)}</td>
            </tr>
            {summary.by_supplier.map((row, index) => (
              <tr key={row.supplier_code || index}>
                <td className="text-center">{index + 2}</td>
                <td>{row.supplier_name || row.supplier_code || '(chưa chọn NCC)'}</td>
                <td>Chi phí lô hàng</td>
                <td className="text-center">{row.count} khoản</td>
                <td className="text-right">{formatMoney(row.base_amount)}</td>
                <td className="text-right">{formatMoney(row.paid_amount)}</td>
                <td className="text-right">{formatMoney(row.remaining)}</td>
              </tr>
            ))}
            <tr>
              <td className="font-bold" colSpan={4}>
                Tổng phải trả:
              </td>
              <td className="text-right font-bold">{formatMoney(summary.landed_total)}</td>
              <td className="text-right font-bold">{formatMoney(totalPaid)}</td>
              <td className="text-right font-bold">{formatMoney(totalRemaining)}</td>
            </tr>
          </tbody>
        </table>
      </section>

      {/* D. Chi phí phân bổ theo dòng hàng */}
      <section className="po-print-block">
        <h2 className="po-print-block-title">D. CHI PHÍ PHÂN BỔ THEO DÒNG HÀNG</h2>
        <p className="mb-1 text-[10px] italic">
          Chia theo cách ghi ở từng khoản chi phí (khối B); phần lệch làm tròn dồn vào dòng cuối
          để tổng luôn khớp. Số này chỉ để tham khảo, không ghi nhận vào giá nhập kho.
        </p>
        {allocation.warnings.length > 0 && (
          <div className="mb-1 text-[10px] text-orange-800">
            {allocation.warnings.map((warning) => (
              <p key={warning}>Lưu ý: {warning}</p>
            ))}
          </div>
        )}
        <table className="po-print-table">
          <thead>
            <tr>
              <th>STT</th>
              <th>Mã hàng / Khoản chi phí</th>
              <th>Cách chia</th>
              <th>Tỷ lệ</th>
              <th>Tiền hàng (VNĐ)</th>
              <th>Chi phí phân bổ (VNĐ)</th>
              <th>Tổng giá trị (VNĐ)</th>
            </tr>
          </thead>
          <tbody>
            {allocation.lines.map((line, index) => (
              <Fragment key={line.item_id || index}>
                <tr className="po-print-row--group">
                  <td className="text-center font-bold">{index + 1}</td>
                  <td className="font-bold">
                    {line.product_code} — {line.product_name}{' '}
                    <span className="font-normal">
                      ({formatQuantity(line.qty_order)} {line.unit}
                      {line.weight_kg ? `, ${formatQuantity(line.weight_kg)} kg` : ''})
                    </span>
                  </td>
                  <td />
                  <td className="text-right">{percentOf(line.cost_base, line.goods_base)}</td>
                  <td className="text-right font-bold">{formatMoney(line.goods_base)}</td>
                  <td className="text-right font-bold">{formatMoney(line.cost_base)}</td>
                  <td className="text-right font-bold">{formatMoney(line.landed_base)}</td>
                </tr>
                {line.costs.map((share, shareIndex) => (
                  <tr key={share.cost_id || shareIndex}>
                    <td />
                    <td className="pl-4!">
                      {share.cost_type_label}
                      {share.description ? ` — ${share.description}` : ''}{' '}
                      <span className="italic">({share.supplier_name || share.supplier_code})</span>
                    </td>
                    <td>
                      {share.effective_method === share.allocation_method
                        ? share.allocation_method_label
                        : `${share.effective_method_label} (*)`}
                    </td>
                    <td className="text-right">{formatRatio(share.ratio)}</td>
                    <td />
                    <td className="text-right">{formatMoney(share.base_amount)}</td>
                    <td />
                  </tr>
                ))}
              </Fragment>
            ))}
            {allocation.lines.length === 0 && (
              <tr>
                <td className="text-center italic" colSpan={7}>
                  Đơn chưa có dòng hàng
                </td>
              </tr>
            )}
            <tr>
              <td className="font-bold" colSpan={3}>
                Tổng toàn đơn:
              </td>
              <td className="text-right">
                {percentOf(allocation.cost_total, allocation.goods_base_total)}
              </td>
              <td className="text-right font-bold">{formatMoney(allocation.goods_base_total)}</td>
              <td className="text-right font-bold">{formatMoney(allocation.cost_total)}</td>
              <td className="text-right font-bold">{formatMoney(allocation.landed_total)}</td>
            </tr>
          </tbody>
        </table>
        {hasFallbackAllocation && (
          <p className="mt-1 text-[10px] italic">
            (*) Cách chia đã chọn thiếu cơ sở (chưa có kg / SL / mã hàng) nên hệ thống lùi về cách
            ghi ở cột.
          </p>
        )}
      </section>

      <div className="mt-5 flex justify-around text-center text-[11.5px]">
        {SIGNATURE_TITLES.map((title) => (
          <div key={title} className={cn('flex-1')}>
            <b>{title}</b>
            <p className="text-[10.5px] italic">(Ký, họ tên)</p>
            <div className="h-16" />
          </div>
        ))}
      </div>
    </article>
  )
}

const SIGNATURE_TITLES = ['Người lập', 'Kế toán', 'Trưởng phòng/Trưởng BP']

/** Cùng khuôn với `purchase-order-print-page.tsx`, thêm khối/tiêu đề khối và dòng nhóm. */
const PRINT_STYLES = `
  .po-print-doc {
    margin: 0 auto;
    background: #fff;
    color: #000;
    font-family: Arial, Helvetica, sans-serif;
    padding: 24px 30px;
  }
  .po-print-doc--portrait { max-width: 210mm; }

  .po-print-block-title {
    font-size: 12.5px;
    font-weight: 700;
    margin: 14px 0 4px;
    color: #1a4d6b;
  }
  .po-print-table { width: 100%; border-collapse: collapse; }
  .po-print-table th,
  .po-print-table td {
    border: 1px solid #555;
    padding: 3px 5px;
    font-size: 10.5px;
    vertical-align: top;
  }
  .po-print-table th { background: #eef2f6; font-weight: 700; text-align: center; }
  .po-print-row--group td { background: #f6f8fa; }

  @media print {
    @page { size: A4 portrait; margin: 0; }
    html, body { margin: 0 !important; background: #fff !important; }
    .no-print { display: none !important; }
    .po-print-root { padding: 0 !important; background: #fff !important; min-height: 0 !important; }
    .po-print-doc {
      max-width: none !important;
      padding: 10mm 12mm !important;
      -webkit-box-decoration-break: clone;
      box-decoration-break: clone;
    }
    .po-print-block { break-inside: avoid; }
  }
`
