<template>
  <button
    class="px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
    @click="onClick"
  >
    <slot></slot>
  </button>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'

interface Props {
  onClick: () => void
}

const props = defineProps<Props>()
</script>
