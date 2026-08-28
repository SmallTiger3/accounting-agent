<template>
  <div class="chat-page">
    <!-- 桌面端会话列表 -->
    <aside class="session-sidebar desktop-only">
      <SessionPanel
        :sessions="sessions"
        :current-session-id="currentSessionId"
        @select="selectSession"
        @new="newSession"
        @delete="deleteSession"
      />
    </aside>

    <section class="chat-main">
      <header class="chat-header">
        <button class="icon-btn mobile-only" @click="showSessions = true">
          <el-icon :size="20"><Menu /></el-icon>
        </button>
        <div class="chat-title">
          <span>{{ currentTitle }}</span>
          <span v-if="currentSessionId" class="chat-sub">AI 记账助手</span>
        </div>
        <button class="icon-btn" @click="newSession" title="新对话">
          <el-icon :size="20"><Plus /></el-icon>
        </button>
      </header>

      <div class="messages" ref="messagesContainer">
        <!-- 空状态 + 快捷指令 -->
        <div v-if="messages.length === 0" class="empty-state">
          <div class="empty-logo">
            <el-icon :size="30"><ChatDotRound /></el-icon>
          </div>
          <h3>开始和 AI 记账助手对话</h3>
          <p>用自然语言记账，比如「今天午餐花了 35 元」</p>
          <div class="quick-prompts">
            <button
              v-for="prompt in quickPrompts"
              :key="prompt"
              class="prompt-chip"
              @click="sendPrompt(prompt)"
            >
              {{ prompt }}
            </button>
          </div>
        </div>

        <div v-for="msg in messages" :key="msg.id" :class="['message', msg.role]">
          <div class="message-avatar">
            <div v-if="msg.role === 'user'" class="avatar user-avatar">
              {{ avatarText }}
            </div>
            <div v-else class="avatar bot-avatar">
              <el-icon :size="17"><ChatDotRound /></el-icon>
            </div>
          </div>
          <div class="message-body">
            <div
              v-if="msg.role === 'assistant'"
              class="message-text markdown-body"
              v-html="renderMarkdown(msg.content)"
            ></div>
            <div v-else class="message-text user-text">{{ msg.content }}</div>
            <div class="message-time">{{ formatTime(msg.created_at) }}</div>
          </div>
        </div>

        <div v-if="sending" class="message assistant">
          <div class="message-avatar">
            <div class="avatar bot-avatar">
              <el-icon :size="17"><ChatDotRound /></el-icon>
            </div>
          </div>
          <div class="message-body">
            <div class="message-text typing">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
          </div>
        </div>
      </div>

      <div class="input-area">
        <div class="input-box">
          <el-input
            v-model="inputText"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 5 }"
            resize="none"
            placeholder="输入消息，例如：今天午餐花了35元"
            @keydown.enter.exact.prevent="sendMessage"
            @keydown.enter.shift.exact.prevent="insertNewline"
            :disabled="sending"
          />
          <button
            class="send-btn"
            :class="{ disabled: !inputText.trim() || sending }"
            @click="sendMessage"
          >
            <el-icon :size="18"><Promotion /></el-icon>
          </button>
        </div>
      </div>
    </section>

    <!-- 移动端会话抽屉 -->
    <el-drawer
      v-model="showSessions"
      direction="ltr"
      size="85%"
      class="app-drawer"
      :with-header="false"
    >
      <SessionPanel
        :sessions="sessions"
        :current-session-id="currentSessionId"
        @select="onSelectMobile"
        @new="onNewMobile"
        @delete="deleteSession"
      />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { chatApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import { marked } from 'marked'
import SessionPanel from '@/components/SessionPanel.vue'

const sessions = ref<any[]>([])
const messages = ref<any[]>([])
const currentSessionId = ref<number | null>(null)
const inputText = ref('')
const sending = ref(false)
const showSessions = ref(false)
const messagesContainer = ref<HTMLElement>()

const authStore = useAuthStore()
const avatarText = computed(() => (authStore.user?.username || '用').slice(0, 1).toUpperCase())

const quickPrompts = [
  '今天午餐花了35元',
  '打车去公司花了20元',
  '本月房租支出3000元',
  '看看我这个月花了多少钱',
]

const currentTitle = computed(() => {
  if (!currentSessionId.value) return '新对话'
  return sessions.value.find((s) => s.id === currentSessionId.value)?.title || '新对话'
})

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

function onSelectMobile(id: number) {
  showSessions.value = false
  selectSession(id)
}

function newSession() {
  currentSessionId.value = null
  messages.value = []
  showSessions.value = false
}

function onNewMobile() {
  newSession()
}

function sendPrompt(text: string) {
  inputText.value = text
  sendMessage()
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || sending.value) return

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

    messages.value.push(response.message)
    currentSessionId.value = response.session_id

    if (response.budget_alerts?.length > 0) {
      response.budget_alerts.forEach((alert: string) => {
        ElMessage.warning(alert)
      })
    }

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

function insertNewline() {
  inputText.value += '\n'
}

function scrollToBottom() {
  nextTick(() => {
    requestAnimationFrame(() => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    })
  })
}

