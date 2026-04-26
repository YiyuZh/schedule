export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface NavItem {
  label: string
  path: string
  icon: string
}

export type RuntimeMode = 'tauri' | 'web'

export interface DeleteResult {
  id: number
  deleted: boolean
}

export interface HealthStatus {
  status: string
}

export interface SystemInfo {
  app_name: string
  app_version: string
  database_status: string
  database_path: string
  ai_enabled: boolean
  current_time: string
  python_version: string
}

export interface PagedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
