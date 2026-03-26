<template>
  <div class="kb-eval-page">
    <a-card class="eval-form-card" :bordered="false">
      <div class="title-row">
        <div>
          <h2>RAG 评测面板</h2>
          <p class="subtitle">对比知识库召回基线与重排结果，观察命中率和分数变化。</p>
        </div>
        <a-space>
          <a-button @click="goHome">返回行程页</a-button>
          <a-button type="primary" :loading="loading" @click="runEvaluation">开始评测</a-button>
        </a-space>
      </div>

      <a-form layout="vertical">
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="查询词">
              <a-input
                v-model:value="formData.query"
                placeholder="例如：北京 雨天 亲子 室内 博物馆"
                allow-clear
              />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="城市过滤">
              <a-input v-model:value="formData.city" placeholder="例如：beijing" allow-clear />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="Top-K">
              <a-input-number v-model:value="formData.top_k" :min="1" :max="20" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="12">
          <a-col :span="8">
            <a-form-item label="标签过滤（逗号分隔）">
              <a-input v-model:value="formData.tags" placeholder="如：rainy_day,family,museum" allow-clear />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="人群过滤（逗号分隔）">
              <a-input v-model:value="formData.crowd_type" placeholder="如：family,couple" allow-clear />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="预算等级">
              <a-select v-model:value="formData.budget_level" allow-clear>
                <a-select-option value="low">低预算</a-select-option>
                <a-select-option value="medium">中预算</a-select-option>
                <a-select-option value="high">高预算</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="12">
          <a-col :span="18">
            <a-form-item label="期望命中关键词（逗号分隔）">
              <a-input
                v-model:value="formData.expected_terms_text"
                placeholder="如：rainy_day,family,museum,室内,亲子"
                allow-clear
              />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="启用重排">
              <a-switch v-model:checked="formData.rerank" checked-children="开" un-checked-children="关" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>

      <a-divider orientation="left">快捷用例</a-divider>
      <a-space wrap>
        <a-button @click="applyQuickCase('beijing_rainy_family')">北京雨天亲子</a-button>
        <a-button @click="applyQuickCase('shanghai_citywalk_food')">上海 citywalk 美食</a-button>
        <a-button @click="applyQuickCase('beijing_light_family')">北京轻松家庭出行</a-button>
      </a-space>
    </a-card>

    <a-card v-if="result" class="metrics-card" :bordered="false" title="评测指标">
      <a-row :gutter="12">
        <a-col :span="6">
          <a-statistic title="召回数量" :value="result.metrics.recall_count" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="最终数量" :value="result.metrics.final_count" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="期望命中率" :value="toPercent(result.metrics.expected_hit_rate)" suffix="%" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="Top1 增益" :value="result.metrics.top1_gain" :precision="4" />
        </a-col>
      </a-row>

      <a-row :gutter="12" style="margin-top: 12px">
        <a-col :span="8">
          <a-statistic title="平均分" :value="result.metrics.score_avg" :precision="4" />
        </a-col>
        <a-col :span="8">
          <a-statistic title="最高分" :value="result.metrics.score_max" :precision="4" />
        </a-col>
        <a-col :span="8">
          <a-statistic title="最低分" :value="result.metrics.score_min" :precision="4" />
        </a-col>
      </a-row>

      <a-alert
        style="margin-top: 16px"
        :type="result.metrics.top1_gain >= 0 ? 'success' : 'warning'"
        :message="summaryText"
        show-icon
      />
    </a-card>

    <a-card v-if="result" class="table-card" :bordered="false" title="Top-K 明细">
      <a-table :columns="columns" :data-source="result.items" row-key="rank" :pagination="false">
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'score'">
            {{ Number(record.score).toFixed(4) }}
          </template>
          <template v-else-if="column.dataIndex === 'base_score'">
            {{ Number(record.base_score).toFixed(4) }}
          </template>
          <template v-else-if="column.dataIndex === 'rerank_score'">
            {{ Number(record.rerank_score).toFixed(4) }}
          </template>
          <template v-else-if="column.dataIndex === 'source_doc'">
            {{ formatSourceDoc(record.source_doc) }}
          </template>
          <template v-else-if="column.dataIndex === 'snippet'">
            <span class="snippet">{{ record.snippet }}</span>
          </template>
        </template>
      </a-table>
    </a-card>
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
  { title: '综合分', dataIndex: 'score', key: 'score', width: 100 },
  { title: '基线分', dataIndex: 'base_score', key: 'base_score', width: 100 },
  { title: '重排分', dataIndex: 'rerank_score', key: 'rerank_score', width: 100 },
  { title: '模式', dataIndex: 'rerank_mode', key: 'rerank_mode', width: 110 },
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
  const metrics = result.value.metrics
  const gain = metrics.top1_gain
  if (gain > 0) {
    return `重排后 Top1 提升 ${gain.toFixed(4)}，当前重排模式：${metrics.rerank_mode}。`
  }
  if (gain < 0) {
    return `重排后 Top1 下降 ${Math.abs(gain).toFixed(4)}，建议检查评测查询词与知识库标签。`
  }
  return `重排与基线 Top1 持平，当前重排模式：${metrics.rerank_mode}。`
})

const goHome = () => router.push('/')

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
.kb-eval-page {
  min-height: 100vh;
  background: linear-gradient(155deg, #f4fbff 0%, #eef4ff 42%, #eef7f5 100%);
  padding: 8px;
}

.eval-form-card,
.metrics-card,
.table-card {
  margin-bottom: 16px;
}

.title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.subtitle {
  margin: 0;
  color: #5f6c80;
}

.snippet {
  color: #243446;
}

@media (max-width: 900px) {
  .title-row {
    flex-direction: column;
  }
}
</style>
