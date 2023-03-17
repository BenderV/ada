<template>
  <pre><code ref="codeElement" class="language-sql">{{ code }}</code></pre>
</template>

<script>
import Prism from 'prismjs'

import 'prismjs/components/prism-sql'
import 'prismjs/themes/prism.css'
import { watchEffect, ref } from 'vue'

export default {
  props: {
    code: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const codeElement = ref(null)

    watchEffect(() => {
      if (codeElement.value) {
        Prism.highlightElement(codeElement.value)
      }
    })

    return { codeElement }
  }
}
</script>

<style scoped>
/* Round the corners of the code block */
pre {
  border-radius: 0.2rem;
}
</style>
