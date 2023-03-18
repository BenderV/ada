<template>
  <div
    class="message-display p-4 mb-4 rounded-lg bg-gray-200"
    :class="{ 'bg-gray-400': message.display === false }"
  >
    <!-- if message.display = hide, then show as light gray -->
    <p class="font-bold">
      {{ message.role }}
    </p>

    <template v-for="(part, index) in parsedText">
      <span v-if="part.type === 'text'" :key="`text-${index}`">
        {{ part.content }}
      </span>
      <SqlCode v-if="part.type === 'sql'" :code="part.content" :key="`sql-${index}`" />
      <BaseTable v-if="part.type === 'json'" :data="message.data" :key="`json-${index}`" />
    </template>
  </div>
</template>

<script>
import SqlCode from '@/components/SqlCode.vue'
import BaseTable from '@/components/BaseTable.vue'

export default {
  components: {
    SqlCode,
    BaseTable
  },
  props: {
    message: {
      type: Object,
      required: true
    }
  },
  computed: {
    parsedText() {
      const regex = /```(?:sql|json)\s*([\s\S]*?)\s*```/g
      let match
      let lastIndex = 0
      const parts = []

      while ((match = regex.exec(this.message.content)) !== null) {
        if (match.index > lastIndex) {
          parts.push({
            type: 'text',
            content: this.message.content.slice(lastIndex, match.index)
          })
        }

        parts.push({
          type: match[0].includes('sql') ? 'sql' : 'json',
          content: match[1].trim()
        })

        lastIndex = match.index + match[0].length
      }

      if (lastIndex < this.message.content.length) {
        parts.push({
          type: 'text',
          content: this.message.content.slice(lastIndex)
        })
      }

      return parts
    }
  }
}
</script>

<style>
.message-display {
  border: 1px solid #e5e7eb;
}
.sql-code {
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 2px 4px;
  font-family: monospace;
  white-space: pre-wrap;
}
</style>
