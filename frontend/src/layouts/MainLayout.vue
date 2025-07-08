<template>
  <q-layout view="hHh lpr lFr">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-btn dense flat round icon="menu" @click="toggleLeftDrawer" />
        <q-toolbar-title>
          <q-avatar>
            <img src="https://cdn.quasar.dev/logo-v2/svg/logo-mono-white.svg" />
          </q-avatar>
          Title
        </q-toolbar-title>
        <q-btn dense flat round icon="menu" @click="toggleRightDrawer" />
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" side="left" overlay elevated>
      <div class="q-pa-md">
        <q-btn label="Nueva ruta" color="primary" @click="addRoute" class="full-width">
          <q-tooltip>Nueva ruta</q-tooltip>
        </q-btn>
        <q-separator spaced />

        <q-btn dense flat icon="file_upload" @click="triggerFileInput" class="full-width">
          <q-tooltip>Importar rutas desde JSON</q-tooltip>
        </q-btn>
        <q-btn dense flat icon="cloud_download" @click="exportAllRoutes" class="full-width">
          <q-tooltip>Exportar todas las rutas</q-tooltip>
        </q-btn>
        <input type="file" ref="fileInput" @change="onFileChange" style="display:none" accept=".json" />

        <q-separator spaced />
        <q-list bordered padding>
          <q-item
            v-for="(route, idx) in routes"
            :key="idx"
            clickable
            @click="selectRoute(idx)"
            :active="idx === selectedRouteIdx"
            class="route-item"
          >
            <q-item-section side class="route-color-bar" :style="{ backgroundColor: route.color }" />
            <q-item-section>{{ route.name }}</q-item-section>

            <q-item-section side top class="route-actions-top">
              <q-btn dense flat icon="delete" @click.stop="deleteRoute(idx)">
                <q-tooltip>Eliminar ruta</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="refresh" @click.stop="recalcRoute(idx)">
                <q-tooltip>Recalcular ruta</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="undo" @click.stop="undoRoute(idx)">
                <q-tooltip>Deshacer último punto</q-tooltip>
              </q-btn>
            </q-item-section>

            <q-item-section side bottom class="route-actions-bottom">
              <q-btn dense flat icon="clear_all" @click.stop="clearRoute(idx)">
                <q-tooltip>Limpiar ruta completa</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="swap_vert" @click.stop="invertRoute(idx)">
                <q-tooltip>Invertir ruta</q-tooltip>
              </q-btn>
              <q-btn dense flat icon="file_download" @click.stop="exportRoute(idx)">
                <q-tooltip>Exportar esta ruta</q-tooltip>
              </q-btn>
              <q-toggle v-model="route.visible" dense>
                <q-tooltip>Mostrar/Ocultar ruta</q-tooltip>
              </q-toggle>
            </q-item-section>
          </q-item>
        </q-list>

        <q-separator spaced />
        <q-toggle v-model="editing" label="Modo edición" class="full-width" dense>
          <q-tooltip>Activar edición</q-tooltip>
        </q-toggle>
        <q-toggle v-model="cleaning" label="Eliminar puntos" class="full-width" dense>
          <q-tooltip>Activar limpieza de puntos</q-tooltip>
        </q-toggle>
      </div>
    </q-drawer>

    <q-drawer v-model="rightDrawerOpen" side="right" overlay elevated>
      <div class="q-pa-md">
        <div v-if="instructions.length">
          <h6>Indicaciones</h6>
          <q-list bordered>
            <q-item
              v-for="(step, i) in instructions"
              :key="i"
              :active="i === currentStepIndex"
            >
              <q-item-section>{{ i + 1 }}. {{ step.text }}</q-item-section>
              <q-item-section side>{{ Math.round(step.distance) }} m</q-item-section>
            </q-item>
          </q-list>
        </div>
        <div v-else class="text-grey">
          Calcula o selecciona una ruta
        </div>
      </div>
    </q-drawer>

    <q-page-container class="bg-grey-1">
      <router-view
        :routes="routes"
        :selected-route-idx="selectedRouteIdx"
        :current-route="currentRoute"
        :recalc-idx="recalcIdx"
        :editing="editing"
        :cleaning="cleaning"
        :position="position"
        @update-route="updateRoute"
        @update-instructions="setInstructions"
      />
    </q-page-container>
  </q-layout>
</template>

<script>
import { ref } from 'vue'
import L from 'leaflet'