function renderMarkdown(content: string) {
  return marked(content || '')
}

function formatTime(time: string) {
  return dayjs(time).format('HH:mm')
}
</script>

<style scoped>
.chat-page {
  display: flex;
  height: 100%;
  min-height: 0;
  width: 100%;
  background: var(--app-surface);
  overflow: hidden;
}

@media (min-width: 1024px) {
  .chat-page {
    border: 1px solid var(--app-border);
    border-radius: var(--app-radius-lg);
    box-shadow: var(--app-shadow);
  }
}

.session-sidebar {
  width: 280px;
  flex-shrink: 0;
  border-right: 1px solid var(--app-border);
  background: var(--app-surface);
}

.chat-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--app-border);
  flex-shrink: 0;
}

.chat-title {
  flex: 1;
  text-align: center;
  min-width: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--app-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-title span:first-child {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-sub {
  display: block;
  font-size: 11px;
  font-weight: 400;
  color: var(--app-text-3);
  margin-top: 2px;
}

.icon-btn {
  width: 36px;
  min-width: 36px;
  height: 36px;
  border: none;
  background: #f5f6f8;
  border-radius: 10px;
  color: var(--app-text-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.15s ease;
}

.icon-btn:hover {
  background: var(--app-primary-soft);
  color: var(--app-primary-strong);
}

.messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 20px 16px;
  scroll-behavior: smooth;
  overscroll-behavior: contain;
}

/* ============ 空状态 ============ */
.empty-state {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--app-text-3);
  padding: 24px 0;
}

.empty-logo {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  background: var(--app-primary-soft);
  color: var(--app-primary-strong);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18px;
}

.empty-state h3 {
  font-size: 17px;
  font-weight: 700;
  color: var(--app-text);
  margin-bottom: 6px;
}

.empty-state p {
  font-size: 13px;
}

.quick-prompts {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  margin-top: 24px;
  max-width: 480px;
  width: 100%;
}

.prompt-chip {
  padding: 10px 16px;
  border: 1px solid var(--app-border);
  border-radius: 999px;
  background: var(--app-surface);
  font-size: 13px;
  color: var(--app-text-2);
  cursor: pointer;
  transition: all 0.15s ease;
  max-width: 100%;
  white-space: normal;
}

.prompt-chip:hover {
  border-color: var(--app-primary);
  color: var(--app-primary-strong);
  background: var(--app-primary-soft);
}

/* ============ 消息气泡 ============ */
.message {
  display: flex;
  gap: 10px;
  margin-bottom: 18px;
  min-width: 0;
}

.message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 14px;
  font-weight: 700;
}

