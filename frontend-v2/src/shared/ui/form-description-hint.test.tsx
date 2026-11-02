import { fireEvent, render, screen } from '@testing-library/react'
import { useForm } from 'react-hook-form'
import { describe, expect, it, vi } from 'vitest'

import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel } from './form'
import { FormSectionProvider, type FormSectionContextValue } from './form-section'
import { Input } from './input'

function Field({ hints }: { hints?: FormSectionContextValue['hints'] }) {
  const form = useForm({ defaultValues: { company: '' } })
  return (
    <FormSectionProvider value={{ variant: 'flat', hints }}>
      <Form {...form}>
        <form onSubmit={(event) => event.preventDefault()}>
          <FormField
            control={form.control}
            name="company"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Công ty</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormDescription>Pháp nhân quyết định phạm vi dữ liệu.</FormDescription>
              </FormItem>
            )}
          />
        </form>
      </Form>
    </FormSectionProvider>
  )
}

describe('FormDescription', () => {
  it('stays an inline line of text by default', () => {
    render(<Field />)
    expect(screen.getByText('Pháp nhân quyết định phạm vi dữ liệu.').tagName).toBe('P')
    expect(screen.queryByRole('button', { name: 'Xem giải thích' })).not.toBeInTheDocument()
  })

  it('folds into an (i) button in icon mode but keeps the text wired to aria-describedby', () => {
    render(<Field hints="icon" />)
    const input = screen.getByRole('textbox', { name: 'Công ty' })
    //  Trình đọc màn hình vẫn đọc chú thích khi vào ô, dù mắt thường không thấy dòng chữ.
    expect(input).toHaveAccessibleDescription('Pháp nhân quyết định phạm vi dữ liệu.')
    const hint = screen.getByRole('button', { name: 'Xem giải thích' })
    //  Nằm trong <form>: thiếu type="button" là bấm (i) thành LƯU hồ sơ.
    expect(hint).toHaveAttribute('type', 'button')
  })

  it('opens the explanation on click without submitting the form', () => {
    const submit = vi.fn()
    const { container } = render(<Field hints="icon" />)
    container.querySelector('form')?.addEventListener('submit', submit)
    fireEvent.click(screen.getByRole('button', { name: 'Xem giải thích' }))
    expect(screen.getAllByText('Pháp nhân quyết định phạm vi dữ liệu.').length).toBeGreaterThan(1)
    expect(submit).not.toHaveBeenCalled()
  })
})
