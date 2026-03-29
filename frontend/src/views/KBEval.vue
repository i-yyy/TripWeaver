<template>
  <div class="brand-page">
    <div class="brand-shell aside-stack">
      <section class="glass-panel kb-panel">
        <div class="glass-toolbar">
          <div class="section-heading">
            <span class="page-kicker">RAG 评测</span>
            <h1 class="page-title kb-title">观察知识库召回和重排的表现，看看推荐依据是否更聪明了</h1>
            <p class="page-subtitle">这个页面主要用来做调试和评估，适合对比不同查询词、标签过滤和重排模式的效果。</p>
          </div>
          <div class="toolbar-group">
            <a-button @click="goPlanner">返回旅行规划</a-button>
            <a-button type="primary" :loading="loading" @click="runEvaluation">开始评测</a-button>
          </div>
        </div>

        <a-form layout="vertical">
          <a-row :gutter="16">
            <a-col :xs="24" :md="12">
              <a-form-item label="查询词">
                <a-input v-model:value="formData.query" placeholder="例如：北京 雨天 亲子 室内 博物馆 科技馆" allow-clear />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="6">
              <a-form-item label="城市过滤">
                <a-input v-model:value="formData.city" placeholder="例如：beijing" allow-clear />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="6">
              <a-form-item label="Top-K">
                <a-input-number v-model:value="formData.top_k" :min="1" :max="20" />
              </a-form-item>
            </a-col>
          </a-row>

          <a-row :gutter="16">
            <a-col :xs="24" :md="8">
              <a-form-item label="标签过滤（逗号分隔）">
                <a-input v-model:value="formData.tags" placeholder="例如：rainy_day,family,museum" allow-clear />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="8">
              <a-form-item label="人群过滤（逗号分隔）">
                <a-input v-model:value="formData.crowd_type" placeholder="例如：family,couple" allow-clear />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="8">
              <a-form-item label="预算等级">
                <a-select v-model:value="formData.budget_level" allow-clear>
                  <a-select-option value="low">低预算</a-select-option>
                  <a-select-option value="medium">中预算</a-select-option>
                  <a-select-option value="high">高预算</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>

          <a-row :gutter="16">
            <a-col :xs="24" :md="18">
              <a-form-item label="期望命中关键词（逗号分隔）">
                <a-input v-model:value="formData.expected_terms_text" placeholder="例如：rainy_day,family,museum,室内,亲子" allow-clear />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="6">
              <a-form-item label="启用重排">
                <a-switch v-model:checked="formData.rerank" checked-children="开" un-checked-children="关" />
              </a-form-item>
            </a-col>
          </a-row>
        </a-form>

        <div class="section-heading" style="margin-top: 10px">
          <h3>快捷用例</h3>
          <p>如果你只是想快速验证，可以直接点下面的样例。</p>
        </div>
        <div class="toolbar-group">
          <a-button @click="applyQuickCase('beijing_rainy_family')">北京雨天亲子</a-button>
          <a-button @click="applyQuickCase('shanghai_citywalk_food')">上海 citywalk 美食</a-button>
          <a-button @click="applyQuickCase('beijing_light_family')">北京轻松家庭出行</a-button>
        </div>
      </section>

      <section v-if="result" class="glass-panel glass-panel--soft kb-panel">
        <div class="section-heading">
          <h2>评测指标</h2>
          <p>{{ summaryText }}</p>
        </div>
        <div class="brand-stat-grid">
          <div class="brand-stat">
            <span>召回数量</span>
            <strong>{{ result.metrics.recall_count }}</strong>
          </div>
          <div class="brand-stat">
            <span>最终数量</span>
            <strong>{{ result.metrics.final_count }}</strong>
          </div>
          <div class="brand-stat">
            <span>期望命中率</span>
            <strong>{{ toPercent(result.metrics.expected_hit_rate) }}%</strong>
          </div>
          <div class="brand-stat">
            <span>Top1 增益</span>
            <strong>{{ result.metrics.top1_gain.toFixed(4) }}</strong>
          </div>
          <div class="brand-stat">
            <span>平均分</span>
            <strong>{{ result.metrics.score_avg.toFixed(4) }}</strong>
          </div>
          <div class="brand-stat">
            <span>最高分 / 最低分</span>
            <strong>{{ result.metrics.score_max.toFixed(4) }} / {{ result.metrics.score_min.toFixed(4) }}</strong>
          </div>
        </div>
      </section>

      <section v-if="result" class="glass-panel glass-panel--soft kb-panel">
        <div class="section-heading">
          <h2>Top-K 明细</h2>
          <p>下面可以看到每条结果的综合分、基础分、重排分和命中文本。</p>
        </div>
        <a-table :columns="columns" :data-source="result.items" row-key="rank" :pagination="false">
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'score'">{{ Number(record.score).toFixed(4) }}</template>
            <template v-else-if="column.dataIndex === 'base_score'">{{ Number(record.base_score).toFixed(4) }}</template>
            <template v-else-if="column.dataIndex === 'rerank_score'">{{ Number(record.rerank_score).toFixed(4) }}</template>
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
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import { evaluateKnowledgeBase } from '@/services/api'
import type { KBEvaluateResponse } from '@/types'

