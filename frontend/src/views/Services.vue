<template>
  <div class="services-page">
    <div class="page-header">
      <h1>{{ $t('services.title') }}</h1>
      <button class="btn btn-primary" @click="showModal = true">
        + {{ $t('services.addService') }}
      </button>
    </div>

    <div class="services-table-wrapper">
      <table class="services-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>{{ $t('common.name') }}</th>
            <th>{{ $t('common.address') }}</th>
            <th>{{ $t('common.status') }}</th>
            <th>{{ $t('common.type') }}</th>
            <th>{{ $t('services.registeredAt') }}</th>
            <th>{{ $t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="service in services" :key="service.id">
            <td><code>{{ service.id }}</code></td>
            <td>{{ service.name }}</td>
            <td>
              <a :href="service.base_url" target="_blank">
                {{ service.host }}:{{ service.port }}
              </a>
            </td>
            <td>
              <span :class="['status-badge', `status-${service.status}`]">
                {{ getStatusText(service.status) }}
              </span>
            </td>
            <td>
              <span v-if="service.is_gateway" class="type-badge gateway">
                {{ $t('common.gateway') }}
              </span>
              <span v-else class="type-badge service">
                {{ $t('common.service') }}
              </span>
            </td>
            <td>{{ formatDate(service.registered_at) }}</td>
            <td>
              <button class="btn btn-sm btn-danger" @click="deleteService(service)">
                {{ $t('common.delete') }}
              </button>
            </td>
          </tr>
          <tr v-if="services.length === 0">
            <td colspan="7" class="empty-message">{{ $t('services.noServices') }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 注册服务模态框 -->
    <div v-if="showModal" class="modal show" @click.self="showModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h2>{{ $t('services.addService') }}</h2>
          <button class="close-btn" @click="showModal = false">&times;</button>
        </div>
        <form @submit.prevent="registerService">
          <div class="form-group">
            <label>ID *</label>
            <input v-model="form.id" type="text" required placeholder="deckview">
          </div>
          <div class="form-group">
            <label>{{ $t('services.serviceName') }} *</label>
            <input v-model="form.name" type="text" required placeholder="DeckView">
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>{{ $t('services.serviceHost') }} *</label>
              <input v-model="form.host" type="text" required placeholder="127.0.0.1">
            </div>
            <div class="form-group">
              <label>{{ $t('services.servicePort') }} *</label>
              <input v-model.number="form.port" type="number" required placeholder="8000" min="1" max="65535">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>{{ $t('common.type') }}</label>
              <select v-model="form.protocol">
                <option value="http">HTTP</option>
                <option value="https">HTTPS</option>
              </select>
            </div>
            <div class="form-group">
              <label>{{ $t('services.healthCheckPath') }}</label>
              <input v-model="form.health_check_path" type="text" placeholder="/health">
            </div>
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="form.is_gateway" type="checkbox">
              {{ $t('services.isGateway') }}
            </label>
          </div>
          <div class="form-actions">
            <button type="button" class="btn btn-secondary" @click="showModal = false">
              {{ $t('common.cancel') }}
            </button>
            <button type="submit" class="btn btn-primary">
              {{ $t('common.save') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { servicesApi } from '@/api'

const { t } = useI18n()

const services = ref([])
const showModal = ref(false)

const form = reactive({
  id: '',
  name: '',
  host: '',
  port: null,
  protocol: 'http',
  health_check_path: '/health',
  is_gateway: false
})

const resetForm = () => {
  form.id = ''
  form.name = ''
  form.host = ''
  form.port = null
  form.protocol = 'http'
  form.health_check_path = '/health'
  form.is_gateway = false
}

const loadServices = async () => {
  try {
    services.value = await servicesApi.getAll()
  } catch (error) {
    console.error('Failed to load services:', error)
  }
}

const getStatusText = (status) => {
  const statusMap = {
    healthy: t('common.healthy'),
    unhealthy: t('common.unhealthy'),
    unknown: t('common.unknown')
  }
  return statusMap[status] || status
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString()
}

const registerService = async () => {
  try {
    await servicesApi.register({
      ...form,
      health_check_path: form.health_check_path || '/health'
    })
    alert(t('services.saveSuccess'))
    showModal.value = false
    resetForm()
    await loadServices()
  } catch (error) {
    alert(`${t('services.saveFailed')}: ${error.message}`)
  }
}

const deleteService = async (service) => {
  if (!confirm(t('services.deleteConfirm', { name: service.name }))) {
    return
  }
  try {
    await servicesApi.delete(service.id)
    alert(t('services.deleteSuccess'))
    await loadServices()
  } catch (error) {
    alert(`${t('services.deleteFailed')}: ${error.message}`)
  }
}

onMounted(() => {
  loadServices()
})
</script>

<style scoped>
.services-page {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2.5rem;
}

.services-page h1 {
  color: #1a202c;
  margin: 0;
  font-size: 2.5rem;
  font-weight: 700;
}

.services-table-wrapper {
  background: white;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.services-table {
  width: 100%;
  border-collapse: collapse;
}

.services-table th,
.services-table td {
  padding: 1.25rem 1.5rem;
  text-align: left;
  border-bottom: 1px solid #f1f5f9;
}

.services-table th {
  background: linear-gradient(to bottom, #f8fafc, #f1f5f9);
  font-weight: 600;
  color: #64748b;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.services-table tbody tr {
  transition: all 0.2s;
}

.services-table tbody tr:hover {
  background: #f8fafc;
  transform: scale(1.001);
}

.services-table tbody tr:last-child td {
  border-bottom: none;
}

.services-table code {
  background: linear-gradient(135deg, #667eea15, #764ba215);
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  color: #667eea;
  border: 1px solid #667eea30;
}

.services-table a {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.services-table a:hover {
  color: #764ba2;
  text-decoration: underline;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.35rem 0.85rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.status-healthy {
  background: linear-gradient(135deg, #d4edda, #c3e6cb);
  color: #155724;
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.1);
}

.status-unhealthy {
  background: linear-gradient(135deg, #f8d7da, #f5c6cb);
  color: #721c24;
  box-shadow: 0 2px 4px rgba(239, 68, 68, 0.1);
}

.status-unknown {
  background: linear-gradient(135deg, #e2e3e5, #d6d8db);
  color: #383d41;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.type-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.35rem 0.85rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
}

.type-badge.gateway {
  background: linear-gradient(135deg, #e8daef, #d7bde2);
  color: #6c3483;
  box-shadow: 0 2px 4px rgba(139, 92, 246, 0.1);
}

.type-badge.service {
  background: linear-gradient(135deg, #d4e6f1, #aed6f1);
  color: #1a5276;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.1);
}

.empty-message {
  text-align: center;
  padding: 4rem 2rem;
  color: #94a3b8;
  font-size: 1.1rem;
}

/* 模态框 */
.modal {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(4px);
  z-index: 1000;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.2s;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal.show {
  display: flex;
}

.modal-content {
  background: white;
  border-radius: 16px;
  width: 90%;
  max-width: 550px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  animation: slideUp 0.3s;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2rem;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(to bottom, #ffffff, #f8fafc);
}

.modal-header h2 {
  font-size: 1.5rem;
  color: #1a202c;
  margin: 0;
  font-weight: 700;
}

.close-btn {
  background: #f1f5f9;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  font-size: 1.5rem;
  cursor: pointer;
  color: #64748b;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: #e2e8f0;
  color: #1a202c;
  transform: rotate(90deg);
}

/* 表单 */
form {
  padding: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #334155;
  font-size: 0.9rem;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 1rem;
  transition: all 0.2s;
  background: #f8fafc;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  padding: 0.75rem;
  border-radius: 8px;
  transition: background 0.2s;
}

.checkbox-label:hover {
  background: #f8fafc;
}

.checkbox-label input {
  width: auto;
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e2e8f0;
}

/* 按钮 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.875rem 1.75rem;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.btn-primary:active {
  transform: translateY(0);
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
  border: 2px solid #e2e8f0;
}

.btn-secondary:hover {
  background: #e2e8f0;
  border-color: #cbd5e0;
}

.btn-danger {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
}

.btn-danger:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

@media (max-width: 768px) {
  .services-page h1 {
    font-size: 2rem;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .services-table th,
  .services-table td {
    padding: 1rem;
  }
}
</style>
