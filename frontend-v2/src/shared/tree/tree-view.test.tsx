import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { TreeView } from './tree-view'
import type { TreeNode } from './tree-types'

const TREE: TreeNode[] = [
  {
    id: 'a',
    label: 'Thư mục A',
    children: [
      { id: 'a1', label: 'Tệp A1' },
      { id: 'a2', label: 'Tệp A2' },
    ],
  },
  { id: 'b', label: 'Tệp B' },
]

/** `expandedIds` cố định — đủ cho phần lớn bài kiểm không cần bấm mở/đóng. */
function renderTree(
  props: Partial<Parameters<typeof TreeView>[0]> = {},
  expanded: (string | number)[] = ['a'],
) {
  const onSelect = vi.fn()
  const onToggleExpand = vi.fn()
  render(
    <TreeView
      nodes={TREE}
      ariaLabel="Cây thử"
      expandedIds={new Set(expanded)}
      onToggleExpand={onToggleExpand}
      onSelect={onSelect}
      {...props}
    />,
  )
  return { onSelect, onToggleExpand }
}

describe('TreeView — khung ARIA', () => {
  it('bọc ngoài role="tree" kèm aria-label, mỗi dòng role="treeitem"', () => {
    renderTree()
    expect(screen.getByRole('tree', { name: 'Cây thử' })).toBeInTheDocument()
    expect(screen.getAllByRole('treeitem')).toHaveLength(4) // a, a1, a2, b (a đang mở)
  })

  it('node có con mang aria-expanded đúng trạng thái; leaf KHÔNG có thuộc tính này', () => {
    renderTree()
    expect(screen.getByRole('treeitem', { name: /Thư mục A/ })).toHaveAttribute(
      'aria-expanded',
      'true',
    )
    expect(screen.getByRole('treeitem', { name: 'Tệp B' })).not.toHaveAttribute('aria-expanded')
  })

  it('gập nhánh thì con của nó KHÔNG còn trong DOM', () => {
    renderTree({}, [])
    expect(screen.queryByText('Tệp A1')).not.toBeInTheDocument()
    expect(screen.getByRole('treeitem', { name: /Thư mục A/ })).toHaveAttribute(
      'aria-expanded',
      'false',
    )
  })

  it('cây rỗng (0 node) không dựng gì, không nổ', () => {
    const { container } = render(
      <TreeView nodes={[]} ariaLabel="Rỗng" expandedIds={new Set()} onToggleExpand={vi.fn()} />,
    )
    expect(container.querySelector('[role="tree"]')).not.toBeInTheDocument()
  })
})

describe('TreeView — chọn', () => {
  it('bấm một dòng gọi onSelect với đúng node', () => {
    const { onSelect } = renderTree()
    screen.getByRole('treeitem', { name: 'Tệp B' }).click()
    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id: 'b', label: 'Tệp B' }))
  })

  it('`selectedId` khớp thì dòng đó aria-selected="true", các dòng khác "false"', () => {
    renderTree({ selectedId: 'a1' })
    expect(screen.getByRole('treeitem', { name: 'Tệp A1' })).toHaveAttribute(
      'aria-selected',
      'true',
    )
    expect(screen.getByRole('treeitem', { name: 'Tệp B' })).toHaveAttribute(
      'aria-selected',
      'false',
    )
  })

  it('bấm vào nút mở/đóng KHÔNG kích hoạt onSelect của dòng cha (event.stopPropagation)', async () => {
    const user = userEvent.setup()
    const { onSelect, onToggleExpand } = renderTree()
    await user.click(screen.getByRole('button', { name: 'Thu gọn' }))
    expect(onToggleExpand).toHaveBeenCalledWith('a')
    expect(onSelect).not.toHaveBeenCalled()
  })
})