type QuickCaseType = 'beijing_rainy_family' | 'shanghai_citywalk_food' | 'beijing_light_family'

const router = useRouter()
const loading = ref(false)
const result = ref<KBEvaluateResponse | null>(null)

const formData = reactive({
  query: '北京 雨天 亲子 室内 博物馆 科技馆',
  city: 'beijing',
  top_k: 6,
  tags: 'rainy_day,family,museum',
  crowd_type: 'family',
  budget_level: 'medium',
  expected_terms_text: 'rainy_day,family,museum,室内,亲子',
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

const summaryText = computed(() => {
  if (!result.value) return '暂无评测数据'
  const gain = result.value.metrics.top1_gain
  const rerankMode = result.value.metrics.rerank_mode
  if (gain > 0) {
    return `重排后 Top1 提升 ${gain.toFixed(4)}，当前重排模式为 ${rerankMode}。`
  }
  if (gain < 0) {
    return `重排后 Top1 下降 ${Math.abs(gain).toFixed(4)}，建议检查查询词、标签过滤和知识库内容。`
  }
  return `重排与基础检索的 Top1 持平，当前重排模式为 ${rerankMode}。`
})

const goPlanner = () => router.push('/planner')
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
    formData.city = 'beijing'
    formData.tags = 'rainy_day,family,museum'
    formData.crowd_type = 'family'
    formData.budget_level = 'medium'
    formData.expected_terms_text = 'rainy_day,family,museum,室内,亲子'
    return
  }
  if (type === 'shanghai_citywalk_food') {
    formData.query = '上海 citywalk 美食 夜景 步行 地铁'
    formData.city = 'shanghai'
    formData.tags = 'citywalk,food,night_view'
    formData.crowd_type = 'friends,couple'
    formData.budget_level = 'medium'
    formData.expected_terms_text = 'citywalk,food,night_view,步行,美食'
    return
  }
  formData.query = '北京 家庭 公共交通 轻松 低强度 行程'
  formData.city = 'beijing'
  formData.tags = 'family'
  formData.crowd_type = 'family'
  formData.budget_level = 'medium'
  formData.expected_terms_text = 'family,public_transit,低强度,亲子'
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
      city: formData.city.trim() || null,
      top_k: formData.top_k,
      tags: formData.tags.trim() || null,
      crowd_type: formData.crowd_type.trim() || null,
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
</script>

<style scoped>
.kb-panel {
  padding: 28px;
}

.kb-title {
  font-size: clamp(34px, 4.2vw, 52px);
}

.kb-snippet {
  color: var(--brand-text);
  line-height: 1.75;
}

@media (max-width: 960px) {
  .kb-panel {
    padding: 22px;
  }
}
</style>