.user-avatar {
  background: linear-gradient(135deg, #10b981, #0d9488);
  color: #fff;
}

.bot-avatar {
  background: var(--app-primary-soft);
  color: var(--app-primary-strong);
}

.message-body {
  max-width: 78%;
  min-width: 0;
}

.message.user .message-body {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-text {
  padding: 11px 15px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.65;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.user-text {
  background: linear-gradient(135deg, #10b981, #0d9488);
  color: #fff;
  border-top-right-radius: 4px;
  white-space: pre-wrap;
}

.message.assistant .message-text {
  background: #f5f6f8;
  color: var(--app-text);
  border-top-left-radius: 4px;
  max-width: 100%;
}

.message-time {
  font-size: 11px;
  color: var(--app-text-3);
  margin-top: 5px;
  padding: 0 4px;
}

/* Markdown 内容样式 */
.markdown-body :deep(p) {
  margin: 0 0 8px;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin: 10px 0 6px;
  font-size: 15px;
  font-weight: 700;
  color: var(--app-text);
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 6px 0;
  padding-left: 20px;
}

.markdown-body :deep(li) {
  margin: 3px 0;
}

.markdown-body :deep(code) {
  background: #eef0f3;
  padding: 2px 6px;
  border-radius: 6px;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 12.5px;
}

.markdown-body :deep(pre) {
  background: #1e293b;
  color: #e2e8f0;
  padding: 12px 14px;
  border-radius: 10px;
  overflow-x: auto;
  margin: 8px 0;
  max-width: 100%;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
}

.markdown-body :deep(blockquote) {
  margin: 8px 0;
  padding: 6px 12px;
  border-left: 3px solid var(--app-primary);
  background: var(--app-primary-soft);
  border-radius: 0 8px 8px 0;
  color: var(--app-text-2);
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
  width: 100%;
  display: block;
  overflow-x: auto;
  font-size: 13px;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid var(--app-border);
  padding: 6px 10px;
  text-align: left;
}

.markdown-body :deep(th) {
  background: #f5f6f8;
  font-weight: 600;
}

.markdown-body :deep(a) {
  color: var(--app-primary-strong);
}

/* 打字动画 */
.typing {
  display: flex;
  gap: 5px;
  padding: 14px 16px;
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--app-text-3);
  animation: typing 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* ============ 输入区 ============ */
.input-area {
  padding: 10px 14px calc(10px + env(safe-area-inset-bottom));
  border-top: 1px solid var(--app-border);
  flex-shrink: 0;
  background: var(--app-surface);
}

.input-box {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  min-width: 0;
  background: #f5f6f8;
  border: 1px solid transparent;
  border-radius: 14px;
  padding: 8px 8px 8px 14px;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.input-box:focus-within {
  border-color: var(--app-primary);
  background: var(--app-surface);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
}

.input-box :deep(.el-textarea__inner) {
  background: transparent;
  border: none;
  box-shadow: none !important;
  padding: 4px 0;
  min-height: 28px;
  font-size: 14px;
  resize: none;
}

.input-box :deep(.el-textarea) {
  flex: 1;
  min-width: 0;
}

.send-btn {
  width: 38px;
  height: 38px;
  border: none;
  border-radius: 12px;
  background: var(--app-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s ease;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.send-btn:hover {
  background: var(--app-primary-strong);
}

.send-btn.disabled {
  background: #d1d5db;
  box-shadow: none;
  cursor: not-allowed;
}

@media (min-width: 1024px) {
  .messages {
    padding: 24px 28px;
  }

  .input-area {
    padding: 14px 20px 16px;
  }

  .message-body {
    max-width: 68%;
  }
}

@media (max-width: 1023.98px) {
  .chat-page {
    height: 100%;
    border-radius: 0;
  }

  .chat-header {
    padding: 10px 12px;
  }

  .messages {
    padding: 16px 12px;
  }

  .message-body {
    max-width: calc(100% - 54px);
  }

  .message-text {
    padding: 10px 13px;
  }

  .empty-logo {
    width: 56px;
    height: 56px;
    border-radius: 16px;
    margin-bottom: 14px;
  }

  .empty-state h3 {
    font-size: 16px;
  }

  .quick-prompts {
    gap: 8px;
    margin-top: 20px;
  }

  .prompt-chip {
    padding: 9px 12px;
    border-radius: 10px;
  }
}

@media (max-width: 374px) {
  .chat-title {
    font-size: 14px;
  }

  .chat-sub {
    display: none;
  }

  .messages {
    padding-left: 10px;
    padding-right: 10px;
  }

  .message {
    gap: 8px;
  }

  .avatar {
    width: 30px;
    height: 30px;
  }

  .message-body {
    max-width: calc(100% - 44px);
  }

  .input-area {
    padding-left: 10px;
    padding-right: 10px;
  }
}
</style>
