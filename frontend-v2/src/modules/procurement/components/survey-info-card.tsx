import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue as ReadOnlyBox } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import { SearchSelect } from '@/shared/ui/search-select'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import type { SurveyRequest } from '../types/purchase-document'
import type { SurveyDetail } from '../types/survey-detail'
import { PurchaseRequestProductPicker } from './purchase-request-product-picker'

interface SurveyInfoCardProps {
  data: SurveyDetail
  editable: boolean
  surveyRequests: SurveyRequest[]
  itemGroups: string[]
  units: string[]
  onChange: (changes: Partial<SurveyDetail>) => void
}

function InfoField({
  label,
  full,
  required,
  children,
}: {
  label: string
  full?: boolean
  /** Ô bắt buộc trước khi GỬI DUYỆT — luật nằm ở `validateSurveySubmit`. */
  required?: boolean
  children: React.ReactNode
}) {
  return (
    <div className={cn('space-y-1.5', full && 'md:col-span-2')}>
      <Label>
        {label}
        {required && <RequiredMark />}
      </Label>
      {children}
    </div>
  )
}

/** Giữ chữ ký `value=` sẵn có của thẻ này; hộp hiển thị dùng chung ở `shared/ui`. */
function ReadOnlyValue({ value, multiline }: { value: string; multiline?: boolean }) {
  return <ReadOnlyBox multiline={multiline}>{value}</ReadOnlyBox>
}

/**
 * Thẻ "Thông tin tiếp nhận" của phiếu khảo sát — giữ nguyên thứ tự và nhãn của
 * bản v1 (`frontend/src/pages/SurveyDetail.tsx`) để người dùng khỏi học lại.
 *
 * Khối MÃ HÀNG chỉ hiện khi tick "Có mã hàng trong danh mục": phần lớn phiếu
 * khảo sát là hàng CHƯA có mã (đang đi tìm NCC), bắt khai mã là không khai được.
 */
