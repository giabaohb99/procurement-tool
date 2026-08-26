import {
  ArrowLeft,
  Layers,
  Settings2,
  SlidersHorizontal,
  X,
} from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { ApprovalNodeForm } from '../components/approval-node-form'
import { FlowCanvasXY } from '../components/flow-canvas-xy'
import { FlowSettingsPanel } from '../components/flow-settings-panel'
import { ENTITY_LABELS } from '../helpers/entity-link'
import {
  useApprovalFlow,
  useDeleteApprovalNode,
  useSaveApprovalNode,
} from '../hooks/use-approvals'
import type { ApprovalNode } from '../types/approval'

/** Bảng bên phải đang bày gì (`null` = đóng panel). */
type RightTable =
  | null
  | { loai: 'cai-dat' }
  | { loai: 'sua-buoc'; nodeId: number }
  | { loai: 'them-buoc'; sauChang: number; vaoChang?: number }

/**
 * MÀN KHAI LUỒNG DUYỆT — Canvas kéo thả React Flow toàn màn hình.
 */
export function ApprovalFlowDesignerPage() {
  const params = useParams()
  const navigate = useNavigate()
  const isCreating = !params.id || params.id === 'new'
  const flowId = isCreating ? 0 : Number(params.id)

  const { data: flow, isLoading } = useApprovalFlow(isCreating ? undefined : flowId)
  const saveNode = useSaveApprovalNode(flowId)
  const deleteNode = useDeleteApprovalNode(flowId)

  const [bangPhai, setBangPhai] = useState<RightTable>(null)
  const [entityMoi, setEntityMoi] = useState('document')

  const nodes = flow?.nodes ?? []
  const cacChang = [...new Set(nodes.map((node) => node.seq))].sort((a, b) => a - b)
  const editingNode =
    bangPhai?.loai === 'sua-buoc'
      ? (nodes.find((node) => node.id === bangPhai.nodeId) ?? null)
      : null

  /** Chèn vào sau chặng thứ `sauChang` → bước mới mang số chặng đó + 1. */
  function suggestedSeq(): number {
    if (!bangPhai || bangPhai.loai !== 'them-buoc') return cacChang.length + 1
    if (bangPhai.vaoChang) return bangPhai.vaoChang
    return Math.min(bangPhai.sauChang + 1, cacChang.length + 1)
  }

  function addStep(values: Partial<ApprovalNode>) {
    //  Chỗ đặt bước do BACKEND lo (`flow_service.them_buoc`): chèn giữa thì nó
    //  tự đẩy các chặng sau xuống, thêm nhánh thì tự đánh lại `branch_key`.
    //  Trước đây màn này chèn thẳng rồi mới gọi sắp lại thứ tự — mà chính lượt
    //  chèn đó đâm vào `UNIQUE(flow_id, seq, branch_key)` và trả 500, bước mới
    //  mất luôn.
    const isQuick = bangPhai?.loai === 'them-buoc' && !!bangPhai.vaoChang

    saveNode.mutate(
      { values, asBranch: isQuick },
      { onSuccess: (moi) => setBangPhai({ loai: 'sua-buoc', nodeId: moi.id }) },
    )
  }

  // Màn hình tạo mới luồng
  if (isCreating) {
    return (
      <PageContainer className="py-8">
        <div className="mx-auto max-w-xl space-y-4">
          <div className="flex items-center gap-3 pb-2">
            <Button
              variant="outline"
              size="icon"
              className="size-9 rounded-xl shadow-2xs"
              onClick={() => navigate(appRoutes.approval.flows)}
            >
              <ArrowLeft className="size-4" />
            </Button>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-foreground">Tạo luồng duyệt mới</h1>
              <p className="text-xs text-muted-foreground">Khai báo thông tin chung trước; vẽ các bước ngay sau khi lưu.</p>
            </div>
          </div>

          <FlowSettingsPanel
            defaultEntity={entityMoi}
            onEntityChange={setEntityMoi}
            onSaved={(moi) => navigate(appRoutes.approval.flowDetail(moi.id), { replace: true })}
            onCancel={() => navigate(appRoutes.approval.flows)}
          />
        </div>
      </PageContainer>
    )
  }

  if (isLoading || !flow) {
    return (
      <PageContainer fill className="flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="size-8 animate-spin rounded-full border-3 border-primary border-t-transparent" />
          <p className="text-sm font-medium text-muted-foreground">Đang tải sơ đồ luồng duyệt…</p>
        </div>
      </PageContainer>
    )
  }

  return (
    <div className="relative flex h-[calc(100vh-3.5rem)] flex-col overflow-hidden bg-background">
      {/* Top Navigation Bar */}
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-border/80 bg-card/95 px-4 backdrop-blur-md z-10">
        <div className="flex items-center gap-3 min-w-0">
          <Button
            variant="ghost"
            size="icon"
            className="size-8 rounded-lg text-muted-foreground hover:text-foreground"
            onClick={() => navigate(appRoutes.approval.flows)}
            title="Về danh sách luồng"
          >
            <ArrowLeft className="size-4" />
          </Button>

          <div className="h-4 w-px bg-border/80" />

          <div className="flex items-center gap-2 min-w-0">
            <h2 className="truncate text-sm font-bold text-foreground">
              {flow.name || 'Luồng duyệt'}
            </h2>
            <Badge variant="secondary" className="gap-1 rounded-md px-2 py-0.5 text-xs font-semibold">
              <Layers className="size-3 text-primary" />
              {ENTITY_LABELS[flow.entity] ?? flow.entity}
            </Badge>
            <Badge variant="outline" className="rounded-md px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground">
              v{flow.version_no}
            </Badge>
            <span className="text-xs text-muted-foreground hidden sm:inline">
              · {nodes.length} bước duyệt
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {!flow.is_active && (
            <Badge variant="destructive" className="rounded-md text-xs">
              Ngừng dùng
            </Badge>
          )}

          <Button
            variant={bangPhai?.loai === 'cai-dat' ? 'default' : 'outline'}
            size="sm"
            onClick={() =>
              setBangPhai((prev) => (prev?.loai === 'cai-dat' ? null : { loai: 'cai-dat' }))
            }
            className="h-8.5 gap-1.5 rounded-xl font-medium shadow-2xs"
          >
            <Settings2 className="size-3.5" />
            Cài đặt luồng
          </Button>
        </div>
      </header>

      {/* Main Canvas Area */}
      <div className="relative min-h-0 flex-1 overflow-hidden">
        <FlowCanvasXY
          nodes={nodes}
          selectedNode={editingNode?.id ?? null}
          onPick={(nodeId) => setBangPhai({ loai: 'sua-buoc', nodeId })}
          onDeselect={() => {
            if (bangPhai?.loai === 'sua-buoc') setBangPhai(null)
          }}
          onDelete={(nodeId) => {
            deleteNode.mutate(nodeId)
            if (bangPhai?.loai === 'sua-buoc' && bangPhai.nodeId === nodeId) {
              setBangPhai(null)
            }
          }}
          onDuplicate={(node) => {
            const { id: _bo, flow_id: _bo2, ...remainder } = node
            //  Bản sao nằm NGAY SAU bản gốc: gửi lại đúng `seq` cũ thì backend
            //  hiểu là chèn chặng mới tại đó và đẩy bản gốc xuống dưới bản sao.
            saveNode.mutate({
              values: { ...remainder, seq: node.seq + 1, name: `${node.name} (bản sao)` },
            })
          }}
          onAdd={(sauChang, vaoChang) =>
            setBangPhai({ loai: 'them-buoc', sauChang, vaoChang })
          }
        />

        {/* Slide-over Right Inspector Panel */}
        {bangPhai !== null && (
          <aside className="absolute right-4 top-4 bottom-4 z-20 w-[420px] max-w-[calc(100vw-2rem)] overflow-hidden rounded-2xl border border-border/80 bg-card/95 shadow-2xl backdrop-blur-xl transition-all duration-300 animate-in fade-in slide-in-from-right-4">
            {bangPhai.loai === 'cai-dat' ? (
              <FlowSettingsPanel
                flow={flow}
                onSaved={() => setBangPhai(null)}
                onCancel={() => setBangPhai(null)}
              />
            ) : (
              <Card className="flex h-full flex-col overflow-hidden rounded-2xl border-none shadow-none bg-transparent">
                <div className="flex items-center justify-between border-b border-border/60 bg-muted/30 px-5 py-4">
                  <div className="flex items-center gap-2">
                    <div className="flex size-7 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <SlidersHorizontal className="size-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-foreground">
                        {editingNode ? `Thuộc tính: ${editingNode.name || `Bước #${editingNode.seq}`}` : 'Thêm bước duyệt mới'}
                      </h3>
                      <p className="text-xs text-muted-foreground">
                        {editingNode ? 'Cấu hình người duyệt & chế độ phê duyệt' : `Chèn bước vào chặng #${suggestedSeq()}`}
                      </p>
                    </div>
                  </div>

                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => setBangPhai(null)}
                    className="size-7 rounded-lg text-muted-foreground hover:text-foreground"
                  >
                    <X className="size-4" />
                  </Button>
                </div>

                <div className="flex-1 overflow-y-auto p-5">
                  <ApprovalNodeForm
                    key={editingNode?.id ?? `moi-${suggestedSeq()}`}
                    node={editingNode ?? undefined}
                    entity={flow.entity}
                    suggestedSeq={suggestedSeq()}
                    isPending={saveNode.isPending}
                    onCancel={() => setBangPhai(null)}
                    onSubmit={(values) => {
                      if (editingNode) {
                        saveNode.mutate({ id: editingNode.id, values }, { onSuccess: () => setBangPhai(null) })
                      } else {
                        addStep(values)
                      }
                    }}
                  />
                </div>
              </Card>
            )}
          </aside>
        )}
      </div>
    </div>
  )
}
