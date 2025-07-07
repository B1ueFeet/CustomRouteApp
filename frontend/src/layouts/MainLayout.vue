<!-- MainLayout.vue -->
<template>
  <q-layout view="hHh lpr lFr">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-btn dense flat round icon="menu" @click="toggleLeftDrawer" />
        <q-toolbar-title>
          <q-avatar>
            <img src="https://cdn.quasar.dev/logo-v2/svg/logo-mono-white.svg">
          </q-avatar>
          Title
        </q-toolbar-title>
        <q-btn dense flat round icon="menu" @click="toggleRightDrawer" />
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" side="left" overlay elevated>
      <div class="q-pa-md">
        <q-btn label="Nueva ruta" color="primary" @click="addRoute" class="full-width" />
        <q-separator spaced />
        <q-list bordered>
          <q-item
            v-for="(route, idx) in routes"
            :key="idx"
            clickable
            @click="selectRoute(idx)"
            :active="idx === selectedRouteIdx"
          >
            <q-item-section>{{ route.name }}</q-item-section>
            <q-item-section side>
              <q-btn dense flat icon="delete" @click.stop="deleteRoute(idx)" />
              <q-btn dense flat icon="refresh" @click.stop="recalcRoute(idx)" />
              <q-toggle v-model="route.visible" dense />
            </q-item-section>
          </q-item>
        </q-list>
      </div>
    </q-drawer>

    <q-drawer v-model="rightDrawerOpen" side="right" overlay elevated>
    </q-drawer>

    <q-page-container class="bg-grey-1">
      <router-view
        :routes="routes"
        :selected-route-idx="selectedRouteIdx"
        :current-route="currentRoute"
        :recalc-idx="recalcIdx"
        @update-route="updateRoute"
      />
    </q-page-container>
  </q-layout>
</template>

<script>
import { ref } from 'vue'

export default {
  data() {
    return {
      colors: ['red','blue','green','orange','purple'],
      routes: [
        { name: 'Ruta 1', points: [], color: 'red', visible: true }
      ],
      selectedRouteIdx: 0,
      recalcIdx: null
    }
  },
  computed: {
    currentRoute() {
      return this.routes[this.selectedRouteIdx] || null
    }
  },
  methods: {
    addRoute() {
      const idx = this.routes.length
      console.log('Adding route', idx + 1)
      this.routes.push({
        name: `Ruta ${idx + 1}`,
        points: [],
        color: this.colors[idx % this.colors.length],
        visible: true
      })
      this.selectedRouteIdx = idx
    },
    selectRoute(idx) {
      console.log('Selecting route', idx)
      this.selectedRouteIdx = idx
    },
    deleteRoute(idx) {
      console.log('Deleting route', idx)
      const prev = this.selectedRouteIdx
      this.routes.splice(idx, 1)
      this.routes.forEach((r, i) => {
        r.name = `Ruta ${i + 1}`
        r.color = this.colors[i % this.colors.length]
      })
      if (this.routes.length === 0) {
        this.selectedRouteIdx = null
      } else if (prev === idx) {
        this.selectedRouteIdx = Math.min(idx, this.routes.length - 1)
      } else if (prev > idx) {
        this.selectedRouteIdx = prev - 1
      } else {
        this.selectedRouteIdx = prev
      }
    },
    recalcRoute(idx) {
      console.log('Recalculating route', idx)
      this.recalcIdx = idx
      setTimeout(() => { this.recalcIdx = null }, 0)
    },
    updateRoute(updatedPoints) {
      if (this.currentRoute) {
        console.log('Updating route', this.selectedRouteIdx, updatedPoints)
        this.currentRoute.points = updatedPoints
      }
    }
  },
  setup () {
    const leftDrawerOpen = ref(false)
    const rightDrawerOpen = ref(false)
    return {
      leftDrawerOpen,
      toggleLeftDrawer () {
        leftDrawerOpen.value = !leftDrawerOpen.value
      },
      rightDrawerOpen,
      toggleRightDrawer () {
        rightDrawerOpen.value = !rightDrawerOpen.value
      }
    }
  }
}
</script>
