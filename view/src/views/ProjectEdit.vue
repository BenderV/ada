<template>
  <Form @submit="clickSave" class="max-w-7xl mx-auto px-4">
    <nav class="flex items-center justify-between px-4 sm:px-0">
      <div class="-mt-px flex w-0 flex-1">
        <a
          @click.prevent="clickCancel"
          class="inline-flex items-center border-t-2 border-transparent pt-4 pr-1 text-sm font-medium text-gray-500 hover:text-gray-700 cursor-pointer"
        >
          <ArrowLeftIcon class="mr-3 h-5 w-5 text-gray-400" aria-hidden="true" />
          Return to all projects
        </a>
      </div>
    </nav>
    <br />
    <div class="sm:col-span-6">
      <base-input name="Name" v-model="project.name" rules="required" />
      <base-input
        name="Description"
        v-model="project.description"
        placeholder="Project used for X,Y and Z..."
      />
      <div class="sm:col-span-6 mt-2">
        <label class="block text-gray-700 text-sm font-medium mt-2" for="tables">Tables</label>
        {{ project.tables }}
        <!-- <BaseSelector
          style="width: 200px"
          :options="tables"
          v-model="project.tables"
        ></BaseSelector> -->
      </div>
    </div>

    <hr class="mt-5" />

    <BaseAlert class="mt-5" v-if="apiError">
      <template #title> There is an error 😔 </template>{{ apiError }}
    </BaseAlert>

    <div class="py-5">
      <div class="flex justify-end">
        <button
          @click.prevent="clickDelete"
          type="button"
          class="rounded-md border border-gray-300 bg-white py-2 px-4 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          Delete
        </button>
        <button
          type="submit"
          class="ml-3 inline-flex justify-center rounded-md border border-transparent bg-blue-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          Save
        </button>
      </div>
    </div>
  </Form>
</template>

<script setup lang="ts">
import { ArrowLeftIcon } from '@heroicons/vue/24/solid'
import { computed, defineComponent, ref } from 'vue'
import { useProjects } from '../stores/projects'
import { fetchDatabaseTables } from '../stores/databases'
import { useRoute } from 'vue-router'
import router from '../router'
import BaseField from '../components/BaseField.vue'
import BaseInput from '../components/BaseInput.vue'
import BaseAlert from '../components/BaseAlert.vue'
import BaseSelector from '@/components/BaseSelector.vue'
import { Field, Form } from 'vee-validate'

// TODO: add class

const route = useRoute()
const apiError = ref(null)

const project = ref({
  id: null,
  name: '',
  description: '',
  tables: [] // selected tables
} as any)

const tables = ref([
  {
    name: 'table1',
    database: 'xxx',
    schema: 'yyy'
  },
  {
    name: 'table2',
    database: 'xxx',
    schema: 'yyy'
  }
])
// TODO fix
// tables.value = await fetchDatabaseTables(2)

const { createProject, updateProject, deleteProject, fetchProjectById } = useProjects()

const isNew = computed(() => route.params.id === 'new')
if (!isNew.value) {
  const projectId = parseInt(route.params.id as string)
  project.value = await fetchProjectById(projectId)
}

const clickDelete = () => {
  if (deleteProject(project.value.id)) {
    router.push({ name: 'ProjectList' })
  }
}

const clickCancel = () => {
  router.push({ name: 'ProjectList' })
}

const clickSave = async () => {
  project.value.tables = tables.value
  try {
    if (isNew.value) {
      project.value = await createProject(project.value)
    } else {
      await updateProject(project.value.id, project.value)
    }
    router.push({ name: 'ProjectList' })
  } catch (error) {
    console.error(error)
    apiError.value = error.response.data.message
  }
}
</script>
