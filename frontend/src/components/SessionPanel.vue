<template>
  <div class="session-panel">
    <div class="panel-header">
      <div class="panel-title">
        <el-icon :size="16"><Clock /></el-icon>
        对话历史
      </div>
      <el-button type="primary" size="small" round @click="$emit('new')">
        <el-icon><Plus /></el-icon>
        新对话
      </el-button>
    </div>

    <div class="session-list">
      <div
        v-for="session in sessions"
        :key="session.id"
        :class="['session-item', { active: currentSessionId === session.id }]"
        @click="$emit('select', session.id)"
      >
        <div class="session-main">
          <div class="session-title">{{ session.title || '新对话' }}</div>
          <div class="session-meta">{{ session.message_count }}条消息</div>
        </div>
        <el-button
          type="danger"
          size="small"
          link
          class="delete-btn"
          @click.stop="$emit('delete', session.id)"
        >
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>

      <div v-if="!sessions.length" class="session-empty">
        <el-icon :size="28"><ChatDotRound /></el-icon>
        <p>还没有对话记录</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  sessions: any[]
  currentSessionId: number | null
}>()

defineEmits<{
  (e: 'select', id: number): void
  (e: 'new'): void
  (e: 'delete', id: number): void
}>()
</script>

<style scoped>
.session-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  width: 100%;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 16px;
  border-bottom: 1px solid var(--app-border);
  flex-shrink: 0;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--app-text);
  min-width: 0;
}

.session-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 10px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-radius: 12px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.15s ease;
  min-width: 0;
}

.session-item:hover {
  background: #f5f6f8;
}

.session-item.active {
  background: var(--app-primary-soft);
}

.session-main {
  flex: 1;
  min-width: 0;
}

.session-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--app-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-item.active .session-title {
  color: var(--app-primary-strong);
  font-weight: 600;
}

.session-meta {
  margin-top: 3px;
  font-size: 12px;
  color: var(--app-text-3);
}

.delete-btn {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.session-item:hover .delete-btn,
.session-item.active .delete-btn {
  opacity: 1;
}

@media (max-width: 1023.98px) {
  .delete-btn {
    opacity: 1;
  }
}

.session-empty {
  padding: 48px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--app-text-3);
  font-size: 13px;
}
</style>
