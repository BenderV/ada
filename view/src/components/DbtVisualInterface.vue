<template>
  <div class="min-h-screen bg-gray-100 py-6 flex flex-col justify-center sm:py-12">
    <div class="relative py-3 sm:max-w-xl sm:mx-auto">
      <h1 class="text-4xl font-bold text-center mb-4">Ada: The Data Engineer Assistant</h1>
      <small class="block text-center mb-8">
        Connected to database <strong class="font-semibold">{{ database }}</strong>
      </small>

      <div class="dbt-visual-interface">
        <div
          class="messages bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4"
          v-if="messages.length > 0"
        >
          <h2 class="font-bold text-xl mb-4">Messages</h2>

          <div class="flex items-center justify-between mb-4">
            <label class="text-gray-700 text-sm font-bold text-right" for="showHiddenMessages">
              Show hidden messages:
            </label>
            <input
              type="checkbox"
              id="showHiddenMessages"
              v-model="showHiddenMessages"
              class="hidden peer"
            />

            <label
              class="toggle-label inline-flex items-center justify-center h-6 w-11 rounded-full transition-all duration-200 peer-checked:bg-blue-500 bg-gray-300 cursor-pointer"
              for="showHiddenMessages"
            >
              <span
                class="block w-4 h-4 bg-white rounded-full shadow-md transform transition-all duration-200 peer-checked:translate-x-5"
              ></span>
            </label>
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
        <form @submit.prevent="askQuestion" class="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
          <div class="mb-4">
            <label class="block text-gray-700 text-sm font-bold mb-2" for="query">
              Enter your query:
            </label>
            <input
              class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              type="text"
              id="query"
              v-model="queryInput"
            />
          </div>

          <div class="flex items-center justify-between">
            <button
              class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
              type="submit"
            >
              Submit
            </button>
          </div>
        </form>
        {{ sqlQuery }}

        <div class="tables-views bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
          <h2 class="font-bold text-xl mb-4">Tables & Views</h2>
          <ul class="list-disc list-inside">
            <li v-for="(table, id) in tablesAndViews" :key="id" class="mb-2">
              {{ table.table }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import MessageDisplay from '@/components/MessageDisplay.vue'

import { ref, onMounted, onUnmounted, computed } from 'vue'
import axios from 'axios'
import io from 'socket.io-client'

// const api = axios.create({
//   baseURL: 'http://localhost:3000',
//   headers: {
//     'Content-Type': 'application/json'
//   },
//   interceptors: {
//     request: (config) => {
//       // Add database uri to the request.
//       config.headers['X-Database-Uri'] = uri.value
//       return config
//     }
//   }
// })

const socket = io('/')

const uri = ref('postgresql://postgres:postgres@localhost:5432/formula1')
const database = computed(() => uri.value.split('/').pop())
const queryInput = ref('Show me the youngest driver')
const sqlQuery = ref('')
const tablesAndViews = ref([])
const databases = ref([])
const messages = ref([])
const showHiddenMessages = ref(false)

const fetchTablesAndViews = async () => {
  // Replace with your dbt API endpoint to fetch tables and views.
  const response = await axios.get('/api/tables')
  tablesAndViews.value = response.data
}

const askQuestion = async () => {
  // Post in json format to your back-end API endpoint to get the response.
  const question = queryInput.value
  queryInput.value = ''
  // Emit ask question and messages.length to the server.
  socket.emit('ask', question, messages.value.length)
  messages.value.push({ sender: 'user', content: question })
}

const addMessage = async (message) => {
  messages.value.push(message)
}

onMounted(async () => {
  await fetchTablesAndViews()
  socket.on('response', (response) => {
    addMessage(response)
  })
})
onUnmounted(() => {
  socket.disconnect()
})
</script>
