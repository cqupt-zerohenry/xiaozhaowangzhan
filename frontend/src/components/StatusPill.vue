<template>
  <span class="status-pill" :class="`tone-${tone}`">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue';
import {
  applicationStatusLabel,
  companyStatusLabel,
  verifyStatusLabel
} from '../constants/status';

const props = defineProps({
  status: {
    type: String,
    default: ''
  },
  kind: {
    type: String,
    default: 'application'
  }
});

const label = computed(() => {
  if (props.kind === 'company') return companyStatusLabel(props.status);
  if (props.kind === 'verify') return verifyStatusLabel(props.status);
  return applicationStatusLabel(props.status);
});

const tone = computed(() => {
  if (props.kind === 'company') {
    if (props.status === 'approved') return 'success';
    if (props.status === 'rejected') return 'danger';
    if (props.status === 'pending') return 'pending';
    return 'muted';
  }
  if (props.kind === 'verify') {
    if (props.status === 'approved') return 'success';
    if (props.status === 'rejected') return 'danger';
    return 'pending';
  }
  if (props.status === 'accepted') return 'success';
  if (props.status === 'rejected') return 'danger';
  if (props.status === 'withdrawn') return 'muted';
  if (props.status === 'reviewing' || props.status === 'to_contact') return 'pending';
  if (props.status === 'interview_scheduled' || props.status === 'interviewing') return 'accent';
  return 'info';
});
</script>

<style scoped>
.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid transparent;
}

.status-pill.tone-success {
  color: #0f8f59;
  background: rgba(24, 160, 88, 0.12);
  border-color: rgba(24, 160, 88, 0.28);
}

.status-pill.tone-danger {
  color: #bf3a3a;
  background: rgba(229, 62, 62, 0.12);
  border-color: rgba(229, 62, 62, 0.24);
}

.status-pill.tone-pending {
  color: #8a6400;
  background: rgba(240, 160, 32, 0.15);
  border-color: rgba(240, 160, 32, 0.26);
}

.status-pill.tone-accent {
  color: #0f8f59;
  background: rgba(24, 160, 88, 0.09);
  border-color: rgba(24, 160, 88, 0.2);
}

.status-pill.tone-info {
  color: #2e7b57;
  background: #eef8f2;
  border-color: #d5eadf;
}

.status-pill.tone-muted {
  color: #5c6f68;
  background: rgba(107, 124, 120, 0.12);
  border-color: rgba(107, 124, 120, 0.24);
}
</style>
