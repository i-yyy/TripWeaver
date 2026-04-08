<template>
  <div class="brand-page">
    <div class="brand-shell aside-stack">
      <section class="glass-panel kb-panel">
        <div class="glass-toolbar">
          <div class="section-heading">
            <span class="page-kicker">🧪 RAG评测</span>
            <h1 class="page-title kb-title">查看知识库召回、重排与推荐依据表现</h1>
            <div class="dev-flag">开发者视图</div>
            <p class="page-subtitle">这个页面主要用来做调试和评估，适合对比不同查询词、标签过滤和重排模式的效果</p>
          </div>
        </div>

        <a-form layout="vertical" class="kb-form">
          <div class="kb-rerank-row kb-rerank-row--top">
            <span class="kb-rerank-label">⚙️ 启用重排</span>
            <a-switch
              v-model:checked="formData.rerank"
              class="kb-rerank-switch"
              checked-children="开"
              un-checked-children="关"
            />
          </div>

          <div class="kb-form-grid">
            <a-form-item label="🔎 查询词" class="kb-form-item">
              <a-input v-model:value="formData.query" placeholder="例如：北京 雨天 亲子 室内 博物馆 科技馆" allow-clear />
            </a-form-item>

            <a-form-item label="🏙️ 城市过滤" class="kb-form-item">
              <a-input v-model:value="formData.city" placeholder="例如：北京" allow-clear />
            </a-form-item>

            <a-form-item label="🔢 返回条数" class="kb-form-item">
              <a-input-number v-model:value="formData.top_k" :min="1" :max="20" class="kb-full-control" />
            </a-form-item>

            <a-form-item label="🏷️ 标签过滤（逗号分隔）" class="kb-form-item">
              <a-input v-model:value="formData.tags" placeholder="例如：雨天,亲子,博物馆" allow-clear />
            </a-form-item>

            <a-form-item label="👥 人群过滤（逗号分隔）" class="kb-form-item">
              <a-input v-model:value="formData.crowd_type" placeholder="例如：家庭,情侣" allow-clear />
            </a-form-item>

            <a-form-item label="💰 预算等级" class="kb-form-item">
              <a-select v-model:value="formData.budget_level" allow-clear>
                <a-select-option value="low">低预算</a-select-option>
                <a-select-option value="medium">中预算</a-select-option>
                <a-select-option value="high">高预算</a-select-option>
              </a-select>
            </a-form-item>

            <a-form-item label="🎯 期望命中关键词（逗号分隔）" class="kb-form-item">
              <a-input v-model:value="formData.expected_terms_text" placeholder="例如：雨天,亲子,博物馆,室内" allow-clear />
            </a-form-item>
          </div>
        </a-form>

        <div class="section-heading" style="margin-top: 10px">
          <h3>⚡ 快捷用例</h3>
          <p>如果你只是想快速验证，可以直接点下面的样例</p>
        </div>
        <div class="toolbar-group">
          <a-button @click="applyQuickCase('beijing_rainy_family')">北京雨天亲子</a-button>
          <a-button @click="applyQuickCase('shanghai_citywalk_food')">上海城市漫游美食</a-button>
          <a-button @click="applyQuickCase('beijing_light_family')">北京轻松家庭出行</a-button>
        </div>

        <div class="kb-submit-row">
          <a-button type="primary" size="large" class="kb-submit-button" :loading="loading" @click="runEvaluation">
            🚀 开始评测
          </a-button>
        </div>
      </section>

      <section v-if="result" class="glass-panel glass-panel--soft kb-panel">
        <div class="section-heading">
          <h2>📊 评测指标</h2>
          <p>{{ summaryText }}</p>
        </div>
        <div class="brand-stat-grid">
          <div class="brand-stat">
            <span>📥 召回数量</span>
            <strong>{{ result.metrics.recall_count }}</strong>
          </div>
          <div class="brand-stat">
            <span>📌 最终数量</span>
            <strong>{{ result.metrics.final_count }}</strong>
          </div>
          <div class="brand-stat">
            <span>🎯 期望命中率</span>
            <strong>{{ toPercent(result.metrics.expected_hit_rate) }}%</strong>
          </div>
          <div class="brand-stat">
            <span>🚀 首位结果增益</span>
            <strong>{{ result.metrics.top1_gain.toFixed(4) }}</strong>
          </div>
          <div class="brand-stat">
            <span>📈 平均分</span>
            <strong>{{ result.metrics.score_avg.toFixed(4) }}</strong>
          </div>
          <div class="brand-stat">
            <span>📉 最高分 / 最低分</span>
            <strong>{{ result.metrics.score_max.toFixed(4) }} / {{ result.metrics.score_min.toFixed(4) }}</strong>
          </div>
        </div>
      </section>

      <section v-if="result" class="glass-panel glass-panel--soft kb-panel">
        <div class="section-heading">
          <h2>📚 前列结果明细</h2>
          <p>下面可以看到每条结果的综合分、基础分、重排分和命中文本</p>
        </div>
        <a-table :columns="columns" :data-source="result.items" row-key="rank" :pagination="false">
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'score'">{{ Number(record.score).toFixed(4) }}</template>
            <template v-else-if="column.dataIndex === 'base_score'">{{ Number(record.base_score).toFixed(4) }}</template>
            <template v-else-if="column.dataIndex === 'rerank_score'">{{ Number(record.rerank_score).toFixed(4) }}</template>
            <template v-else-if="column.dataIndex === 'rerank_mode'">{{ rerankModeLabel(record.rerank_mode) }}</template>
            <template v-else-if="column.dataIndex === 'city_hint'">{{ cityHintLabel(record.city_hint) }}</template>
            <template v-else-if="column.dataIndex === 'source_doc'">{{ formatSourceDoc(record.source_doc) }}</template>
            <template v-else-if="column.dataIndex === 'snippet'">
              <span class="kb-snippet">{{ record.snippet }}</span>
            </template>
          </template>
        </a-table>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'

