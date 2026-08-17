import { AlertTriangle, ArrowLeft, GitBranch, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Switch } from '@/shared/ui/switch'
import { Textarea } from '@/shared/ui/textarea'
import { ApprovalNodeForm } from '../components/approval-node-form'
import { ENTITY_LABELS } from '../helpers/entity-link'
import {
  useApprovalFlow,
  useDeleteApprovalNode,
  useSaveApprovalFlow,
  useSaveApprovalNode,
} from '../hooks/use-approvals'
import { NODE_KIND, type ApprovalFlow, type ApprovalNode } from '../types/approval'

/**
 * Khai một LUỒNG DUYỆT và các bước của nó — bài nghiệm thu số 1 của phase 3:
 * *"khai luồng 4 bước bằng giao diện, không sửa dòng mã nào, không deploy lại"*.
 *
 * Các bước gom theo **chặng**: nhiều bước cùng số chặng là các nhánh song song,
 * lúc chạy chỉ một nhánh được chọn. Màn hình phải nói ra điều đó, không thì
 * người khai tưởng mình vừa thêm hai bước nối tiếp.
 */
export function ApprovalFlowDetailPage() {
  const params = useParams()
  const navigate = useNavigate()
  const laTaoMoi = params.id === 'new'
  const flowId = laTaoMoi ? 0 : Number(params.id)

  const { data: flow, isLoading } = useApprovalFlow(laTaoMoi ? undefined : flowId)
  const save = useSaveApprovalFlow()

  if (!laTaoMoi && isLoading) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Đang tải…</p>
      </PageContainer>
    )
  }

  return (
    <PageContainer className="space-y-4">
      <PageHeader
        title={laTaoMoi ? 'Tạo luồng duyệt' : flow?.name || 'Luồng duyệt'}
        description={
          laTaoMoi
            ? 'Khai xong phần chung rồi mới thêm được các bước.'
            : `${ENTITY_LABELS[flow?.entity ?? ''] ?? flow?.entity} · bản ${flow?.version_no}`
        }
        leading={
          <Button
            variant="outline"
            size="icon"
            title="Về danh sách"
            aria-label="Về danh sách"
            onClick={() => navigate(appRoutes.approval.flows)}
          >
            <ArrowLeft className="size-4" />
          </Button>
        }
      />

      <ThongTinChung
        flow={flow}
        isPending={save.isPending}
        onSubmit={(values) =>
          save.mutate(
            { id: laTaoMoi ? undefined : flowId, values },
            {
              onSuccess: (moi) =>
                laTaoMoi && navigate(appRoutes.approval.flowDetail(moi.id), { replace: true }),
            },
          )
        }
      />

      {!laTaoMoi && flow && <CacBuoc flow={flow} />}
    </PageContainer>
  )
}

interface ThongTinChungProps {
  flow?: ApprovalFlow
  isPending: boolean
  onSubmit: (values: Partial<ApprovalFlow>) => void
}

