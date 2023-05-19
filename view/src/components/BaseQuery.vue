<template>
  <BaseSelector
    class="float-right ml-auto"
    style="width: 200px"
    :options="databases"
    v-model="databaseSelected"
  ></BaseSelector>
  <br /><br />
  <BaseEditor v-model="querySQL" @run-query="runQuery"></BaseEditor>

  <div class="mt-2 flex justify-end">
    <button
      v-if="selectedIndex === 1"
      class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 mx-2 disabled:bg-slate-50 disabled:text-slate-500 disabled:border-slate-200 disabled:shadow-none"
      @click="validateQuery"
      :disabled="queryValidated && !queryIsModified"
    >
      <span v-if="!queryIsModified">Validate query</span>
      <span v-else>Save correction</span>
    </button>

    <button
      class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      @click="runQuery()"
      :disabled="queryLoading"
    >
      <ArrowPathIcon v-if="queryLoading" class="animate-reverse-spin h-5 w-5 text-white mr-2" />
      Run Query
    </button>
  </div>
</template>

<script setup lang="ts">
import BaseEditor from '@/components/BaseEditor.vue'
import {
  querySQL,
  runQuery,
  validateQuery,
  queryIsModified,
  loading as queryLoading,
  queryValidated
} from '../stores/query'
import { ref } from 'vue'

import { useDatabases } from '../stores/databases'
import BaseSelector from './BaseSelector.vue'
import { ArrowPathIcon } from '@heroicons/vue/24/outline'

const { databaseSelected, databases } = useDatabases()

const selectedIndex = ref<number>(0)
</script>
