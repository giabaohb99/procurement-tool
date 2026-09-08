import { ArrowLeft, Printer, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { ErrorState } from '@/shared/ui/error-state'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { PurchaseOrderPrintGoodsForm } from '../components/purchase-order-print-goods-form'
import { PurchaseOrderPrintOrderForm } from '../components/purchase-order-print-order-form'
import { usePurchaseOrderPrintData } from '../hooks/use-purchase-order'

/** Hai mẫu in của ĐMH — bản v1 tách thành hai route, ở đây gộp một trang có công tắc. */
const PRINT_MODES = [
  { value: 'order', label: 'Đơn đặt hàng (gửi NCC)' },
  { value: 'goods', label: 'Đơn mua hàng (nội bộ)' },
] as const

type PrintMode = (typeof PRINT_MODES)[number]['value']

/** Bản gửi ra ngoài thường phải ký tươi + đóng dấu, nên phải bỏ được ảnh chữ ký số. */
const SIGNATURE_MODES = [
  { value: true, label: 'Có chữ ký' },
  { value: false, label: 'Không chữ ký' },
] as const

/**
 * Bản in Đơn mua hàng. Route nằm NGOÀI `ModuleLayout` để trang in không mang
 * theo menu và thanh tiêu đề.
 *
 * Khổ giấy đổi theo mẫu: Đơn đặt hàng in NGANG (13 cột), Đơn mua hàng in DỌC.
 */
export function PurchaseOrderPrintPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const purchaseOrderId = Number(id)
  const { data, isLoading, isError } = usePurchaseOrderPrintData(purchaseOrderId)
  const [mode, setMode] = useState<PrintMode>('order')
  const [showSignature, setShowSignature] = useState(true)

  useEffect(() => {
    if (!data?.code) return
    const previousTitle = document.title
    document.title = `${data.code} - Đơn mua hàng`
    return () => {
      document.title = previousTitle
    }
  }, [data?.code])

  if (isLoading) {
    return (
      <main className="min-h-[100dvh] bg-slate-200 p-5">
        <Skeleton className="mx-auto mb-3 h-10 max-w-[280mm]" />
        <Skeleton className="mx-auto h-[200mm] max-w-[280mm] bg-white" />
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
    <main
      className={cn(
        'po-print-root min-h-[100dvh] bg-slate-200 p-6 text-slate-950',
        mode === 'order' ? 'po-print-root--landscape' : 'po-print-root--portrait',
      )}
    >
      <style>{PRINT_STYLES}</style>

      <div className="no-print mx-auto mb-3 flex max-w-[280mm] flex-wrap items-center gap-2">
        <Button onClick={() => window.print()}>
          <Printer />
          In / Lưu PDF
        </Button>
        <Button variant="outline" onClick={() => window.close()}>
          <X />
          Đóng
        </Button>

        <div className="ml-auto flex flex-wrap items-center gap-2">
          <div className="flex gap-1 rounded-lg border bg-white p-1">
            {SIGNATURE_MODES.map((option) => (
              <Button
                key={option.label}
                size="sm"
                variant={showSignature === option.value ? 'default' : 'ghost'}
                onClick={() => setShowSignature(option.value)}
              >
                {option.label}
              </Button>
            ))}
          </div>

          <div className="flex gap-1 rounded-lg border bg-white p-1">
            {PRINT_MODES.map((option) => (
              <Button
                key={option.value}
                size="sm"
                variant={mode === option.value ? 'default' : 'ghost'}
                onClick={() => setMode(option.value)}
              >
                {option.label}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {mode === 'order' ? (
        <PurchaseOrderPrintOrderForm data={data} showSignature={showSignature} />
      ) : (
        <PurchaseOrderPrintGoodsForm data={data} showSignature={showSignature} />
      )}
    </main>
  )
}

/**
 * `@page { margin: 0 }`: trình duyệt vẽ ngày giờ / đường dẫn / số trang vào dải
 * lề của khổ giấy — bỏ lề đi thì không còn chỗ cho mấy dòng đó. Lề thật của
 * chứng từ chuyển vào padding của `.po-print-doc`.
 */
const PRINT_STYLES = `
  .po-print-doc {
    margin: 0 auto;
    background: #fff;
    color: #000;
    font-family: Arial, Helvetica, sans-serif;
    padding: 24px 28px;
  }
  .po-print-doc--landscape { max-width: 280mm; }
  .po-print-doc--portrait { max-width: 210mm; }

  .po-print-table { width: 100%; border-collapse: collapse; }
  .po-print-table th,
  .po-print-table td {
    border: 1px solid #555;
    padding: 4px 6px;
    font-size: 11px;
    vertical-align: top;
  }
  .po-print-table th { background: #eef2f6; font-weight: 700; text-align: center; }

  @media print {
    .po-print-root--landscape { --po-page: A4 landscape; }
    .po-print-root--portrait { --po-page: A4 portrait; }
    @page { size: var(--po-page, A4 portrait); margin: 0; }
    html, body { margin: 0 !important; background: #fff !important; }
    .no-print { display: none !important; }
    .po-print-root { padding: 0 !important; background: #fff !important; min-height: 0 !important; }
    /* box-decoration-break: clone -> đơn nhiều dòng tràn sang trang 2 thì mỗi
       mảnh vẫn đủ lề, không chạy sát mép giấy. */
    .po-print-doc {
      max-width: none !important;
      padding: 8mm 12mm !important;
      -webkit-box-decoration-break: clone;
      box-decoration-break: clone;
    }
  }
`
