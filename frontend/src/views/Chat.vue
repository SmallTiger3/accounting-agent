<template>
  <div class="chat-container">
    <!-- 左侧会话列表 -->
    <div class="session-list">
      <div class="session-header">
        <h3>对话历史</h3>
        <el-button type="primary" size="small" @click="newSession">
          <el-icon><Plus /></el-icon> 新对话
        </el-button>
      </div>
      <div class="sessions">
        <div
          v-for="session in sessions"
          :key="session.id"
          :class="['session-item', { active: currentSessionId === session.id }]"
          @click="selectSession(session.id)"
        >
          <div class="session-title">{{ session.title || '新对话' }}</div>
          <div class="session-meta">
            <span>{{ session.message_count }}条消息</span>
            <el-button
              type="danger"
              size="small"
              link
              @click.stop="deleteSession(session.id)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 右侧聊天区域 -->
    <div class="chat-main">
      <div class="messages" ref="messagesContainer">
        <div v-if="messages.length === 0" class="empty-state">
          <el-icon size="64" color="#c0c4cc"><ChatDotRound /></el-icon>
          <h3>开始和AI记账助手对话</h3>
          <p>试试说："今天午餐花了35元"</p>
        </div>
        
        <div v-for="msg in messages" :key="msg.id" :class="['message', msg.role]">
          <div class="message-avatar">
            <el-avatar v-if="msg.role === 'user'" :size="36" icon="User" />
            <el-avatar v-else :size="36" style="background: #409eff">
              <el-icon><ChatDotRound /></el-icon>
            </el-avatar>
          </div>
          <div class="message-content">
            <div class="message-text" v-html="renderMarkdown(msg.content)"></div>
            <div class="message-time">{{ formatTime(msg.created_at) }}</div>
          </div>
        </div>
        
        <div v-if="sending" class="message assistant">
          <div class="message-avatar">
            <el-avatar :size="36" style="background: #409eff">
              <el-icon><ChatDotRound /></el-icon>
            </el-avatar>
          </div>
          <div class="message-content">
            <div class="message-text typing">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="input-area">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="2"
          placeholder="输入消息，例如：今天午餐花了35元"
          @keydown.enter.exact.prevent="sendMessage"
          :disabled="sending"
        />
        <el-button
          type="primary"
          :loading="sending"
          @click="sendMessage"
          :disabled="!inputText.trim()"
        >
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { chatApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import { marked } from 'marked'

const sessions = ref<any[]>([])
const messages = ref<any[]>([])
const currentSessionId = ref<number | null>(null)
const inputText = ref('')
const sending = ref(false)
const messagesContainer = ref<HTMLElement>()

onMounted(() => {
  loadSessions()
})

async function loadSessions() {
  try {
    sessions.value = await chatApi.getSessions()
  } catch (error) {
    console.error('Failed to load sessions:', error)
  }
}

async function selectSession(sessionId: number) {
  currentSessionId.value = sessionId
  try {
    messages.value = await chatApi.getMessages(sessionId)
    scrollToBottom()
  } catch (error) {
    console.error('Failed to load messages:', error)
  }
}

function newSession() {
  currentSessionId.value = null
  messages.value = []
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || sending.value) return
  
  // 添加用户消息到界面
  const userMsg = {
    id: Date.now(),
    role: 'user',
    content: text,
    created_at: new Date().toISOString(),
  }
  messages.value.push(userMsg)
  inputText.value = ''
  sending.value = true
  scrollToBottom()
  
  try {
    const response: any = await chatApi.sendMessage(text, currentSessionId.value || undefined)
    
    // 添加AI回复
    messages.value.push(response.message)
    currentSessionId.value = response.session_id
    
    // 显示预算告警
    if (response.budget_alerts?.length > 0) {
      response.budget_alerts.forEach((alert: string) => {
        ElMessage.warning(alert)
      })
    }
    
    // 刷新会话列表
    await loadSessions()
    scrollToBottom()
  } catch (error) {
    ElMessage.error('发送失败，请重试')
  } finally {
    sending.value = false
  }
}

async function deleteSession(sessionId: number) {
  try {
    await ElMessageBox.confirm('确定要删除这个对话吗？', '确认')
    await chatApi.deleteSession(sessionId)
    if (currentSessionId.value === sessionId) {
      newSession()
    }
    await loadSessions()
    ElMessage.success('已删除')
  } catch (error) {
    // 用户取消
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

function renderMarkdown(content: string) {
  return marked(content)
}

function formatTime(time: string) {
  return dayjs(time).format('HH:mm')
}
</script>

<style scoped>
.chat-container {
  display: flex;
  height: calc(100vh - 120px);
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.session-list {
  width: 280px;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
}

.session-header {
  padding: 16px;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.session-header h3 {
  margin: 0;
  font-size: 16px;
}

.sessions {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
}

.session-item:hover {
  background: #f5f7fa;
}

.session-item.active {
  background: #ecf5ff;
}

.session-title {
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.empty-state h3 {
  margin: 16px 0 8px;
  color: #606266;
}

.empty-state p {
  font-size: 14px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 70%;
}

.message.user .message-content {
  text-align: right;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.message.assistant .message-text {
  background: #f5f7fa;
  color: #303133;
}

.message.user .message-text {
  background: #409eff;
  color: white;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.typing {
  display: flex;
  gap: 4px;
  padding: 16px;
}

.dot {
  width: 8px;
  height: 8px;
  background: #909399;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.input-area {
  padding: 16px;
  border-top: 1px solid #e8e8e8;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-area .el-input {
  flex: 1;
}
</style>
