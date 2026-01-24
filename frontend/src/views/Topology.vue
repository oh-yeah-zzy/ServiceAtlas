<template>
  <div class="topology-page">
    <div class="page-header">
      <h1>{{ $t('topology.title') }}</h1>
      <button class="btn btn-primary" @click="showModal = true; resetForm()">
        + {{ $t('topology.addDependency') }}
      </button>
    </div>

    <div class="topology-container">
      <div id="topology-graph" ref="graphContainer"></div>
    </div>

    <div class="topology-legend">
      <div class="legend-item">
        <span class="legend-dot gateway"></span>
        <span>{{ $t('common.gateway') }}</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot healthy"></span>
        <span>{{ $t('common.healthy') }}</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot unhealthy"></span>
        <span>{{ $t('common.unhealthy') }}</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot unknown"></span>
        <span>{{ $t('common.unknown') }}</span>
      </div>
    </div>

    <div v-if="!hasData" class="empty-message">
      {{ $t('topology.noDependencies') }}
    </div>

    <!-- 添加依赖模态框 -->
    <div v-if="showModal" class="modal show" @click.self="showModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h2>{{ $t('topology.addDependency') }}</h2>
          <button class="close-btn" @click="showModal = false">&times;</button>
        </div>
        <form @submit.prevent="addDependency">
          <div class="form-group">
            <label>{{ $t('topology.sourceService') }} *</label>
            <select v-model="form.source_service_id" required>
              <option value="">{{ $t('topology.selectService') }}</option>
              <option v-for="service in services" :key="service.id" :value="service.id">
                {{ service.name }} ({{ service.id }})
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>{{ $t('topology.targetService') }} *</label>
            <select v-model="form.target_service_id" required>
              <option value="">{{ $t('topology.selectService') }}</option>
              <option v-for="service in services" :key="service.id" :value="service.id">
                {{ service.name }} ({{ service.id }})
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>{{ $t('topology.description') }}</label>
            <input v-model="form.description" type="text" :placeholder="$t('topology.descriptionPlaceholder')">
          </div>
          <div class="form-actions">
            <button type="button" class="btn btn-secondary" @click="showModal = false">
              {{ $t('common.cancel') }}
            </button>
            <button type="submit" class="btn btn-primary">
              {{ $t('common.add') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { servicesApi, dependenciesApi } from '@/api'
import * as d3 from 'd3'

const { t } = useI18n()

const graphContainer = ref(null)
const hasData = ref(true)
const showModal = ref(false)
const services = ref([])
let dependencies = []
let simulation = null

const form = reactive({
  source_service_id: '',
  target_service_id: '',
  description: ''
})

const resetForm = () => {
  form.source_service_id = ''
  form.target_service_id = ''
  form.description = ''
}

const loadData = async () => {
  try {
    const [servicesData, depsData] = await Promise.all([
      servicesApi.getAll(),
      dependenciesApi.getAll()
    ])
    services.value = servicesData
    dependencies = depsData
    hasData.value = services.value.length > 0
    await nextTick()
    renderGraph()
  } catch (error) {
    console.error('Failed to load topology data:', error)
    hasData.value = false
  }
}

const addDependency = async () => {
  try {
    await dependenciesApi.create({
      source_service_id: form.source_service_id,
      target_service_id: form.target_service_id,
      description: form.description || null
    })
    alert(t('topology.addSuccess'))
    showModal.value = false
    resetForm()
    await loadData()
  } catch (error) {
    alert(`${t('topology.addFailed')}: ${error.message}`)
  }
}

const getNodeColor = (node) => {
  if (node.is_gateway) return '#9b59b6'  // 紫色 - 网关
  switch (node.status) {
    case 'healthy': return '#2ecc71'     // 绿色 - 健康
    case 'unhealthy': return '#e74c3c'   // 红色 - 异常
    default: return '#95a5a6'            // 灰色 - 未知
  }
}

const renderGraph = () => {
  if (!graphContainer.value || services.value.length === 0) return

  const container = graphContainer.value
  const width = container.clientWidth
  const height = container.clientHeight || 500

  // 清空容器和旧的 simulation
  container.innerHTML = ''
  if (simulation) {
    simulation.stop()
  }

  // 准备节点和边数据
  const nodes = services.value.map(s => ({ ...s }))
  const edges = dependencies.map(dep => ({
    source: dep.service_id || dep.source_service_id,
    target: dep.depends_on_id || dep.target_service_id
  })).filter(e => {
    // 确保源和目标节点都存在
    return nodes.some(n => n.id === e.source) && nodes.some(n => n.id === e.target)
  })

  // 创建 SVG
  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)

  // 定义箭头标记
  svg.append('defs').append('marker')
    .attr('id', 'arrowhead')
    .attr('viewBox', '-0 -5 10 10')
    .attr('refX', 25)
    .attr('refY', 0)
    .attr('orient', 'auto')
    .attr('markerWidth', 8)
    .attr('markerHeight', 8)
    .append('path')
    .attr('d', 'M 0,-5 L 10,0 L 0,5')
    .attr('fill', '#999')

  // 创建力导向图
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges)
      .id(d => d.id)
      .distance(150))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(40))

  // 绘制连线
  const link = svg.append('g')
    .selectAll('line')
    .data(edges)
    .join('line')
    .attr('stroke', '#999')
    .attr('stroke-width', 2)
    .attr('marker-end', 'url(#arrowhead)')

  // 绘制节点组
  const node = svg.append('g')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended))

  // 节点圆形
  node.append('circle')
    .attr('r', 20)
    .attr('fill', d => getNodeColor(d))
    .attr('stroke', 'white')
    .attr('stroke-width', 3)

  // 节点标签
  node.append('text')
    .attr('dy', 35)
    .attr('text-anchor', 'middle')
    .attr('fill', '#333')
    .attr('font-size', '12px')
    .text(d => d.name)

  // 节点半径和边距
  const nodeRadius = 20
  const padding = 40

  // 更新位置（添加边界约束）
  simulation.on('tick', () => {
    // 限制节点在 SVG 边界内
    nodes.forEach(d => {
      d.x = Math.max(nodeRadius + padding, Math.min(width - nodeRadius - padding, d.x))
      d.y = Math.max(nodeRadius + padding, Math.min(height - nodeRadius - padding, d.y))
    })

    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    node.attr('transform', d => `translate(${d.x},${d.y})`)
  })

  function dragstarted(event) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    event.subject.fx = event.subject.x
    event.subject.fy = event.subject.y
  }

  function dragged(event) {
    event.subject.fx = event.x
    event.subject.fy = event.y
  }

  function dragended(event) {
    if (!event.active) simulation.alphaTarget(0)
    event.subject.fx = null
    event.subject.fy = null
  }
}

