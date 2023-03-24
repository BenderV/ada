<template>
  <div class="w-full h-screen flex justify-center items-center px-4">
    <div class="flex flex-col w-full max-w-2xl h-full">
      <div class="flex flex-col flex-grow h-full overflow-y-auto">
        <div class="w-full pt-4">
          <!-- Dropdown to select the dabase to query -->
          <label class="block text-gray-700 text-sm font-bold mb-2" for="database">
            Database
          </label>
          <BaseSelector
            :options="databases"
            v-model="databaseSelected"
            class="w-full"
            placeholder="Select a database"
            :disabled="conversationId"
          />

          <div class="flex items-center justify-between mb-4 pl-2" v-if="hasHiddenMessages">
            <BaseSwitch v-model="showHiddenMessages" class="float-right">
              <span class="text-gray-700">Show hidden messages</span>
            </BaseSwitch>
          </div>
          <ul class="list-none">
            <li v-for="(message, id) in messages" :key="id">
              <message-display
                :key="id"
                :message="message"
                v-if="message?.display !== false || showHiddenMessages"
              />
            </li>
          </ul>
        </div>
        <!-- Add stop button, centered, displayed only if a query is running -->
        <div class="w-full py-8">
          <div class="w-full flex justify-center">
            queryStatus: {{ queryStatus }}
            <!-- Display error message if queryStatus is error -->
            <div v-if="queryStatus === 'error'">
              <p class="text-red-500">Error: {{ queryStatus }}</p>
            </div>

            <button
              @click="stopQuery"
              v-if="queryStatus === 'running'"
              :disabled="queryStatus === 'to_stop'"
              class="w-24 bg-red-500 text-white py-2 px-4 rounded ml-2"
              type="submit"
            >
              Stop
            </button>
          </div>
        </div>
      </div>
      <div class="w-full py-8">
        <div class="w-full flex">
          <!-- input if return key is pressed, not if ctrl or shift is pressed -->
          <textarea
            @input="resizeTextarea"
            @keyup.enter="handleEnter"
            class="flex-grow py-2 px-3 rounded border border-gray-300"
            rows="1"
            placeholder="Type your message"
            v-model="queryInput"
          ></textarea>
          <button
            @click="sendMessage"
            class="w-24 bg-blue-500 text-white py-2 px-4 rounded ml-2"
            type="submit"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import MessageDisplay from '@/components/MessageDisplay.vue'
import BaseInput from '@/components/BaseInput.vue'
import BaseSwitch from '@/components/BaseSwitch.vue'
import BaseSelector from '@/components/BaseSelector.vue'
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import axios from 'axios'
import io from 'socket.io-client'
import { useDatabases } from '@/stores/databases'
import { useRoute } from 'vue-router'
import { useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const socket = io('/')

const { databaseSelected, databases, selectDatabaseById } = useDatabases()

const queryInput = ref('Show me the youngest driver')
const messages = ref([])
const showHiddenMessages = ref(true)
const conversationId = computed(() => route.params.id)
const queryStatus = ref('')

const fetchMessages = async () => {
  // Replace with your dbt API endpoint to fetch messages.
  axios.get(`/api/conversations/${conversationId.value}`).then((response) => {
    const conversation = response.data
    messages.value = conversation.messages
    selectDatabaseById(conversation.databaseId)
  })
}

watch(
  () => route.params.id,
  (newValue) => {
    queryInput.value = ''
    if (newValue) {
      fetchMessages()
    } else {
      messages.value = []
    }
  }
)

const isQueryRunning = computed(() => {
  // Last message is a query.
  return messages.value[messages.value.length - 1]?.role === 'user'
})

const hasHiddenMessages = computed(() => {
  return messages.value.some((message) => message.display === false)
})

const sendMessage = async () => {
  // Post in json format to your back-end API endpoint to get the response.
  const question = queryInput.value
  queryInput.value = ''
  // Emit ask question and messages.length to the server.
  socket.emit('ask', question, conversationId.value, databaseSelected.value.id)
  messages.value.push({ role: 'user', content: question })
}

const receiveMessage = async (message) => {
  // If message has conversation_id, it is a new conversation.
  if (message.conversation_id) {
    router.push({ path: `/chat/${message.conversation_id}` })
  }
  messages.value.push(message)
}

const stopQuery = async () => {
  socket.emit('stop', conversationId.value)
}

const handleEnter = (event) => {
  if (!event.shiftKey) {
    sendMessage()
  }
}

const Status = {
  RUNNING: 'running',
  CLEAR: 'clear',
  TO_STOP: 'to_stop',
  ERROR: 'error'
}

const updateStatus = (status) => {
  queryStatus.value = status
}

onMounted(async () => {
  await fetchMessages()
  socket.on('response', (response) => {
    receiveMessage(response)
  })

  socket.on('status', (response) => {
    updateStatus(response.status)
  })
})
onUnmounted(() => {
  socket.disconnect()
})

const resizeTextarea = (event) => {
  event.target.style.height = 'auto'
  event.target.style.height = event.target.scrollHeight + 'px'
}
</script>

<style scoped>
textarea {
  height: auto;
}
</style>
