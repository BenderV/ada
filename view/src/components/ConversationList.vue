<template>
  <div class="w-96 h-screen bg-gray-100 flex flex-col">
    <div class="px-4 py-2">
      <BaseButton class="w-full" @click="selectNewConversation">New Conversation</BaseButton>
    </div>
    <div class="overflow-y-auto">
      <!-- Iterate through conversation items -->
      <div
        class="p-4 border-b border-gray-300 cursor-pointer hover:bg-gray-200"
        v-for="conversation in conversations"
        :key="conversation.id"
        @click="selectConversation(conversation)"
      >
        {{ conversation.name }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import BaseSearch from '@/components/BaseSearch.vue'
import BaseButton from '@/components/BaseButton.vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()

const conversations = ref([])

conversations.value = await axios
  .get('/api/conversations')
  .then((res) => res.data.sort((a, b) => b.id - a.id))

const selectNewConversation = () => {
  router.push({ path: '/chat' })
}

const selectConversation = (conversation) => {
  router.push({ path: `/chat/${conversation.id}` })
}
</script>
