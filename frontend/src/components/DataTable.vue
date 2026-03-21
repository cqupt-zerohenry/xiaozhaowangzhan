<template>
  <div class="data-table">
    <div v-if="columns.length" class="data-head" :style="{ gridTemplateColumns: gridTemplate }">
      <span
        v-for="col in columns"
        :key="col.key"
        :style="{ textAlign: col.align || 'left' }"
      >
        {{ col.label }}
      </span>
    </div>

    <div v-if="loading" class="data-loading">
      <div
        v-for="n in loadingRows"
        :key="`table-skeleton-${n}`"
        class="data-skeleton-row"
        :style="{ gridTemplateColumns: gridTemplate }"
      >
        <div v-for="col in columns" :key="`table-skeleton-${n}-${col.key}`" class="skeleton data-skeleton-cell"></div>
      </div>
    </div>

    <div v-else-if="!rows.length" class="data-empty mono">{{ emptyText }}</div>

    <div v-else class="data-body">
      <div
        v-for="(row, index) in rows"
        :key="resolveRowKey(row, index)"
        class="data-row"
        :class="[rowClass, { clickable }]"
        @click="handleRowClick(row, index)"
      >
        <slot name="row" :row="row" :index="index" :gridTemplate="gridTemplate">
          <div class="mono">{{ row }}</div>
        </slot>
      </div>
    </div>

    <div v-if="showPager && totalPages > 1" class="data-pager">
      <button type="button" class="btn btn-outline" :disabled="page <= 1" @click="emit('update:page', page - 1)">上一页</button>
      <span class="mono">第 {{ page }} 页 / 共 {{ totalPages }} 页</span>
      <button type="button" class="btn btn-outline" :disabled="page >= totalPages" @click="emit('update:page', page + 1)">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  columns: {
    type: Array,
    default: () => []
  },
  rows: {
    type: Array,
    default: () => []
  },
  rowKey: {
    type: String,
    default: 'id'
  },
  loading: {
    type: Boolean,
    default: false
  },
  loadingRows: {
    type: Number,
    default: 4
  },
  emptyText: {
    type: String,
    default: '暂无数据'
  },
  rowClass: {
    type: String,
    default: ''
  },
  clickable: {
    type: Boolean,
    default: false
  },
  page: {
    type: Number,
    default: 1
  },
  totalPages: {
    type: Number,
    default: 1
  },
  showPager: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['row-click', 'update:page']);

const gridTemplate = computed(() => {
  if (!props.columns.length) return '1fr';
  return props.columns.map((col) => col.width || '1fr').join(' ');
});

function resolveRowKey(row, index) {
  const key = row?.[props.rowKey];
  if (key !== undefined && key !== null && key !== '') return key;
  return index;
}

function handleRowClick(row, index) {
  if (!props.clickable) return;
  emit('row-click', { row, index });
}
</script>

<style scoped>
.data-table {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.data-head {
  display: grid;
  gap: 10px;
  padding: 0 10px;
  font-size: 12px;
  color: #6f847b;
}

.data-head span {
  white-space: nowrap;
}

.data-loading {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.data-skeleton-row {
  display: grid;
  gap: 10px;
  border: 1px dashed var(--line);
  border-radius: 12px;
  padding: 12px;
}

.data-skeleton-cell {
  min-height: 16px;
}

.data-empty {
  padding: 12px 0;
  color: #7f918a;
}

.data-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.data-row {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 10px;
  background: #fff;
}

.data-row.clickable {
  cursor: pointer;
  transition: background 0.15s ease;
}

.data-row.clickable:hover {
  background: rgba(24, 160, 88, 0.05);
}

.data-pager {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

@media (max-width: 900px) {
  .data-head {
    display: none;
  }
}
</style>