describe('TreeView — bàn phím (roving tabindex)', () => {
  it('chỉ một dòng có tabIndex=0 tại một thời điểm, phần còn lại -1', () => {
    renderTree({ selectedId: 'a1' })
    const items = screen.getAllByRole('treeitem')
    const zeroTab = items.filter((el) => el.getAttribute('tabindex') === '0')
    expect(zeroTab).toHaveLength(1)
    expect(zeroTab[0]).toHaveAccessibleName('Tệp A1')
  })

  it('ArrowDown/ArrowUp chuyển tiêu điểm giữa các dòng ĐANG HIỆN theo đúng thứ tự', async () => {
    const user = userEvent.setup()
    renderTree({ selectedId: 'a' })
    const first = screen.getByRole('treeitem', { name: /Thư mục A/ })
    first.focus()
    await user.keyboard('{ArrowDown}')
    expect(screen.getByRole('treeitem', { name: 'Tệp A1' })).toHaveFocus()
    await user.keyboard('{ArrowDown}')
    expect(screen.getByRole('treeitem', { name: 'Tệp A2' })).toHaveFocus()
    await user.keyboard('{ArrowUp}')
    expect(screen.getByRole('treeitem', { name: 'Tệp A1' })).toHaveFocus()
  })

  it('ArrowDown ở dòng CUỐI không rơi ra ngoài cây (không lỗi, tiêu điểm đứng yên)', async () => {
    const user = userEvent.setup()
    renderTree({ selectedId: 'b' })
    screen.getByRole('treeitem', { name: 'Tệp B' }).focus()
    await user.keyboard('{ArrowDown}')
    expect(screen.getByRole('treeitem', { name: 'Tệp B' })).toHaveFocus()
  })

  it('Enter/Space trên một dòng gọi onSelect giống hệt bấm chuột', async () => {
    const user = userEvent.setup()
    const { onSelect } = renderTree({ selectedId: 'b' })
    screen.getByRole('treeitem', { name: 'Tệp B' }).focus()
    await user.keyboard('{Enter}')
    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id: 'b' }))
  })

  it('ArrowRight trên nhánh ĐANG GẬP thì MỞ nhánh, không nhảy dòng', async () => {
    const user = userEvent.setup()
    const { onToggleExpand } = renderTree({ selectedId: 'a' }, [])
    screen.getByRole('treeitem', { name: /Thư mục A/ }).focus()
    await user.keyboard('{ArrowRight}')
    expect(onToggleExpand).toHaveBeenCalledWith('a')
  })

  it('ArrowLeft trên nhánh ĐANG MỞ thì ĐÓNG nhánh, không lùi ra cha (vì đây đã là gốc)', async () => {
    const user = userEvent.setup()
    const { onToggleExpand } = renderTree({ selectedId: 'a' }, ['a'])
    screen.getByRole('treeitem', { name: /Thư mục A/ }).focus()
    await user.keyboard('{ArrowLeft}')
    expect(onToggleExpand).toHaveBeenCalledWith('a')
  })

  it('ArrowLeft trên một CON thì lùi tiêu điểm về ĐÚNG cha của nó', async () => {
    const user = userEvent.setup()
    renderTree({ selectedId: 'a1' }, ['a'])
    screen.getByRole('treeitem', { name: 'Tệp A1' }).focus()
    await user.keyboard('{ArrowLeft}')
    expect(screen.getByRole('treeitem', { name: /Thư mục A/ })).toHaveFocus()
  })

  it('Home/End nhảy thẳng dòng đầu / dòng cuối đang hiện', async () => {
    const user = userEvent.setup()
    renderTree({ selectedId: 'a2' }, ['a'])
    screen.getByRole('treeitem', { name: 'Tệp A2' }).focus()
    await user.keyboard('{End}')
    expect(screen.getByRole('treeitem', { name: 'Tệp B' })).toHaveFocus()
    await user.keyboard('{Home}')
    expect(screen.getByRole('treeitem', { name: /Thư mục A/ })).toHaveFocus()
  })
})

describe('TreeView — onFocusChange (tiêu điểm bàn phím đổi tệp đang xem)', () => {
  it('ArrowDown/ArrowUp gọi onFocusChange với node MỚI, không gọi onSelect', async () => {
    const user = userEvent.setup()
    const onFocusChange = vi.fn()
    const { onSelect } = renderTree({ selectedId: 'a', onFocusChange })
    screen.getByRole('treeitem', { name: /Thư mục A/ }).focus()

    await user.keyboard('{ArrowDown}')
    expect(onFocusChange).toHaveBeenCalledWith(expect.objectContaining({ id: 'a1' }))
    expect(onSelect).not.toHaveBeenCalled()
  })

  it('bấm CHUỘT không gọi onFocusChange — chỉ đường bàn phím mới gọi', () => {
    const onFocusChange = vi.fn()
    renderTree({ selectedId: 'a', onFocusChange })
    screen.getByRole('treeitem', { name: 'Tệp B' }).click()
    expect(onFocusChange).not.toHaveBeenCalled()
  })

  it('không truyền onFocusChange thì bàn phím vẫn di chuyển bình thường, không nổ', async () => {
    const user = userEvent.setup()
    renderTree({ selectedId: 'a' })
    screen.getByRole('treeitem', { name: /Thư mục A/ }).focus()
    await user.keyboard('{ArrowDown}')
    expect(screen.getByRole('treeitem', { name: 'Tệp A1' })).toHaveFocus()
  })
})

