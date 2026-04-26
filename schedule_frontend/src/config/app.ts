import type { NavItem } from '@/types/common'

export const APP_NAME = '日程安排'
export const APP_VERSION = '0.3.0'
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
export const REQUEST_TIMEOUT = 15000

export const NAV_ITEMS: NavItem[] = [
  { label: '今日任务', path: '/today', icon: 'Calendar' },
  { label: '长期任务', path: '/long-term-tasks', icon: 'Flag' },
  { label: '任务模板', path: '/templates', icon: 'Memo' },
  { label: '日程规划', path: '/schedule', icon: 'Clock' },
  { label: '学习记录', path: '/study-records', icon: 'TrendCharts' },
  { label: '导入中心', path: '/imports', icon: 'UploadFilled' },
  { label: 'AI 工作区', path: '/ai-workspace', icon: 'MagicStick' },
  { label: '设置', path: '/settings', icon: 'Setting' },
]

export const PAGE_TITLE_MAP: Record<string, string> = {
  today: '今日任务',
  'long-term-tasks': '长期任务',
  templates: '任务模板',
  schedule: '日程规划',
  'study-records': '学习记录',
  imports: '导入中心',
  'ai-workspace': 'AI 工作区',
  settings: '设置',
  'focus-mode': '沉浸式专注',
}
