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
      <q-tabs v-model="leftTab" dense>
        <q-tab name="rutas" label="Rutas" icon="route" />
        <q-tab name="paradas" label="Paradas" icon="directions_bus" />
      </q-tabs>
      <q-separator spaced />

      <q-tab-panels v-model="leftTab" animated>

        <q-tab-panel name="rutas" class="q-pa-md">
          <q-btn label="Nueva ruta" color="primary" @click="addRoute" class="full-width" />
          <q-separator spaced />
          <q-btn dense flat icon="file_upload" @click="triggerFileInput" class="full-width" />
          <q-btn dense flat icon="cloud_download" @click="exportAllRoutes" class="full-width" />
          <input type="file" ref="fileInput" @change="onFileChange" accept=".json" style="display:none" />
          <q-separator spaced />
          <q-list bordered padding>
            <q-item
              v-for="(route, idx) in routes"
              :key="idx"
              clickable
              @click="selectRoute(idx)"
              :active="idx === selectedRouteIdx"
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
          <q-toggle v-model="editing"  label="Modo edición"   class="full-width" dense />
          <q-toggle v-model="cleaning" label="Eliminar puntos" class="full-width" dense />
        </q-tab-panel>

        <q-tab-panel name="paradas" class="q-pa-md">
          <q-toggle v-model="stopsMode"   label="Definir paradas" class="full-width" dense />
          <q-toggle v-model="stopsEditing" label="Modo edición de paradas" class="full-width" dense />
          <q-slider
            v-model="stopsRadius"
            :label="`Radio: ${stopsRadius} m`"
            label-always
            :min="50"
            :max="1000"
            :step="10"
            style="margin-top: 50px;"
          />
          <q-btn label="Limpiar paradas" color="negative" @click="stops = []" class="full-width" />
          <q-separator spaced />
          <q-list bordered padding v-if="stops.length">
            <q-item v-for="(s, i) in stops" :key="i">
              <q-item-section>Parada {{ i+1 }}: {{ s[0].toFixed(5) }}, {{ s[1].toFixed(5) }}</q-item-section>
              <q-item-section side>
                <q-btn dense flat icon="delete" @click="removeStop(i)" />
              </q-item-section>
            </q-item>
          </q-list>
          <div v-else class="text-grey">No hay paradas</div>
        </q-tab-panel>

      </q-tab-panels>
    </q-drawer>

    <q-drawer v-model="rightDrawerOpen" side="right" overlay elevated>
      <div class="q-pa-md">
        <div v-if="instructions.length">
          <h6>Indicaciones</h6>
          <q-list bordered>
            <q-item v-for="(step, i) in instructions" :key="i" :active="i === currentStepIndex">
              <q-item-section>{{ i+1 }}. {{ step.text }}</q-item-section>
              <q-item-section side>{{ Math.round(step.distance) }} m</q-item-section>
            </q-item>
          </q-list>
        </div>
        <div v-else class="text-grey">Calcula o selecciona una ruta</div>
      </div>
    </q-drawer>

    <q-page-container class="bg-grey-1">
      <router-view
        :routes="routes"
        :stops-editing="stopsEditing"
        :selected-route-idx="selectedRouteIdx"
        :current-route="currentRoute"
        :recalc-idx="recalcIdx"
        :editing="editing"
        :cleaning="cleaning"
        :stops="stops"
        :stops-mode="stopsMode"
        :stops-radius="stopsRadius"
        :position="position"
        @update-route="updateRoute"
        @update-stops="stops = $event"
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
    const leftDrawerOpen = ref(false)
    const rightDrawerOpen = ref(false)
    const leftTab = ref('rutas')
    return { leftDrawerOpen, rightDrawerOpen, leftTab }
  },
  data() {
    return {
      colors: ['red','blue','green','orange','purple','yellow','teal','magenta','cyan','brown','pink',
               'lime','indigo','amber','deep-orange','light-blue','grey','deep-purple','light-green','blue-grey'],
      routes: [{ name: 'Ruta 1', points: [], color: 'red', visible: true }],
      selectedRouteIdx: 0,
      recalcIdx: null,
      editing: false,
      cleaning: false,
      instructions: [],
      currentStepIndex: 0,
      stops: [],
      stopsMode: false,
      stopsRadius: 200,
      stopsEditing: false,
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
    addRoute() {
      console.log('Añadiendo nueva ruta')
      const i = this.routes.length
      this.routes.push({
        name: `Ruta ${i+1}`,
        points: [],
        color: this.colors[i % this.colors.length],
        visible: true
      })
      this.selectedRouteIdx = i
    },
    selectRoute(i) {
      console.log('Seleccionando ruta', i)
      this.selectedRouteIdx = i
    },
    deleteRoute(i) {
      console.log('Eliminando ruta', i)
      const prev = this.selectedRouteIdx
      this.routes.splice(i, 1)
      this.routes.forEach((r, j) => {
        r.name = `Ruta ${j+1}`
        r.color = this.colors[j % this.colors.length]
      })
      this.selectedRouteIdx = this.routes.length
        ? prev > i ? prev-1 : Math.min(prev, this.routes.length-1)
        : null
    },
    recalcRoute(i) {
      console.log('Recalculando ruta', i)
      this.recalcIdx = i
      setTimeout(() => { this.recalcIdx = null }, 0)
    },
    updateRoute(pts) {
      console.log('Actualizando puntos de ruta', pts)
      if (this.currentRoute) {
        this.currentRoute.points = pts
      }
    },
    undoRoute(i) {
      console.log('Deshaciendo último punto de ruta', i)
      const pts = this.routes[i].points
      if (pts.length) {
        pts.pop()
        this.recalcRoute(i)
      }
    },
    clearRoute(i) {
      console.log('Limpiando ruta completa', i)
      const pts = this.routes[i].points
      if (pts.length) {
        this.routes[i].points = []
        this.recalcRoute(i)
      }
    },
    invertRoute(i) {
      console.log('Invertir ruta', i)
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
    triggerFileInput() {
      this.$refs.fileInput.click()
    },
    onFileChange(e) {
      console.log('Cargando archivo de rutas')
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
      console.log('Exportando todas las rutas')
      const data = this.routes.map(r => ({
        name: r.name,
        color: r.color,
        waypoints: r.points.map(p => ({ lat: p[0], lng: p[1] }))
      }))
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = 'routes.json'; a.click()
      URL.revokeObjectURL(url)
    },
    exportRoute(idx) {
      console.log('Exportando ruta individual', idx)
      const r = this.routes[idx]
      const data = {
        name: r.name,
        color: r.color,
        waypoints: r.points.map(p => ({ lat: p[0], lng: p[1] }))
      }
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = `${r.name}.json`; a.click()
      URL.revokeObjectURL(url)
    },
    removeStop(i) {
      console.log('Eliminando parada', i)
      this.stops.splice(i, 1)
    },
    setInstructions(idx, steps) {
      console.log('Actualizando instrucciones para ruta', idx)
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
.route-color-bar { width: 4px; margin-right: 8px; }
.q-page.no-padding    { padding: 0 !important; }
.clean-mode .leaflet-container { cursor: crosshair !important; }
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