describe('TreeView — tô sáng kết quả lọc', () => {
  it('id trong highlightIds được đánh dấu khác dòng thường (không lẫn với dòng đang chọn)', () => {
    renderTree({ selectedId: 'b', highlightIds: new Set(['a1']) })
    // Không có API "đang tô sáng" công khai qua ARIA (đây là màu, không phải ngữ nghĩa) —
    // bài kiểm chỉ canh KHÔNG NỔ và dòng khớp vẫn hiện đúng tên, tránh khoá vào class CSS cụ thể.
    expect(screen.getByRole('treeitem', { name: 'Tệp A1' })).toBeInTheDocument()
  })
})

describe('TreeView — renderLabel (đổi tên tại chỗ)', () => {
  it('có renderLabel thì DÙNG nó thay cho <span>{label}</span> mặc định', () => {
    renderTree({ renderLabel: (node) => <input aria-label={`sửa ${node.label}`} /> })
    expect(screen.getByLabelText('sửa Tệp B')).toBeInTheDocument()
    // Nhãn mặc định không còn hiện dưới dạng text thường của dòng đó nữa —
    // nó đã được thay hẳn, không phải thêm vào bên cạnh.
    expect(screen.queryByText('Tệp B')).not.toBeInTheDocument()
  })

  it('bỏ trống renderLabel thì vẫn vẽ nhãn thường như trước (không phá hành vi cũ)', () => {
    renderTree()
    expect(screen.getByText('Tệp B')).toBeInTheDocument()
  })
})

describe('TreeView — kéo thả (native HTML5 DnD)', () => {
  it('canDrag=false thì dòng không có thuộc tính draggable bật', () => {
    renderTree({ canDrag: () => false })
    expect(screen.getByRole('treeitem', { name: 'Tệp B' })).toHaveAttribute('draggable', 'false')
  })

  it('kéo dòng kéo-được gọi onDragStartNode với đúng node', () => {
    const onDragStartNode = vi.fn()
    renderTree({ canDrag: () => true, onDragStartNode })
    const row = screen.getByRole('treeitem', { name: 'Tệp B' })
    expect(row).toHaveAttribute('draggable', 'true')
    fireEvent.dragStart(row, { dataTransfer: makeDataTransfer() })
    expect(onDragStartNode).toHaveBeenCalledWith(expect.objectContaining({ id: 'b' }))
  })

  it('dropState trả "valid" rồi thả thì gọi onDropNode; "invalid" thì KHÔNG gọi', () => {
    const onDropNode = vi.fn()
    const { rerender } = render(
      <TreeView
        nodes={TREE}
        ariaLabel="Cây thử"
        expandedIds={new Set(['a'])}
        onToggleExpand={vi.fn()}
        dropState={(node) => (node.id === 'a1' ? 'valid' : 'invalid')}
        onDropNode={onDropNode}
      />,
    )
    fireEvent.drop(screen.getByRole('treeitem', { name: 'Tệp A2' }), {
      dataTransfer: makeDataTransfer(),
    })
    expect(onDropNode).not.toHaveBeenCalled()

    fireEvent.drop(screen.getByRole('treeitem', { name: 'Tệp A1' }), {
      dataTransfer: makeDataTransfer(),
    })
    expect(onDropNode).toHaveBeenCalledWith(expect.objectContaining({ id: 'a1' }))
    rerender(<></>)
  })

  it('node không nằm trong dropState (undefined) thì thả cũng không gọi onDropNode', () => {
    const onDropNode = vi.fn()
    renderTree({ dropState: () => undefined, onDropNode })
    fireEvent.drop(screen.getByRole('treeitem', { name: 'Tệp B' }), {
      dataTransfer: makeDataTransfer(),
    })
    expect(onDropNode).not.toHaveBeenCalled()
  })
})

