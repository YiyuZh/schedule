import { invoke, isTauri } from '@tauri-apps/api/core'
import { open } from '@tauri-apps/plugin-dialog'

export interface PickedTextFile {
  content: string
  fileName: string
  source: 'tauri-dialog' | 'browser-input'
  path?: string
}

function extractFileName(path: string): string {
  const segments = path.split(/[/\\]/)
  return segments[segments.length - 1] || path
}

function readBrowserFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.onerror = () => reject(new Error('Failed to read the selected file.'))
    reader.readAsText(file, 'utf-8')
  })
}

function pickWithBrowserInput(): Promise<PickedTextFile | null> {
  return new Promise((resolve, reject) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.json,.txt,application/json,text/plain'
    input.style.display = 'none'
    document.body.appendChild(input)

    input.addEventListener(
      'change',
      async () => {
        try {
          const file = input.files?.[0]
          if (!file) {
            resolve(null)
            return
          }

          const content = await readBrowserFile(file)
          resolve({
            content,
            fileName: file.name,
            source: 'browser-input',
          })
        } catch (error) {
          reject(error)
        } finally {
          input.remove()
        }
      },
      { once: true },
    )

    input.addEventListener(
      'cancel',
      () => {
        resolve(null)
        input.remove()
      },
      { once: true },
    )

    input.click()
  })
}

export async function pickJsonTextFile(): Promise<PickedTextFile | null> {
  if (isTauri()) {
    const selected = await open({
      directory: false,
      multiple: false,
      filters: [
        {
          name: 'JSON',
          extensions: ['json', 'txt'],
        },
      ],
      title: 'Select a schedule JSON file',
    })

    if (!selected || Array.isArray(selected)) {
      return null
    }

    const content = await invoke<string>('read_text_file', { path: selected })
    return {
      content,
      fileName: extractFileName(selected),
      path: selected,
      source: 'tauri-dialog',
    }
  }

  return pickWithBrowserInput()
}