import { evaluateKnowledgeBase, getCurrentUser } from '@/services/api'
import type { KBEvaluateResponse } from '@/types'
import { updateStoredUser, useAuthState } from '@/utils/auth'

type QuickCaseType = 'beijing_rainy_family' | 'shanghai_citywalk_food' | 'beijing_light_family'

const router = useRouter()
const authState = useAuthState()
const loading = ref(false)
const result = ref<KBEvaluateResponse | null>(null)

const formData = reactive({
  query: '北京 雨天 亲子 室内 博物馆 科技馆',
  city: '北京',
  top_k: 6,
  tags: '雨天,亲子,博物馆',
  crowd_type: '家庭',
  budget_level: 'medium',
  expected_terms_text: '雨天,亲子,博物馆,室内',
  rerank: true,
})

const columns = [
  { title: '排名', dataIndex: 'rank', key: 'rank', width: 70 },
  { title: '综合分', dataIndex: 'score', key: 'score', width: 110 },
  { title: '基础分', dataIndex: 'base_score', key: 'base_score', width: 110 },
  { title: '重排分', dataIndex: 'rerank_score', key: 'rerank_score', width: 110 },
  { title: '模式', dataIndex: 'rerank_mode', key: 'rerank_mode', width: 120 },
  { title: '城市', dataIndex: 'city_hint', key: 'city_hint', width: 100 },
  { title: '来源文档', dataIndex: 'source_doc', key: 'source_doc', width: 180 },
  { title: '命中片段', dataIndex: 'snippet', key: 'snippet' },
]

const expectedTerms = computed(() =>
  formData.expected_terms_text
    .split(',')
    .map((token) => token.trim())
    .filter(Boolean),
)

const cityMappings: Record<string, string> = {
  北京: 'beijing',
  上海: 'shanghai',
  杭州: 'hangzhou',
  南京: 'nanjing',
  武汉: 'wuhan',
  黄山: 'huangshan',
  黄山市: 'huangshan',
}

const keywordMappings: Record<string, string> = {
  雨天: 'rainy_day',
  亲子: 'family',
  家庭: 'family',
  情侣: 'couple',
  朋友: 'friends',
  博物馆: 'museum',
  城市漫游: 'citywalk',
  美食: 'food',
  夜景: 'night_view',
  公共交通: 'public_transit',
}

const normalizeCityFilter = (value: string) => {
  const text = value.trim()
  if (!text) return null
  return cityMappings[text] || text.toLowerCase()
}

const normalizeCsvValues = (value: string) =>
  value
    .split(',')
    .map((token) => token.trim())
    .filter(Boolean)
    .map((token) => keywordMappings[token] || token)
    .join(',')

const rerankModeLabel = (value?: string) => {
  const text = String(value || '').toLowerCase()
  if (!text) return '未标注'
  if (text.includes('off') || text.includes('none')) return '未启用重排'
  if (text.includes('cross')) return '交叉重排'
  if (text.includes('hybrid')) return '混合重排'
  if (text.includes('semantic')) return '语义重排'
  return value || '未标注'
}

const cityHintLabel = (value?: string) => {
  const text = String(value || '').trim().toLowerCase()
  const reverseMappings: Record<string, string> = {
    beijing: '北京',
    shanghai: '上海',
    hangzhou: '杭州',
    nanjing: '南京',
    wuhan: '武汉',
    huangshan: '黄山',
  }
  return reverseMappings[text] || value || '-'
}

