<template>
  <div class="dashboard">
    <h1>Dashboard</h1>
    <GridLayout
      :layout.sync="layout"
      :col-num="12"
      :row-height="30"
      :is-draggable="true"
      :is-resizable="true"
      :vertical-compact="true"
      :use-css-transforms="true"
      @layout-updated="updateLayout"
    >
      <GridItem
        v-for="item in layout"
        :key="item.i"
        :i="item.i"
        :x="item.x"
        :y="item.y"
        :w="item.w"
        :h="item.h"
      />
    </GridLayout>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { GridLayout, GridItem } from 'vue3-grid-layout'
import DashboardItem from './DashboardItem.vue'

const layout = ref([
  { i: 'a', x: 0, y: 0, w: 6, h: 4 },
  { i: 'b', x: 6, y: 0, w: 6, h: 4 },
  { i: 'c', x: 0, y: 4, w: 12, h: 4 }
])

const updateLayout = (newLayout) => {
  layout.value = newLayout
}
</script>

<style scoped>
.dashboard {
  /* Add your dashboard styles here */
}
</style>
