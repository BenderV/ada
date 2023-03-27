<template>
  <div class="w-96 h-screen bg-gray-100 flex flex-col">
    <div class="px-4 py-2">
      <BaseButton class="w-full" @click="selectNewConversation">New Conversation</BaseButton>
    </div>
    <div class="overflow-y-auto">
      <!-- Iterate through conversation items -->
      <div
        class="p-4 border-b border-gray-300 cursor-pointer hover:bg-gray-200 flex justify-between items-center"
        v-for="conversation in conversations"
        :key="conversation.id"
        @click.stop="selectConversation(conversation)"
      >
        <div @click="selectConversation(conversation)" class="truncate">
          {{ conversation.name }}
        </div>
        <button @click.stop="deleteConversation(conversation.id)" class="text-grey-500">
          <TrashIcon class="h-5 w-5" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Ref } from 'vue'
import { ref } from 'vue'
import BaseButton from '@/components/BaseButton.vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { TrashIcon } from '@heroicons/vue/24/outline'

// Output the conversations types
type Conversation = {
  id: number
  name: string
}

const router = useRouter()

const conversations: Ref<Conversation[]> = ref([])

conversations.value = await axios
  .get('/api/conversations')
  .then((res) => res.data.sort((a, b) => b.id - a.id))

const selectNewConversation = () => {
  router.push({ path: '/chat' })
}

const selectConversation = (conversation: Conversation) => {
  router.push({ path: `/chat/${conversation.id}` })
}

const deleteConversation = async (id: number) => {
  await axios.delete(`/api/conversations/${id}`)
  conversations.value = conversations.value.filter((conversation) => conversation.id !== id)
  // Redirect to home if the deleted conversation is the current conversation
  if (router.currentRoute.value.params.id === id.toString()) {
    router.push({ path: '/chat' })
  }
}
</script>