function ThongTinChung({ flow, isPending, onSubmit }: ThongTinChungProps) {
  const [form, setForm] = useState<Partial<ApprovalFlow>>(() => ({
    entity: flow?.entity ?? 'document',
    code: flow?.code ?? '',
    name: flow?.name ?? '',
    description: flow?.description ?? '',
    is_active: flow?.is_active ?? true,
    priority: flow?.priority ?? 0,
    condition: flow?.condition ?? '',
    company_id: flow?.company_id ?? null,
  }))

  function dat<K extends keyof ApprovalFlow>(khoa: K, gia_tri: ApprovalFlow[K]) {
    setForm((truoc) => ({ ...truoc, [khoa]: gia_tri }))
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Thông tin chung</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Loại chứng từ</Label>
            <Select
              value={form.entity ?? 'document'}
              onValueChange={(value) => dat('entity', value)}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(ENTITY_LABELS).map(([ma, nhan]) => (
                  <SelectItem key={ma} value={ma}>
                    {nhan}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Tên luồng</Label>
            <Input
              placeholder="VD: Duyệt quy chế nội bộ"
              value={form.name ?? ''}
              onChange={(event) => dat('name', event.target.value)}
            />
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Mã luồng</Label>
            <Input
              value={form.code ?? ''}
              onChange={(event) => dat('code', event.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>Độ ưu tiên</Label>
            <Input
              type="number"
              value={form.priority ?? 0}
              onChange={(event) => dat('priority', Number(event.target.value))}
            />
            <p className="text-xs text-muted-foreground">
              Số lớn xét trước. Luồng không khai điều kiện là luồng mặc định.
            </p>
          </div>
        </div>

        <div className="space-y-2">
          <Label>Áp cho phiếu nào</Label>
          <Textarea
            rows={2}
            className="font-mono text-xs"
            placeholder='Để trống = mọi phiếu. VD: [{"field": "doc_type_id", "op": "eq", "value": 3}]'
            value={form.condition ?? ''}
            onChange={(event) => dat('condition', event.target.value)}
          />
        </div>

        <div className="flex items-center gap-3">
          <Switch
            id="flow-active"
            checked={form.is_active ?? true}
            onCheckedChange={(bat) => dat('is_active', bat)}
          />
          <Label htmlFor="flow-active">Đang dùng</Label>
        </div>

        <div className="flex justify-end">
          <Button type="button" disabled={isPending} onClick={() => onSubmit(form)}>
            Lưu luồng
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function CacBuoc({ flow }: { flow: ApprovalFlow }) {
  const [dangThem, setDangThem] = useState(false)
  const [dangSua, setDangSua] = useState<number | null>(null)
  const saveNode = useSaveApprovalNode(flow.id)
  const deleteNode = useDeleteApprovalNode(flow.id)

  const nodes = flow.nodes ?? []
  const cacChang = [...new Set(nodes.map((node) => node.seq))].sort((a, b) => a - b)

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <GitBranch className="size-4 text-muted-foreground" />
          Các bước ({nodes.length})
        </CardTitle>
        {!dangThem && (
          <Button type="button" variant="outline" size="sm" onClick={() => setDangThem(true)}>
            <Plus className="size-4" />
            Thêm bước
          </Button>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {nodes.length === 0 && !dangThem && (
          <p className="text-sm text-muted-foreground">
            Chưa có bước nào. Luồng không có bước thì trình duyệt sẽ báo lỗi.
          </p>
        )}

        {cacChang.map((seq) => {
          const cungChang = nodes.filter((node) => node.seq === seq)
          const coReNhanh = cungChang.length > 1
          const thieuMacDinh = coReNhanh && !cungChang.some((node) => node.is_default_branch)

          return (
            <div key={seq} className="space-y-2">
              <p className="flex items-center gap-2 text-sm font-medium">
                Chặng {seq}
                {coReNhanh && (
                  <Badge variant="outline">{cungChang.length} nhánh — chỉ một nhánh chạy</Badge>
                )}
              </p>

              {/*  Cảnh báo tại chỗ, không đợi tới lúc phiếu chạy mới kẹt. */}
              {thieuMacDinh && (
                <p className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                  <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
                  <span>
                    Chặng này rẽ nhánh nhưng <b>chưa có nhánh mặc định</b>. Phiếu không
                    khớp điều kiện nào sẽ bị kẹt và biến mất khỏi mọi danh sách.
                  </span>
                </p>
              )}

              <ul className="divide-y rounded-md border">
                {cungChang.map((node) =>
                  dangSua === node.id ? (
                    <li key={node.id} className="p-3">
                      <ApprovalNodeForm
                        node={node}
                        seqGoiY={seq}
                        isPending={saveNode.isPending}
                        onCancel={() => setDangSua(null)}
                        onSubmit={(values) =>
                          saveNode.mutate(
                            { id: node.id, values },
                            { onSuccess: () => setDangSua(null) },
                          )
                        }
                      />
                    </li>
                  ) : (
                    <DongBuoc
                      key={node.id}
                      node={node}
                      onSua={() => setDangSua(node.id)}
                      onXoa={() => deleteNode.mutate(node.id)}
                    />
                  ),
                )}
              </ul>
            </div>
          )
        })}

        {dangThem && (
          <ApprovalNodeForm
            seqGoiY={(cacChang.at(-1) ?? 0) + 1}
            isPending={saveNode.isPending}
            onCancel={() => setDangThem(false)}
            onSubmit={(values) =>
              saveNode.mutate({ values }, { onSuccess: () => setDangThem(false) })
            }
          />
        )}
      </CardContent>
    </Card>
  )
}

interface DongBuocProps {
  node: ApprovalNode
  onSua: () => void
  onXoa: () => void
}

function DongBuoc({ node, onSua, onXoa }: DongBuocProps) {
  return (
    <li className="flex items-center gap-3 p-3">
      <button
        type="button"
        onClick={onSua}
        className="min-w-0 flex-1 text-left hover:underline"
      >
        <p className="text-sm font-medium">
          {node.name || `Bước ${node.seq}`}
          {node.node_kind === NODE_KIND.cc && (
            <Badge variant="outline" className="ml-2 font-normal">
              {node.node_kind_label}
            </Badge>
          )}
          {node.is_default_branch && (
            <Badge variant="outline" className="ml-2 font-normal">
              Nhánh mặc định
            </Badge>
          )}
        </p>
        <p className="text-xs text-muted-foreground">
          {node.approver_kind_label}
          {node.approver_names && ` · ${node.approver_names}`}
          {` · ${node.multi_mode_label}`}
          {node.sla_hours > 0 && ` · hạn ${node.sla_hours} giờ`}
        </p>
        {node.condition && (
          <p className="font-mono text-xs text-muted-foreground">Khi: {node.condition}</p>
        )}
      </button>

      <ConfirmIconButton
        icon={Trash2}
        title="Xóa bước"
        destructive
        confirmTitle="Xóa bước này?"
        confirmDescription="Phiếu ĐANG chạy không bị ảnh hưởng — chúng giữ bản chụp luồng riêng."
        confirmLabel="Xóa"
        onConfirm={onXoa}
      />
    </li>
  )
}
