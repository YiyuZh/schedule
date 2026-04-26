import { createRouter, createWebHashHistory } from 'vue-router'

import { APP_NAME, PAGE_TITLE_MAP } from '@/config/app'
import AppLayout from '@/layouts/AppLayout.vue'

const TodayPage = () => import('@/pages/TodayPage.vue')
const LongTermTasksPage = () => import('@/pages/LongTermTasksPage.vue')
const TaskTemplatesPage = () => import('@/pages/TaskTemplatesPage.vue')
const SchedulePage = () => import('@/pages/SchedulePage.vue')
const StudyRecordsPage = () => import('@/pages/StudyRecordsPage.vue')
const ImportPage = () => import('@/pages/ImportPage.vue')
const SettingsPage = () => import('@/pages/SettingsPage.vue')
const AiWorkspacePage = () => import('@/pages/AiWorkspacePage.vue')
const FocusModePage = () => import('@/pages/FocusModePage.vue')

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      redirect: '/today',
      children: [
        {
          path: 'today',
          name: 'today',
          component: TodayPage,
          meta: { title: '今日任务' },
        },
        {
          path: 'long-term-tasks',
          name: 'long-term-tasks',
          component: LongTermTasksPage,
          meta: { title: '长期任务' },
        },
        {
          path: 'templates',
          name: 'templates',
          component: TaskTemplatesPage,
          meta: { title: '任务模板' },
        },
        {
          path: 'schedule',
          name: 'schedule',
          component: SchedulePage,
          meta: { title: '日程规划' },
        },
        {
          path: 'study-records',
          name: 'study-records',
          component: StudyRecordsPage,
          meta: { title: '学习记录' },
        },
        {
          path: 'imports',
          name: 'imports',
          component: ImportPage,
          meta: { title: '导入中心' },
        },
        {
          path: 'settings',
          name: 'settings',
          component: SettingsPage,
          meta: { title: '设置' },
        },
        {
          path: 'ai-workspace',
          name: 'ai-workspace',
          component: AiWorkspacePage,
          meta: { title: 'AI 工作区' },
        },
      ],
    },
    {
      path: '/focus-mode',
      name: 'focus-mode',
      component: FocusModePage,
      meta: { title: '沉浸式专注' },
    },
  ],
})

router.afterEach((to) => {
  const routeName = String(to.name || '')
  const pageTitle = (to.meta.title as string) || PAGE_TITLE_MAP[routeName] || APP_NAME
  document.title = pageTitle === APP_NAME ? APP_NAME : `${pageTitle} - ${APP_NAME}`
})

export default router
