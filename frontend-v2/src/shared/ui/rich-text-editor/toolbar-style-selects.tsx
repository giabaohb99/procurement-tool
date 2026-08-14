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
 * biết mình đang gõ phông gì, cỡ mấy. Bù lại, bề ngang của chúng để vừa đủ chữ
 * để dành chỗ cho các nút lệnh trên màn 13".
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
        className="w-18"
        value={String(zoom)}
        onValueChange={(value) => onZoomChange(Number(value))}
        options={ZOOM_LEVELS.map((level) => ({
          label: `${Math.round(Number(level) * 100)}%`,
          value: level,
        }))}
      />
      <ToolbarSelect
        label="Kiểu đoạn"
        className="w-30"
        value={state.blockStyle}
        onValueChange={setBlockStyle}
        options={BLOCK_STYLES}
      />
      <ToolbarSelect
        label="Phông chữ"
        className="w-36"
        previewFont
        value={state.fontFamily}
        onValueChange={(value) =>
          value === INHERIT ? run().unsetFontFamily().run() : run().setFontFamily(value).run()
        }
        options={[{ label: 'Phông mặc định', value: INHERIT }, ...FONT_FAMILIES]}
      />
      <ToolbarSelect
        label="Cỡ chữ"
        className="w-20"
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