export function SurveyInfoCard({
  data,
  editable,
  surveyRequests,
  itemGroups,
  units,
  onChange,
}: SurveyInfoCardProps) {
  function pickSurveyRequest(code: string) {
    const request = surveyRequests.find((item) => item.code === code)
    // Chép mục đích của YCBG sang "Nội dung chính" — hai ô này gần như luôn
    // giống nhau, gõ lại tay chỉ tổ lệch chữ giữa hai phiếu.
    onChange({
      sr_code: code,
      survey_request_id: request?.id ?? 0,
      main_content: request?.purpose || data.main_content,
    })
  }

  return (
    <Card className="gap-4 py-4">
      <CardHeader className="flex min-h-9 flex-row items-center gap-3 border-b px-4 pb-3!">
        <CardTitle className="text-base text-navy dark:text-foreground">
          Thông tin tiếp nhận
        </CardTitle>
      </CardHeader>

      <CardContent className="grid gap-x-4 gap-y-3 px-4 md:grid-cols-2">
        <InfoField label="Mã phiếu">
          <ReadOnlyValue value={data.code || '— (tự sinh khi tạo)'} />
        </InfoField>

        <InfoField label="Mã YCBG">
          {editable ? (
            <SearchSelect
              value={data.sr_code}
              placeholder="-- Chọn yêu cầu báo giá --"
              searchPlaceholder="Tìm theo mã YCBG…"
              clearable
              options={surveyRequests.map((request) => ({
                value: request.code,
                label: request.purpose ? `${request.code} — ${request.purpose}` : request.code,
              }))}
              onChange={pickSurveyRequest}
            />
          ) : data.survey_request_id ? (
            <p className="min-h-9 px-3 py-2 text-sm">
              <Link
                className="text-primary hover:underline"
                to={appRoutes.procurement.surveyRequestDetail(data.survey_request_id)}
              >
                {data.sr_code || 'Mở phiếu YCBG'}
              </Link>
            </p>
          ) : (
            <ReadOnlyValue value={data.sr_code} />
          )}
        </InfoField>

        <InfoField label="Nội dung chính" full>
          {editable ? (
            <Textarea
              rows={1}
              value={data.main_content}
              placeholder="Nội dung cần khảo sát"
              onChange={(event) => onChange({ main_content: event.target.value })}
            />
          ) : (
            <ReadOnlyValue value={data.main_content} multiline />
          )}
        </InfoField>

        <InfoField label="Ngày tiếp nhận">
          {editable ? (
            <DatePicker
              value={data.received_date}
              clearable
              onChange={(value) => onChange({ received_date: value })}
            />
          ) : (
            <ReadOnlyValue value={formatDate(data.received_date)} />
          )}
        </InfoField>

        <InfoField label="Ngày dự kiến trả kết quả">
          {editable ? (
            <DatePicker
              value={data.result_due_date}
              clearable
              onChange={(value) => onChange({ result_due_date: value })}
            />
          ) : (
            <ReadOnlyValue value={formatDate(data.result_due_date)} />
          )}
        </InfoField>

        <InfoField label="Nhóm hàng" required>
          {editable ? (
            <SearchSelect
              value={data.item_group}
              placeholder="-- Phân loại --"
              searchPlaceholder="Tìm nhóm hàng…"
              clearable
              options={itemGroups.map((group) => ({ value: group, label: group }))}
              onChange={(value) => onChange({ item_group: value })}
            />
          ) : (
            <ReadOnlyValue value={data.item_group} />
          )}
        </InfoField>

        {/* NSPT do backend gán theo người tạo phiếu — form không cho đổi. */}
        <InfoField label="NSPT phụ trách">
          <ReadOnlyValue value={data.nspt} />
        </InfoField>

        <InfoField label="Chi tiết yêu cầu" full required={!data.has_product_code}>
          {editable ? (
            <Textarea
              value={data.requirement_detail}
              placeholder="Mô tả yêu cầu khi hàng chưa có mã trong danh mục"
              onChange={(event) => onChange({ requirement_detail: event.target.value })}
            />
          ) : (
            <ReadOnlyValue value={data.requirement_detail} multiline />
          )}
        </InfoField>

        <div className="md:col-span-2">
          <label className="flex w-fit items-center gap-2 text-sm">
            <Checkbox
              checked={data.has_product_code}
              disabled={!editable}
              onCheckedChange={(next) => onChange({ has_product_code: next === true })}
            />
            Hàng đã có mã trong danh mục
          </label>
        </div>

        {data.has_product_code && (
          <>
            <InfoField label="Mã hàng" required>
              {editable ? (
                <PurchaseRequestProductPicker
                  code={data.item_code}
                  name={data.item_name}
                  onPick={(product) =>
                    onChange({
                      item_code: product?.code ?? '',
                      item_name: product?.name ?? '',
                      uom: product?.unit || data.uom,
                      item_group: product?.item_group || data.item_group,
                    })
                  }
                />
              ) : (
                <ReadOnlyValue value={data.item_code} />
              )}
            </InfoField>

            <InfoField label="Tên hàng">
              <ReadOnlyValue value={data.item_name} />
            </InfoField>

            <InfoField label="Số lượng yêu cầu" required>
              {editable ? (
                <Input
                  type="number"
                  inputMode="decimal"
                  min={0}
                  step="any"
                  value={String(data.request_qty ?? 0)}
                  onChange={(event) => onChange({ request_qty: Number(event.target.value) || 0 })}
                />
              ) : (
                <ReadOnlyValue value={formatQuantity(data.request_qty ?? 0)} />
              )}
            </InfoField>

            <InfoField label="ĐVT" required>
              {editable ? (
                <SearchSelect
                  value={data.uom}
                  placeholder="-- ĐVT --"
                  searchPlaceholder="Tìm đơn vị tính…"
                  clearable
                  options={units.map((unit) => ({ value: unit, label: unit }))}
                  onChange={(value) => onChange({ uom: value })}
                />
              ) : (
                <ReadOnlyValue value={data.uom} />
              )}
            </InfoField>

            <InfoField label="Đơn giá đề xuất" required>
              {editable ? (
                <Input
                  type="number"
                  inputMode="decimal"
                  min={0}
                  step="any"
                  value={String(data.proposed_rate ?? 0)}
                  onChange={(event) =>
                    onChange({ proposed_rate: Number(event.target.value) || 0 })
                  }
                />
              ) : (
                <ReadOnlyValue value={formatUnitPrice(data.proposed_rate ?? 0)} />
              )}
            </InfoField>
          </>
        )}
      </CardContent>
    </Card>
  )
}