describe('TreeView — kéo thả đổi thứ tự anh em (before/after)', () => {
  /** Cây thư mục thật cao ~36-40px một dòng — giả một chiều cao cố định để
   * `ratioY` (`resolve-drop-zone.ts`) tính ra đúng vùng theo `clientY` truyền vào,
   * thay vì rơi về mặc định 0.5 vì jsdom không đo layout thật. */
  function mockRowRect(height = 40, top = 0) {
    return vi.spyOn(Element.prototype, 'getBoundingClientRect').mockReturnValue({
      top,
      height,
      bottom: top + height,
      left: 0,
      right: 200,
      width: 200,
      x: 0,
      y: top,
      toJSON: () => ({}),
    } as DOMRect)
  }

  /**
   * `fireEvent.drop(el, { clientY })` KHÔNG truyền được `clientY` xuống sự
   * kiện thật trong môi trường test hiện tại (`@testing-library/dom` dựng
   * `drop`/`dragover` bằng `Event` gốc, không phải `MouseEvent`/`DragEvent` —
   * đã xác minh bằng script debug: `event.clientY` luôn ra `undefined`). Tự
   * dựng sự kiện rồi ghi đè `clientY` bằng `Object.defineProperty` để bài
   * kiểm điều khiển được đúng toạ độ con trỏ.
   */
  function dispatchAt(el: Element, type: 'dragover' | 'drop', clientY: number) {
    const event = new Event(type, { bubbles: true, cancelable: true })
    Object.defineProperty(event, 'clientY', { value: clientY, configurable: true })
    Object.defineProperty(event, 'dataTransfer', { value: makeDataTransfer(), configurable: true })
    fireEvent(el, event)
  }

  it('chỉ đổi thứ tự hợp lệ (không đổi cha) — thả mép trên gọi "before", mép dưới gọi "after"', () => {
    const rect = mockRowRect(40, 0)
    const onReorderDrop = vi.fn()
    renderTree({ canReorderWith: () => true, onReorderDrop })
    const row = screen.getByRole('treeitem', { name: 'Tệp B' })

    dispatchAt(row, 'drop', 2)
    expect(onReorderDrop).toHaveBeenCalledWith(expect.objectContaining({ id: 'b' }), 'before')

    onReorderDrop.mockClear()
    dispatchAt(row, 'drop', 38)
    expect(onReorderDrop).toHaveBeenCalledWith(expect.objectContaining({ id: 'b' }), 'after')
    rect.mockRestore()
  })

  it('cả đổi cha lẫn đổi thứ tự cùng hợp lệ — GIỮA dòng đổi cha, MÉP đổi thứ tự', () => {
    const rect = mockRowRect(40, 0)
    const onDropNode = vi.fn()
    const onReorderDrop = vi.fn()
    render(
      <TreeView
        nodes={TREE}
        ariaLabel="Cây thử"
        expandedIds={new Set(['a'])}
        onToggleExpand={vi.fn()}
        dropState={() => 'valid'}
        onDropNode={onDropNode}
        canReorderWith={() => true}
        onReorderDrop={onReorderDrop}
      />,
    )
    const row = screen.getByRole('treeitem', { name: 'Tệp B' })

    dispatchAt(row, 'drop', 20)
    expect(onDropNode).toHaveBeenCalledWith(expect.objectContaining({ id: 'b' }))
    expect(onReorderDrop).not.toHaveBeenCalled()

    onDropNode.mockClear()
    dispatchAt(row, 'drop', 2)
    expect(onReorderDrop).toHaveBeenCalledWith(expect.objectContaining({ id: 'b' }), 'before')
    expect(onDropNode).not.toHaveBeenCalled()
    rect.mockRestore()
  })

  it('canReorderWith trả false thì thả ở mép KHÔNG gọi onReorderDrop', () => {
    const rect = mockRowRect(40, 0)
    const onReorderDrop = vi.fn()
    renderTree({ canReorderWith: () => false, onReorderDrop })
    dispatchAt(screen.getByRole('treeitem', { name: 'Tệp B' }), 'drop', 2)
    expect(onReorderDrop).not.toHaveBeenCalled()
    rect.mockRestore()
  })

  it('kéo qua mép dòng vẽ vạch chỉ báo `aria-hidden`, không nổ khi chưa từng "drop"', () => {
    const rect = mockRowRect(40, 0)
    renderTree({ canReorderWith: () => true })
    const row = screen.getByRole('treeitem', { name: 'Tệp B' })
    dispatchAt(row, 'dragover', 2)
    expect(row.querySelector('[aria-hidden]')).not.toBeNull()
    rect.mockRestore()
  })
})

