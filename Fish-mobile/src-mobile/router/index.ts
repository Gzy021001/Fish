import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/login',
      name: 'MobileLogin',
      component: () => import('../pages/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      component: () => import('../components/MobileLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/dashboard' },
        { path: 'dashboard', name: 'MobileDashboard', component: () => import('../pages/Dashboard.vue') },
        { path: 'billing', name: 'MobileBilling', component: () => import('../pages/Billing.vue') },
        { path: 'billing/new', name: 'MobileBillingNew', component: () => import('../pages/BillingForm.vue') },
        { path: 'billing/edit/:id', name: 'MobileBillingEdit', component: () => import('../pages/BillingForm.vue') },
        { path: 'billing/:id', name: 'MobileBillingDetail', component: () => import('../pages/BillingDetail.vue') },
        { path: 'species', name: 'MobileSpecies', component: () => import('../pages/Species.vue') },
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/dashboard',
    }
  ]
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.token) {
    next('/login')
    return
  }
  if (to.path === '/login' && authStore.token) {
    next('/dashboard')
    return
  }
  next()
})

export default router
