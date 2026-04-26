import { afterEach, describe, expect, it, vi } from 'vitest'

describe('pickJsonTextFile', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.resetModules()
  })

  it('uses tauri dialog in desktop mode', async () => {
    const openMock = vi.fn().mockResolvedValue('C:\\schedule\\courses.json')
    const invokeMock = vi.fn().mockResolvedValue('{"ok":true}')

    vi.doMock('@tauri-apps/api/core', () => ({
      isTauri: () => true,
      invoke: invokeMock,
    }))
    vi.doMock('@tauri-apps/plugin-dialog', () => ({
      open: openMock,
    }))

    const { pickJsonTextFile } = await import('@/utils/desktop')
    const result = await pickJsonTextFile()

    expect(openMock).toHaveBeenCalled()
    expect(invokeMock).toHaveBeenCalledWith('read_text_file', { path: 'C:\\schedule\\courses.json' })
    expect(result).toEqual({
      content: '{"ok":true}',
      fileName: 'courses.json',
      path: 'C:\\schedule\\courses.json',
      source: 'tauri-dialog',
    })
  })

  it('falls back to browser input when not running in tauri', async () => {
    const file = new File(['{"hello":"world"}'], 'import.json', { type: 'application/json' })
    const fileList = {
      0: file,
      length: 1,
      item: (index: number) => (index === 0 ? file : null),
    } as unknown as FileList

    class MockFileReader {
      result: string | ArrayBuffer | null = null
      onload: ((this: FileReader, ev: ProgressEvent<FileReader>) => void) | null = null
      onerror: ((this: FileReader, ev: ProgressEvent<FileReader>) => void) | null = null

      readAsText(target: File): void {
        this.result = target === file ? '{"hello":"world"}' : ''
        this.onload?.call(this as unknown as FileReader, {} as ProgressEvent<FileReader>)
      }
    }

    const originalCreateElement = document.createElement.bind(document)
    vi.stubGlobal('FileReader', MockFileReader)

    vi.doMock('@tauri-apps/api/core', () => ({
      isTauri: () => false,
      invoke: vi.fn(),
    }))
    vi.doMock('@tauri-apps/plugin-dialog', () => ({
      open: vi.fn(),
    }))

    vi.spyOn(document, 'createElement').mockImplementation(((tagName: string) => {
      const element = originalCreateElement(tagName)
      if (tagName === 'input') {
        const input = element as HTMLInputElement
        Object.defineProperty(input, 'files', {
          configurable: true,
          get: () => fileList,
        })
        queueMicrotask(() => input.dispatchEvent(new Event('change')))
        return input
      }
      return element
    }) as typeof document.createElement)

    const { pickJsonTextFile } = await import('@/utils/desktop')
    const result = await pickJsonTextFile()

    expect(result).toEqual({
      content: '{"hello":"world"}',
      fileName: 'import.json',
      source: 'browser-input',
    })
  })
})
