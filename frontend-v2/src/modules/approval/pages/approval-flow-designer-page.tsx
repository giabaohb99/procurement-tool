import { ArrowLeft, Settings2, SlidersHorizontal } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { ApprovalNodeForm } from '../components/approval-node-form'
import { FlowCanvas } from '../components/flow-canvas'
import { FlowEntitySidebar } from '../components/flow-entity-sidebar'
import { FlowSettingsPanel } from '../components/flow-settings-panel'
import { ENTITY_LABELS } from '../helpers/entity-link'
import {
  useApprovalFlow,
  useDeleteApprovalNode,
  useReorderApprovalNodes,
  useSaveApprovalNode,
} from '../hooks/use-approvals'
import type { ApprovalNode } from '../types/approval'

/** Bảng bên phải đang bày gì. */
type BangPhai =
  | { loai: 'cai-dat' }
  | { loai: 'sua-buoc'; nodeId: number }
  | { loai: 'them-buoc'; sauChang: number; vaoChang?: number }

/**
 * MÀN KHAI LUỒNG DUYỆT — ba cột, dựng theo lối Lark Approval.
 *
 * Trái: loại chứng từ → các luồng của loại đó. Giữa: **sơ đồ luồng**, kéo thả
 * đổi thứ tự, dấu + giữa hai chặng để chèn bước. Phải: thuộc tính của bước đang
 * chọn, hoặc cài đặt chung của luồng khi chưa chọn bước nào.
 *
 * Bố cục này thay cho bản danh sách form trước đó, vì hai thứ một danh sách
 * không nói ra được: **phiếu đi theo chiều nào**, và **chặng nào rẽ nhánh**.
 * Người khai luồng phải thấy hình dạng của luồng chứ không phải đọc một bảng rồi
 * tự vẽ trong đầu.
 */
