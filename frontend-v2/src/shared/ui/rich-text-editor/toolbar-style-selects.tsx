import type { Editor } from '@tiptap/react'

import {
  BLOCK_STYLES,
  FONT_FAMILIES,
  FONT_SIZES,
  INHERIT,
  ZOOM_LEVELS,
} from './editor-options'
import { ToolbarSelect } from './toolbar-primitives'
import type { ToolbarState } from './use-toolbar-state'

interface ToolbarStyleSelectsProps {
  editor: Editor
  state: ToolbarState
  zoom: number
  onZoomChange: (zoom: number) => void
}

/**
 * Bốn ô chọn của thanh công cụ: mức phóng, kiểu đoạn, phông, cỡ chữ.
 *
 * Bốn ô này KHÔNG bao giờ bị thu vào menu "Thêm" — chúng vừa là nơi bấm vừa là
 * nơi ĐỌC ra định dạng của đoạn đang đứng, giấu đi thì người dùng mất luôn cách
 * biết mình đang gõ phông gì, cỡ mấy.
 *
 * ⚠️ BỀ NGANG PHẢI ĐỦ CHO NHÃN DÀI NHẤT. Trước đây bóp hẹp để nhường chỗ cho
 * các nút lệnh, kết quả là chữ bị cắt cụt giữa chừng: "Phông mặc địn", "Cỡ g",
 * và mức phóng mất luôn dấu phần trăm ("100"). Cắt chữ thì không tiết kiệm được
 * gì — người dùng vẫn phải mở ra xem mình đang ở đâu.
 *
 * Số đo (đo thật ở `text-sm`, cùng phông giao diện) + 48px cho lề ô và mũi tên:
 *
 * | Ô          | Nhãn dài nhất     | Chữ   | Cần   | Đặt          |
 * | ---------- | ----------------- | ----- | ----- | ------------ |
 * | Mức phóng  | `100%`            |  37px |  85px | `w-22` 88px  |
 * | Kiểu đoạn  | `Tiêu đề 3`       |  70px | 118px | `w-32` 128px |
 * | Phông chữ  | `Times New Roman` | 120px | 168px | `w-44` 176px |
 * | Cỡ chữ     | `Cỡ gốc`          |  47px |  95px | `w-26` 104px |
 *
 * Thanh công cụ chật thì các NÚT LỆNH tự thu vào menu "Thêm"
 * (`use-toolbar-density.ts`) — chỗ nhường là ở đó, không phải ở bốn ô này.
 */
export function ToolbarStyleSelects({
  editor,
  state,
  zoom,
  onZoomChange,
}: ToolbarStyleSelectsProps) {
  const run = () => editor.chain().focus()

  function setBlockStyle(value: string) {
    if (value === 'paragraph') run().setParagraph().run()
    else run().toggleHeading({ level: Number(value) as 1 | 2 | 3 }).run()
  }

  return (
    <>
      <ToolbarSelect
        label="Mức phóng"
        className="w-22"
        value={String(zoom)}
        onValueChange={(value) => onZoomChange(Number(value))}
        options={ZOOM_LEVELS.map((level) => ({
          label: `${Math.round(Number(level) * 100)}%`,
          value: level,
        }))}
      />
      <ToolbarSelect
        label="Kiểu đoạn"
        className="w-32"
        value={state.blockStyle}
        onValueChange={setBlockStyle}
        options={BLOCK_STYLES}
      />
      <ToolbarSelect
        label="Phông chữ"
        className="w-44"
        previewFont
        value={state.fontFamily}
        onValueChange={(value) =>
          value === INHERIT ? run().unsetFontFamily().run() : run().setFontFamily(value).run()
        }
        options={[{ label: 'Phông mặc định', value: INHERIT }, ...FONT_FAMILIES]}
      />
      <ToolbarSelect
        label="Cỡ chữ"
        className="w-26"
        value={state.fontSize}
        onValueChange={(value) =>
          value === INHERIT ? run().unsetFontSize().run() : run().setFontSize(value).run()
        }
        options={[
          { label: 'Cỡ gốc', value: INHERIT },
          ...FONT_SIZES.map((size) => ({ label: size.replace('pt', ''), value: size })),
        ]}
      />
    </>
  )
}
