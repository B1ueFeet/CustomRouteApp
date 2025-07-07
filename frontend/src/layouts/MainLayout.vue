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
              <q-toggle v-model="route.visible" dense />
            </q-item-section>
          </q-item>
        </q-list>
        <div v-if="currentRoute">
          <q-separator spaced />
          <div class="q-pa-sm">
            <div>Puntos: {{ currentRoute.points.length }}</div>
            <q-btn label="Limpiar ruta" color="negative" @click="clearCurrentRoute" flat dense />
          </div>
        </div>
      </div>
    </q-drawer>

    <q-drawer v-model="rightDrawerOpen" side="right" overlay elevated>
    </q-drawer>

    <q-page-container class="bg-grey-1">
      <router-view
        :current-route="currentRoute"
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
      routes: [
        { name: 'Ruta 1', points: [], color: 'red', visible: true }
      ],
      selectedRouteIdx: 0
    }
  },
  computed: {
    currentRoute() {
      return this.routes[this.selectedRouteIdx]
    }
  },
  methods: {
    addRoute() {
      const idx = this.routes.length + 1
      console.log('Adding route', idx)
      this.routes.push({
        name: `Ruta ${idx}`,
        points: [],
        color: ['blue','green','orange','purple'][idx % 4],
        visible: true
      })
      this.selectedRouteIdx = this.routes.length - 1
    },
    selectRoute(idx) {
      console.log('Selecting route', idx)
      this.selectedRouteIdx = idx
    },
    clearCurrentRoute() {
      if (this.currentRoute) {
        console.log('Clearing route', this.selectedRouteIdx)
        this.currentRoute.points = []
      }
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
