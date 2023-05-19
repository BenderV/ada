import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useConfigStore = defineStore(
  'config',
  () => {
    const showHiddenMessages = ref(true)

    const updateShowHiddenMessages = (value: boolean) => {
      showHiddenMessages.value = value
    }

    return {
      showHiddenMessages,
      updateShowHiddenMessages
    }
  },
  {
    persist: true
  }
)
