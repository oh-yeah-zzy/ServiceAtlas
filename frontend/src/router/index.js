import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/services',
    name: 'Services',
    component: () => import('@/views/Services.vue')
  },
  {
    path: '/topology',
    name: 'Topology',
    component: () => import('@/views/Topology.vue')
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