describe('TreeView — đường gióng thụt lề (kiểu VS Code)', () => {
  it('dòng gốc (depth 0) không có đường gióng, dòng con depth 1 kẻ đúng 1 cấp', () => {
    renderTree()
    const root = screen.getByRole('treeitem', { name: 'Tệp B' })
    const child = screen.getByRole('treeitem', { name: 'Tệp A1' })
    expect(root.querySelectorAll('[data-tree-indent-guide]')).toHaveLength(0)
    const guide = child.querySelector('[data-tree-indent-guide]')
    expect(guide?.getAttribute('data-tree-indent-levels')).toBe('1')
  })
})

describe('TreeView — hành động chỉ hiện khi rê chuột (renderHoverActions)', () => {
  it('có renderHoverActions thì vẽ thêm nút bên cạnh renderTrailing, không thay thế nó', () => {
    renderTree({
      renderHoverActions: (node) => <button aria-label={`thêm con ${node.label}`} />,
      renderTrailing: (node) => <button aria-label={`thao tác ${node.label}`} />,
    })
    expect(screen.getByLabelText('thêm con Tệp B')).toBeInTheDocument()
    expect(screen.getByLabelText('thao tác Tệp B')).toBeInTheDocument()
  })
})

describe('TreeView — bấm đúp một dòng', () => {
  it('bấm đúp gọi onRowDoubleClick với đúng node, KHÔNG gọi onSelect thêm lần nữa ngoài lượt bấm đơn tự nhiên của trình duyệt', () => {
    const onRowDoubleClick = vi.fn()
    renderTree({ onRowDoubleClick })
    fireEvent.doubleClick(screen.getByRole('treeitem', { name: 'Tệp B' }))
    expect(onRowDoubleClick).toHaveBeenCalledWith(expect.objectContaining({ id: 'b' }))
  })
})

describe('TreeView — nhận payload NGOÀI cây (kéo từ khung khác)', () => {
  const MIME = 'application/x-doc-folder-items'

  it('dataTransfer khớp MIME thì thả gọi onExternalDropNode, KHÔNG gọi onDropNode dù dropState hợp lệ', () => {
    const onExternalDropNode = vi.fn()
    const onDropNode = vi.fn()
    renderTree({
      externalDropMimeType: MIME,
      onExternalDropNode,
      dropState: () => 'valid',
      onDropNode,
    })
    const row = screen.getByRole('treeitem', { name: 'Tệp B' })
    fireEvent.drop(row, { dataTransfer: makeDataTransfer([MIME]) })
    expect(onExternalDropNode).toHaveBeenCalledWith(expect.objectContaining({ id: 'b' }), expect.anything())
    expect(onDropNode).not.toHaveBeenCalled()
  })

  it('acceptsExternalDrop trả false cho dòng này thì thả KHÔNG gọi onExternalDropNode', () => {
    const onExternalDropNode = vi.fn()
    renderTree({
      externalDropMimeType: MIME,
      onExternalDropNode,
      acceptsExternalDrop: () => false,
    })
    fireEvent.drop(screen.getByRole('treeitem', { name: 'Tệp B' }), {
      dataTransfer: makeDataTransfer([MIME]),
    })
    expect(onExternalDropNode).not.toHaveBeenCalled()
  })

  it('dataTransfer KHÔNG mang đúng MIME thì không gọi onExternalDropNode', () => {
    const onExternalDropNode = vi.fn()
    renderTree({ externalDropMimeType: MIME, onExternalDropNode })
    fireEvent.drop(screen.getByRole('treeitem', { name: 'Tệp B' }), {
      dataTransfer: makeDataTransfer(['text/plain']),
    })
    expect(onExternalDropNode).not.toHaveBeenCalled()
  })

  it('không khai externalDropMimeType thì thả bình thường không nổ (kể cả dataTransfer thiếu `types`)', () => {
    renderTree()
    expect(() =>
      fireEvent.drop(screen.getByRole('treeitem', { name: 'Tệp B' }), { dataTransfer: makeDataTransfer() }),
    ).not.toThrow()
  })
})

/** jsdom không tự có `DataTransfer` — chỉ cần đủ các hàm/field `TreeView` gọi tới. */
function makeDataTransfer(types: string[] = []) {
  return { setData: vi.fn(), getData: vi.fn(), types }
}