export default {
  setup() {
    return {
      leftDrawerOpen: ref(false),
      rightDrawerOpen: ref(false)
    }
  },
  data() {
    return {
      colors: ['red','blue','green','orange','purple'],
      routes: [{ name: 'Ruta 1', points: [], color: 'red', visible: true }],
      selectedRouteIdx: 0,
      recalcIdx: null,
      editing: false,
      cleaning: false,
      instructions: [],
      currentStepIndex: 0,
      position: null,
      watchId: null
    }
  },
  computed: {
    currentRoute() {
      return this.routes[this.selectedRouteIdx] || null
    }
  },
  methods: {
    triggerFileInput() {
      this.$refs.fileInput.click()
    },
    onFileChange(e) {
      const f = e.target.files[0]
      if (!f) return
      const reader = new FileReader()
      reader.onload = () => {
        const json = JSON.parse(reader.result)
        const arr = Array.isArray(json) ? json : [json]
        this.routes = arr.map((r, i) => ({
          name: r.name || `Ruta ${i+1}`,
          points: (r.waypoints||[]).map(w => [w.lat, w.lng]),
          color: r.color || this.colors[i % this.colors.length],
          visible: true
        }))
        this.selectedRouteIdx = 0
      }
      reader.readAsText(f)
      e.target.value = ''
    },
    exportAllRoutes() {
      const data = this.routes.map(r => ({
        name: r.name,
        color: r.color,
        waypoints: r.points.map(p => ({ lat: p[0], lng: p[1] }))
      }))
      const blob = new Blob([JSON.stringify(data,null,2)],{type:'application/json'})
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = 'routes.json'; a.click()
      URL.revokeObjectURL(url)
    },
    exportRoute(idx) {
      const r = this.routes[idx]
      const data = {
        name: r.name,
        color: r.color,
        waypoints: r.points.map(p => ({ lat: p[0], lng: p[1] }))
      }
      const blob = new Blob([JSON.stringify(data,null,2)],{type:'application/json'})
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = `${r.name}.json`; a.click()
      URL.revokeObjectURL(url)
    },
    addRoute() {
      const i = this.routes.length
      this.routes.push({ name:`Ruta ${i+1}`, points:[], color:this.colors[i%this.colors.length], visible:true })
      this.selectedRouteIdx = i
    },
    selectRoute(i) {
      this.selectedRouteIdx = i
    },
    deleteRoute(i) {
      const prev = this.selectedRouteIdx
      this.routes.splice(i,1)
      this.routes.forEach((r,j) => {
        r.name = `Ruta ${j+1}`
        r.color = this.colors[j % this.colors.length]
      })
      this.selectedRouteIdx = this.routes.length
        ? prev>i ? prev-1 : Math.min(prev,this.routes.length-1)
        : null
    },
    recalcRoute(i) {
      this.recalcIdx = i
      setTimeout(() => { this.recalcIdx = null }, 0)
    },
    updateRoute(pts) {
      if (this.currentRoute) this.currentRoute.points = pts
    },
    undoRoute(i) {
      const pts = this.routes[i].points
      if (pts.length) {
        pts.pop()
        this.recalcIdx = i
        setTimeout(() => { this.recalcIdx = null }, 0)
      }
    },
    clearRoute(i) {
      const pts = this.routes[i].points
      if (pts.length) {
        this.routes[i].points = []
        this.recalcIdx = i
        setTimeout(() => { this.recalcIdx = null }, 0)
      }
    },
    invertRoute(i) {
      const b = this.routes[i]
      const inv = b.points.slice().reverse()
      const j = this.routes.length
      this.routes.push({
        name: `${b.name} (Invertida)`,
        points: inv,
        color: this.colors[j % this.colors.length],
        visible: b.visible
      })
      this.selectedRouteIdx = j
    },
    setInstructions(idx, steps) {
      if (idx === this.selectedRouteIdx) {
        this.instructions = steps
        this.currentStepIndex = 0
      }
    },
    updateCurrentStep() {
      if (!this.instructions.length || !this.position) return
      let next = this.currentStepIndex
      for (let i = 0; i < this.instructions.length; i++) {
        const [lat, lng] = this.instructions[i].location
        const d = L.latLng(...this.position).distanceTo(L.latLng(lat, lng))
        if (d < 20) next = i + 1
        else break
      }
      this.currentStepIndex = Math.min(next, this.instructions.length - 1)
    },
    toggleLeftDrawer() {
      this.leftDrawerOpen = !this.leftDrawerOpen
    },
    toggleRightDrawer() {
      this.rightDrawerOpen = !this.rightDrawerOpen
    }
  },
  mounted() {
    if ('geolocation' in navigator) {
      this.watchId = navigator.geolocation.watchPosition(
        pos => {
          this.position = [pos.coords.latitude, pos.coords.longitude]
          this.updateCurrentStep()
        },
        console.error,
        { enableHighAccuracy: true }
      )
    }
  },
  beforeUnmount() {
    if (this.watchId != null) {
      navigator.geolocation.clearWatch(this.watchId)
    }
  }
}
</script>

<style scoped>
.route-color-bar {
  width: 4px;
  margin-right: 8px;
}
.route-actions-top q-btn,
.route-actions-bottom q-btn {
  margin-left: 4px;
}
.route-actions-top {
  display: flex;
  align-items: center;
}
.route-actions-bottom {
  display: flex;
  align-items: center;
  margin-top: 4px;
}
</style>
