<template>
  <div class="dashboard">
    <div class="page-header">
      <div>
        <h1>{{ $t('dashboard.title') }}</h1>
        <p class="subtitle">{{ $t('dashboard.subtitle') }}</p>
      </div>
      <button class="btn-refresh" @click="loadStats" :disabled="loading">
        <span class="icon">🔄</span>
        {{ $t('common.refresh') }}
      </button>
    </div>

    <div class="stats-grid">
      <div class="stat-card total">
        <div class="stat-header">
          <span class="stat-icon">💻</span>
          <span class="stat-label">{{ $t('dashboard.totalServices') }}</span>
        </div>
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-trend">
          <span class="trend-label">{{ $t('dashboard.registered') }}</span>
        </div>
      </div>

      <div class="stat-card healthy">
        <div class="stat-header">
          <span class="stat-icon">✅</span>
          <span class="stat-label">{{ $t('dashboard.healthyServices') }}</span>
        </div>
        <div class="stat-value">{{ stats.healthy }}</div>
        <div class="stat-trend positive">
          <span class="trend-label">{{ Math.round((stats.healthy / stats.total) * 100) || 0 }}% {{ $t('dashboard.healthy') }}</span>
        </div>
      </div>

      <div class="stat-card unhealthy">
        <div class="stat-header">
          <span class="stat-icon">❌</span>
          <span class="stat-label">{{ $t('dashboard.unhealthyServices') }}</span>
        </div>
        <div class="stat-value">{{ stats.unhealthy }}</div>
        <div class="stat-trend negative">
          <span class="trend-label">{{ stats.unhealthy > 0 ? $t('dashboard.needsAttention') : $t('dashboard.allGood') }}</span>
        </div>
      </div>

      <div class="stat-card gateways">
        <div class="stat-header">
          <span class="stat-icon">🌐</span>
          <span class="stat-label">{{ $t('dashboard.gatewayServices') }}</span>
        </div>
        <div class="stat-value">{{ stats.gateways }}</div>
        <div class="stat-trend">
          <span class="trend-label">{{ $t('dashboard.activeGateways') }}</span>
        </div>
      </div>
    </div>

    <div class="action-cards">
      <div class="action-card primary" @click="triggerHealthCheck" :class="{ disabled: checking }">
        <div class="action-icon">🏥</div>
        <div class="action-content">
          <h3>{{ $t('dashboard.triggerHealthCheck') }}</h3>
          <p>{{ checking ? $t('common.loading') : $t('dashboard.healthCheckDesc') }}</p>
        </div>
        <div class="action-arrow">→</div>
      </div>

      <router-link to="/services" class="action-card">
        <div class="action-icon">📋</div>
        <div class="action-content">
          <h3>{{ $t('dashboard.manageServices') }}</h3>
          <p>{{ $t('dashboard.manageServicesDesc') }}</p>
        </div>
        <div class="action-arrow">→</div>
      </router-link>

      <router-link to="/topology" class="action-card">
        <div class="action-icon">🗺️</div>
        <div class="action-content">
          <h3>{{ $t('dashboard.viewTopology') }}</h3>
          <p>{{ $t('dashboard.viewTopologyDesc') }}</p>
        </div>
        <div class="action-arrow">→</div>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { monitorApi } from '@/api'

const { t } = useI18n()

const stats = ref({
  total: 0,
  healthy: 0,
  unhealthy: 0,
  gateways: 0
})

const checking = ref(false)
const loading = ref(false)

const loadStats = async () => {
  loading.value = true
  try {
    const data = await monitorApi.getStats()
    // API 返回 { status, services: { total, healthy, ... } }
    stats.value = data.services || data
  } catch (error) {
    console.error('Failed to load stats:', error)
  } finally {
    loading.value = false
  }
}

const triggerHealthCheck = async () => {
  if (checking.value) return

  checking.value = true
  try {
    const data = await monitorApi.triggerHealthCheck()
    alert(`${t('dashboard.healthCheckComplete')}\n${t('dashboard.checked')}: ${data.result.checked} ${t('dashboard.servicesCount')}\n${t('common.healthy')}: ${data.result.healthy}\n${t('common.unhealthy')}: ${data.result.unhealthy}`)
    await loadStats()
  } catch (error) {
    alert(`${t('dashboard.healthCheckFailed')}: ${error.message}`)
  } finally {
    checking.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2.5rem;
  gap: 2rem;
}

.page-header h1 {
  margin: 0 0 0.5rem 0;
  color: #1a202c;
  font-size: 2.5rem;
  font-weight: 700;
}

.subtitle {
  margin: 0;
  color: #718096;
  font-size: 1.1rem;
}

.btn-refresh {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  color: #4a5568;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-refresh:hover:not(:disabled) {
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-refresh .icon {
  font-size: 1.2rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2.5rem;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 1.75rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  border: 1px solid #e2e8f0;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  opacity: 0;
  transition: opacity 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.1);
  border-color: #cbd5e0;
}

.stat-card:hover::before {
  opacity: 1;
}

.stat-card.total::before { background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%); }
.stat-card.healthy::before { background: linear-gradient(90deg, #10b981 0%, #059669 100%); }
.stat-card.unhealthy::before { background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%); }
.stat-card.gateways::before { background: linear-gradient(90deg, #8b5cf6 0%, #7c3aed 100%); }

.stat-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.stat-icon {
  font-size: 2rem;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: #f7fafc;
}

.stat-label {
  color: #718096;
  font-size: 0.9rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 3rem;
  font-weight: 700;
  color: #1a202c;
  line-height: 1;
  margin-bottom: 0.5rem;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.trend-label {
  color: #a0aec0;
  font-size: 0.85rem;
}

.stat-trend.positive .trend-label {
  color: #10b981;
}

.stat-trend.negative .trend-label {
  color: #ef4444;
}

.action-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
}

.action-card {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  padding: 1.75rem;
  cursor: pointer;
  text-decoration: none;
  color: inherit;
  transition: all 0.3s;
}

.action-card:hover {
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.15);
}

.action-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-card.disabled:hover {
  transform: none;
  border-color: #e2e8f0;
  box-shadow: none;
}

.action-card.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
}

.action-card.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
}

.action-card.primary .action-content h3,
.action-card.primary .action-content p,
.action-card.primary .action-arrow {
  color: white;
}

.action-icon {
  font-size: 2.5rem;
  flex-shrink: 0;
}

.action-content {
  flex: 1;
}

.action-content h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #1a202c;
}

.action-content p {
  margin: 0;
  font-size: 0.9rem;
  color: #718096;
}

.action-arrow {
  font-size: 1.5rem;
  color: #cbd5e0;
  flex-shrink: 0;
  transition: transform 0.3s;
}

.action-card:hover .action-arrow {
  transform: translateX(4px);
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .action-cards {
    grid-template-columns: 1fr;
  }

  .stat-value {
    font-size: 2.5rem;
  }
}
</style>