export function ApprovalFlowDesignerPage() {
  const params = useParams()
  const navigate = useNavigate()
  const laTaoMoi = params.id === 'new'
  const flowId = laTaoMoi ? 0 : Number(params.id)

  const { data: flow, isLoading } = useApprovalFlow(laTaoMoi ? undefined : flowId)
  const saveNode = useSaveApprovalNode(flowId)
  const deleteNode = useDeleteApprovalNode(flowId)
  const reorder = useReorderApprovalNodes(flowId)

  const [bangPhai, setBangPhai] = useState<BangPhai>({ loai: 'cai-dat' })
  const [entityMoi, setEntityMoi] = useState('document')

  const nodes = flow?.nodes ?? []
  const cacChang = [...new Set(nodes.map((node) => node.seq))].sort((a, b) => a - b)
  const nodeDangSua =
    bangPhai.loai === 'sua-buoc'
      ? (nodes.find((node) => node.id === bangPhai.nodeId) ?? null)
      : null

  /** Chèn vào sau chặng thứ `sauChang` → bước mới mang số chặng đó + 1. */
  function seqGoiY(): number {
    if (bangPhai.loai !== 'them-buoc') return cacChang.length + 1
    if (bangPhai.vaoChang) return bangPhai.vaoChang
    return Math.min(bangPhai.sauChang + 1, cacChang.length + 1)
  }

  function themBuoc(values: Partial<ApprovalNode>) {
    saveNode.mutate(
      { values },
      {
        onSuccess: (moi) => {
          //  Chèn vào GIỮA luồng thì các chặng phía sau phải lùi xuống một bậc.
          //  Không đẩy thì bước mới nằm chung chặng với bước đang có và biến
          //  thành một nhánh song song — khác hẳn ý người dùng vừa bấm.
          if (bangPhai.loai === 'them-buoc' && !bangPhai.vaoChang) {
            const truoc = cacChang.slice(0, bangPhai.sauChang)
            const sau = cacChang.slice(bangPhai.sauChang)
            const thuTu = [
              ...truoc.map((seq) => nodes.filter((n) => n.seq === seq).map((n) => n.id)),
              [moi.id],
              ...sau.map((seq) => nodes.filter((n) => n.seq === seq).map((n) => n.id)),
            ]
            reorder.mutate(thuTu)
          }
          setBangPhai({ loai: 'sua-buoc', nodeId: moi.id })
        },
      },
    )
  }

  if (laTaoMoi) {
    return (
      <PageContainer className="space-y-4">
        <PageHeader
          title="Tạo luồng duyệt"
          description="Khai phần chung trước; vẽ các bước ngay sau khi lưu."
          leading={<NutQuayLai onClick={() => navigate(appRoutes.approval.flows)} />}
        />
        <div className="max-w-2xl">
          <FlowSettingsPanel
            entityMacDinh={entityMoi}
            onDoiEntity={setEntityMoi}
            onSaved={(moi) => navigate(appRoutes.approval.flowDetail(moi.id), { replace: true })}
          />
        </div>
      </PageContainer>
    )
  }

  if (isLoading || !flow) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Đang tải…</p>
      </PageContainer>
    )
  }

  return (
    <PageContainer fill className="flex flex-col">
      <PageHeader
        title={flow.name || 'Luồng duyệt'}
        description={`${ENTITY_LABELS[flow.entity] ?? flow.entity} · bản ${flow.version_no} · ${nodes.length} bước`}
        leading={<NutQuayLai onClick={() => navigate(appRoutes.approval.flows)} />}
        actions={
          <>
            {!flow.is_active && <Badge variant="outline">Ngừng dùng</Badge>}
            <Button
              variant="outline"
              onClick={() => setBangPhai({ loai: 'cai-dat' })}
            >
              <Settings2 className="size-4" />
              Cài đặt luồng
            </Button>
          </>
        }
      />

      <div className="flex min-h-0 flex-1 gap-4">
        <FlowEntitySidebar
          flowId={flow.id}
          onTaoLuong={(entity) => {
            setEntityMoi(entity)
            navigate(appRoutes.approval.flowNew)
          }}
        />

        {/*  Sơ đồ nằm giữa và CUỘN RIÊNG: luồng mười bước dài hơn màn hình, mà
             bảng thuộc tính bên phải phải luôn nhìn thấy được trong lúc sửa. */}
        <Card className="min-w-0 flex-1 overflow-y-auto p-4">
          {nodes.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
              <p className="text-sm text-muted-foreground">
                Luồng chưa có bước nào. Luồng rỗng thì trình duyệt sẽ báo lỗi.
              </p>
              <Button onClick={() => setBangPhai({ loai: 'them-buoc', sauChang: 0 })}>
                Thêm bước đầu tiên
              </Button>
            </div>
          ) : (
            <FlowCanvas
              nodes={nodes}
              nodeDangChon={nodeDangSua?.id ?? null}
              onChon={(nodeId) => setBangPhai({ loai: 'sua-buoc', nodeId })}
              onXoa={(nodeId) => {
                deleteNode.mutate(nodeId)
                setBangPhai({ loai: 'cai-dat' })
              }}
              onNhanBan={(node) => {
                const { id: _bo, flow_id: _bo2, ...phanConLai } = node
                saveNode.mutate({ values: { ...phanConLai, name: `${node.name} (bản sao)` } })
              }}
              onThem={(sauChang) => setBangPhai({ loai: 'them-buoc', sauChang })}
              onThemNhanh={(chang) =>
                setBangPhai({ loai: 'them-buoc', sauChang: chang - 1, vaoChang: chang })
              }
              onDoiThuTu={(stages) => reorder.mutate(stages)}
            />
          )}
        </Card>

        <aside className="w-96 shrink-0 overflow-y-auto">
          {bangPhai.loai === 'cai-dat' ? (
            <FlowSettingsPanel flow={flow} />
          ) : (
            <Card className="p-4">
              <p className="mb-3 flex items-center gap-2 text-sm font-medium">
                <SlidersHorizontal className="size-4 text-muted-foreground" />
                {nodeDangSua ? 'Thuộc tính bước' : 'Bước mới'}
              </p>
              <ApprovalNodeForm
                key={nodeDangSua?.id ?? `moi-${seqGoiY()}`}
                node={nodeDangSua ?? undefined}
                seqGoiY={seqGoiY()}
                isPending={saveNode.isPending}
                onCancel={() => setBangPhai({ loai: 'cai-dat' })}
                onSubmit={(values) =>
                  nodeDangSua
                    ? saveNode.mutate({ id: nodeDangSua.id, values })
                    : themBuoc(values)
                }
              />
            </Card>
          )}
        </aside>
      </div>
    </PageContainer>
  )
}

function NutQuayLai({ onClick }: { onClick: () => void }) {
  return (
    <Button
      variant="outline"
      size="icon"
      title="Về danh sách luồng"
      aria-label="Về danh sách luồng"
      onClick={onClick}
    >
      <ArrowLeft className="size-4" />
    </Button>
  )
}