const summaryText = computed(() => {
  if (!result.value) return '暂无评测数据'
  const gain = result.value.metrics.top1_gain
  const rerankMode = rerankModeLabel(result.value.metrics.rerank_mode)
  if (gain > 0) {
    return `重排后首位结果提升 ${gain.toFixed(4)}，当前重排模式为 ${rerankMode}`
  }
  if (gain < 0) {
    return `重排后首位结果下降 ${Math.abs(gain).toFixed(4)}，建议检查查询词、标签过滤和知识库内容`
  }
  return `重排与基础检索的首位结果持平，当前重排模式为 ${rerankMode}`
})

const toPercent = (value: number) => Number(value || 0).toFixed(2)

const formatSourceDoc = (docPath?: string) => {
  if (!docPath) return '-'
  const normalized = docPath.replace(/\\/g, '/')
  const segments = normalized.split('/')
  return segments[segments.length - 1] || docPath
}

const applyQuickCase = (type: QuickCaseType) => {
  if (type === 'beijing_rainy_family') {
    formData.query = '北京 雨天 亲子 室内 博物馆 科技馆'
    formData.city = '北京'
    formData.tags = '雨天,亲子,博物馆'
    formData.crowd_type = '家庭'
    formData.budget_level = 'medium'
    formData.expected_terms_text = '雨天,亲子,博物馆,室内'
    return
  }
  if (type === 'shanghai_citywalk_food') {
    formData.query = '上海 城市漫游 美食 夜景 步行 地铁'
    formData.city = '上海'
    formData.tags = '城市漫游,美食,夜景'
    formData.crowd_type = '朋友,情侣'
    formData.budget_level = 'medium'
    formData.expected_terms_text = '城市漫游,美食,夜景,步行'
    return
  }
  formData.query = '北京 家庭 公共交通 轻松 低强度 行程'
  formData.city = '北京'
  formData.tags = '家庭'
  formData.crowd_type = '家庭'
  formData.budget_level = 'medium'
  formData.expected_terms_text = '家庭,公共交通,低强度,亲子'
}

const runEvaluation = async () => {
  if (!formData.query.trim()) {
    message.error('查询词不能为空')
    return
  }

  loading.value = true
  try {
    result.value = await evaluateKnowledgeBase({
      query: formData.query.trim(),
      city: normalizeCityFilter(formData.city),
      top_k: formData.top_k,
      tags: normalizeCsvValues(formData.tags) || null,
      crowd_type: normalizeCsvValues(formData.crowd_type) || null,
      budget_level: formData.budget_level || null,
      expected_terms: expectedTerms.value,
      rerank: formData.rerank,
    })
    message.success('评测完成')
  } catch (error: any) {
    message.error(error.message || '评测失败')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  if (authState.user?.is_developer === true) {
    return
  }

  try {
    const response = await getCurrentUser()
    if (response.success && response.data) {
      updateStoredUser(response.data)
      if (response.data.is_developer) {
        return
      }
    }
  } catch {
    // Ignore here and redirect below.
  }

  message.warning('这个页面仅对开发者开放')
  router.replace('/planner')
})
</script>

<style scoped>
.kb-panel {
  padding: 28px;
}

.kb-title {
  font-size: clamp(34px, 4.2vw, 52px);
}

.dev-flag {
  display: inline-flex;
  align-items: center;
  margin: 8px 0 2px;
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(29, 93, 155, 0.12);
  border: 1px solid rgba(29, 93, 155, 0.22);
  color: #1d5d9b;
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.05em;
}

.kb-form {
  display: block;
}

.kb-form-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.kb-form-item {
  margin-bottom: 0;
}

.kb-full-control {
  width: 100%;
}

.kb-rerank-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 0;
}

.kb-rerank-label {
  color: var(--brand-text);
  font-size: 16px;
  font-weight: 700;
}

.kb-rerank-switch {
  flex: 0 0 auto;
}

.kb-snippet {
  color: var(--brand-text);
  line-height: 1.75;
}

.kb-submit-row {
  display: flex;
  justify-content: center;
  margin-top: 22px;
}

.kb-submit-button {
  min-width: 240px;
  height: 52px;
  border-radius: 18px;
  font-size: 16px;
  font-weight: 700;
  box-shadow: 0 18px 36px rgba(71, 143, 255, 0.22);
}

@media (max-width: 960px) {
  .kb-panel {
    padding: 22px;
  }

  .kb-form-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .kb-rerank-row {
    margin-top: 12px;
  }

  .kb-submit-button {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .kb-form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
