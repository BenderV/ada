<template>
  <div class="max-w-7xl mx-auto px-4">
    <div class="mt-6 flow-root">
      <ul role="list" class="-my-5 divide-y divide-gray-200">
        <li v-for="project in sortedProject" :key="project.id" class="py-4">
          <div class="flex items-center space-x-4">
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-gray-900">
                {{ project.id }} - {{ project.name }}
              </p>
              <p class="truncate text-sm text-gray-500">
                {{ project.engine }}
              </p>
            </div>
            <div>
              <router-link
                :to="'/projects/' + project.id"
                class="inline-flex items-center rounded-full border border-gray-300 bg-white px-2.5 py-0.5 text-sm font-medium leading-5 text-gray-700 shadow-sm hover:bg-gray-50"
              >
                Edit
              </router-link>
            </div>
          </div>
        </li>
      </ul>
    </div>
    <div class="mt-6">
      <router-link
        to="/projects/new"
        href="#"
        class="flex w-full items-center justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
        >Add new
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useProjects } from '../stores/projects'

const { fetchProjects, projects } = useProjects()

fetchProjects({ refresh: true })

const sortedProject = computed(() => {
  return projects.value.sort((a, b) => a.id - b.id)
})
</script>