const handleResize = () => {
  renderGraph()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (simulation) {
    simulation.stop()
  }
})
</script>

<style scoped>
.topology-page .page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.topology-page h1 {
  color: #2c3e50;
  margin: 0;
}

.topology-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  min-height: 500px;
  margin-bottom: 1rem;
}

#topology-graph {
  width: 100%;
  height: 500px;
}

.topology-legend {
  display: flex;
  gap: 2rem;
  justify-content: center;
  padding: 1rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #7f8c8d;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-dot.gateway { background: #9b59b6; }
.legend-dot.healthy { background: #2ecc71; }
.legend-dot.unhealthy { background: #e74c3c; }
.legend-dot.unknown { background: #95a5a6; }

.empty-message {
  text-align: center;
  padding: 3rem;
  color: #7f8c8d;
}

/* 模态框 */
.modal {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  z-index: 1000;
  align-items: center;
  justify-content: center;
}

.modal.show {
  display: flex;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #ecf0f1;
}

.modal-header h2 {
  font-size: 1.25rem;
  color: #2c3e50;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #7f8c8d;
}

form {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #2c3e50;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #dfe6e9;
  border-radius: 6px;
  font-size: 1rem;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #ecf0f1;
}

.btn {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  text-decoration: none;
  transition: all 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-secondary {
  background: #ecf0f1;
  color: #2c3e50;
}
</style>
