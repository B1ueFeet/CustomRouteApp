<template>
  <q-layout view="hHh lpr lFr">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-btn dense flat round icon="menu" @click="toggleLeftDrawer">
          <q-tooltip anchor="center left" self="center right">Mostrar menú izquierdo</q-tooltip>
        </q-btn>
        <q-toolbar-title>
          <q-avatar><img src="../assets/icon.png" /></q-avatar>
          Custom Route Manager
        </q-toolbar-title>
        <q-btn dense flat round icon="menu" @click="toggleRightDrawer">
          <q-tooltip anchor="center right" self="center left">Mostrar menú derecho</q-tooltip>
        </q-btn>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" side="left" overlay elevated>
      <q-tabs v-model="leftTab" dense>
        <q-tab name="rutas" label="Rutas" icon="route" />
        <q-tab name="paradas" label="Paradas" icon="directions_bus" />
        <q-tab name="layers" label="Capas" icon="layers" />
      </q-tabs>
      <q-separator spaced />
      <q-tab-panels v-model="leftTab" animated>
        <q-tab-panel name="rutas" class="q-pa-md">
          <q-btn label="Nueva ruta" color="primary" @click="addRoute" class="full-width" />
          <q-separator spaced />
          <q-btn dense flat icon="file_upload" @click="triggerFileInput">
            <q-tooltip anchor="center left" self="center right">Importar rutas</q-tooltip>
          </q-btn>
          <q-btn dense flat icon="cloud_download" @click="exportAllRoutes">
            <q-tooltip anchor="center left" self="center right">Exportar todas las rutas</q-tooltip>
          </q-btn>
          <input type="file" ref="fileInput" @change="onFileChange" accept=".json" style="display:none" />
          <q-separator spaced />
          <q-toggle v-model="editing" label="Modo edición" class="full-width" dense />
          <q-toggle v-model="cleaning" label="Eliminar puntos" class="full-width" dense />
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
                  <q-tooltip anchor="center left" self="center right">Eliminar ruta</q-tooltip>
                </q-btn>
                <q-btn dense flat icon="refresh" @click.stop="recalcRoute(idx)">
                  <q-tooltip anchor="center left" self="center right">Recalcular ruta</q-tooltip>
                </q-btn>
                <q-btn dense flat icon="undo" @click.stop="undoRoute(idx)">
                  <q-tooltip anchor="center left" self="center right">Deshacer último punto</q-tooltip>
                </q-btn>
              </q-item-section>
              <q-item-section side bottom class="route-actions-bottom">
                <q-btn dense flat icon="clear_all" @click.stop="clearRoute(idx)">
                  <q-tooltip anchor="center left" self="center right">Limpiar ruta completa</q-tooltip>
                </q-btn>
                <q-btn dense flat icon="swap_vert" @click.stop="invertRoute(idx)">
                  <q-tooltip anchor="center left" self="center right">Invertir ruta</q-tooltip>
                </q-btn>
                <q-btn dense flat icon="file_download" @click.stop="exportRoute(idx)">
                  <q-tooltip anchor="center left" self="center right">Exportar esta ruta</q-tooltip>
                </q-btn>
                <q-toggle v-model="route.visible" dense>
                  <q-tooltip anchor="center left" self="center right">Mostrar/Ocultar ruta</q-tooltip>
                </q-toggle>
              </q-item-section>
            </q-item>
          </q-list>
        </q-tab-panel>

        <q-tab-panel name="paradas" class="q-pa-md">
          <q-toggle v-model="stopsMode" label="Definir paradas" class="full-width" dense />
          <q-toggle v-model="stopsEditing" label="Modo edición de paradas" class="full-width" dense />
          <q-toggle v-model="stopsCleaning" label="Eliminar paradas" class="full-width" dense />
          <q-slider
            v-model="stopsRadius"
            :label="`Radio: ${stopsRadius} m`"
            label-always
            :min="50"
            :max="1000"
            :step="10"
            style="margin-top: 50px;"
          />
          <q-btn label="Limpiar paradas" color="negative" @click="updateStops([])" class="full-width">
            <q-tooltip anchor="center left" self="center right">Eliminar todas las paradas</q-tooltip>
          </q-btn>
          <q-separator spaced />
          <q-list bordered padding v-if="stops.length">
            <q-item v-for="(label, i) in stopsLabels" :key="i">
              <q-item-section>{{ label }}</q-item-section>
              <q-item-section side>
                <q-btn dense flat icon="delete" @click="removeStop(i)">
                  <q-tooltip anchor="center left" self="center right">Eliminar parada</q-tooltip>
                </q-btn>
              </q-item-section>
            </q-item>
          </q-list>
          <div v-else class="text-grey">No hay paradas</div>
        </q-tab-panel>

        <q-tab-panel name="layers" class="q-pa-md">
          <q-list bordered padding>
            <q-item v-for="(label, key) in layerLabels" :key="key">
              <q-item-section>
                <q-checkbox v-model="layers[key]" :label="label" dense />
              </q-item-section>
            </q-item>
          </q-list>
        </q-tab-panel>
      </q-tab-panels>
    </q-drawer>

    <q-drawer v-model="rightDrawerOpen" side="right" overlay elevated>
      <div class="q-pa-md">
        <div v-if="instructions.length">
          <q-btn v-if="!guidanceActive" label="Iniciar guía" color="primary" class="full-width q-mb-sm" @click="startGuidance" />
          <q-btn v-else label="Detener guía" color="secondary" class="full-width q-mb-sm" @click="stopGuidance" />
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
      <router-view v-slot="{ Component }">
        <component
          :is="Component"
          :routes="routes"
          :stops-editing="stopsEditing"
          :stops-cleaning="stopsCleaning"
          :selected-route-idx="selectedRouteIdx"
          :current-route="currentRoute"
          :recalc-idx="recalcIdx"
          :editing="editing"
          :cleaning="cleaning"
          :stops="stops"
          :stops-mode="stopsMode"
          :stops-radius="stopsRadius"
          :position="position"
          :guidance-active="guidanceActive"
          :layers="layers"
          @update-route="updateRoute"
          @update-stops="updateStops"
          @update-instructions="setInstructions"
        />
      </router-view>
    </q-page-container>
  </q-layout>
</template>


<script>
import { ref , reactive } from 'vue'
import L from 'leaflet'
const layerLabels = {
  most_frequent_points:        'Most Frequent Points',
  most_frequent_points_barrio: 'Most Frequent Points Barrio',
  heat_data:                   'Heat Data',
  grouped_barrios:             'Grouped Barrios',
  decesos_heat:                'Decesos (Heat Negro)',
  decesos_points:              'Decesos (Icono Fantasma)'
}

const layers = reactive({
  most_frequent_points:        false,
  most_frequent_points_barrio: false,
  heat_data:                   true,
  grouped_barrios:             false,
  decesos_heat:                true,
  decesos_points:              false
})
export default {
  setup() {
    return {
      leftDrawerOpen: ref(false),
      rightDrawerOpen: ref(false),
      leftTab: ref('rutas'),
      layerLabels,
      layers
    }
  },
  data() {
    return {
      colors: ['red','blue','green','orange','purple','yellow','teal','magenta','cyan','brown','gray'],
      routes: [
        { name: 'Ruta 1', points: [], color: 'red', visible: true, stops: [], stopsLabels: [] }
      ],
      selectedRouteIdx: 0,
      recalcIdx: null,
      editing: false,
      cleaning: false,
      instructions: [],
      currentStepIndex: 0,
      stopsMode: false,
      stopsRadius: 200,
      stopsEditing: false,
      stopsCleaning: false,
      guidanceActive: false,
      position: null,
      watchId: null,
      
    }
  },
  computed: {
    currentRoute() {
      return this.routes[this.selectedRouteIdx] || null
    },
    stops() {
      return this.currentRoute?.stops || []
    },
    stopsLabels() {
      return this.currentRoute?.stopsLabels || []
    },
    currentInstruction() {
      return this.instructions[this.currentStepIndex] || { text: '', distance: 0 }
    }
  },
  methods: {
    toggleLeftDrawer() {
      this.leftDrawerOpen = !this.leftDrawerOpen
      console.log('toggleLeftDrawer:', this.leftDrawerOpen)
    },
    toggleRightDrawer() {
      this.rightDrawerOpen = !this.rightDrawerOpen
      console.log('toggleRightDrawer:', this.rightDrawerOpen)
    },
    addRoute() {
      const i = this.routes.length
      this.routes.push({
        name: `Ruta ${i+1}`,
        points: [],
        color: this.colors[i % this.colors.length],
        visible: true,
        stops: [],
        stopsLabels: []
      })
      this.selectedRouteIdx = i
      console.log('addRoute:', this.routes)
    },
    selectRoute(i) {
      this.selectedRouteIdx = i
      console.log('selectRoute:', i)
    },
    deleteRoute(i) {
      const prev = this.selectedRouteIdx
      this.routes.splice(i, 1)
      this.routes.forEach((r, j) => {
        r.name = `Ruta ${j+1}`
        r.color = this.colors[j % this.colors.length]
      })
      this.selectedRouteIdx = this.routes.length
        ? prev > i ? prev-1 : Math.min(prev, this.routes.length-1)
        : null
      console.log('deleteRoute:', i, this.routes)
    },
    recalcRoute(i) {
      this.recalcIdx = i
      console.log('recalcRoute:', i)
      setTimeout(() => { this.recalcIdx = null }, 0)
    },
    updateRoute(pts) {
      if (this.currentRoute) {
        this.currentRoute.points = pts
        console.log('updateRoute:', pts)
      }
    },
    undoRoute(i) {
      const pts = this.routes[i].points
      if (pts.length) {
        pts.pop()
        this.recalcRoute(i)
        console.log('undoRoute:', i)
      }
    },
    clearRoute(i) {
      const pts = this.routes[i].points
      if (pts.length) {
        this.routes[i].points = []
        this.recalcRoute(i)
        console.log('clearRoute:', i)
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
        visible: b.visible,
        stops: [],
        stopsLabels: []
      })
      this.selectedRouteIdx = j
      console.log('invertRoute:', i)
    },
    triggerFileInput() {
      this.$refs.fileInput.click()
      console.log('triggerFileInput')
    },
    async onFileChange(e) {
      const f = e.target.files[0]
      if (!f) return
      const reader = new FileReader()
      reader.onload = async () => {
        const json = JSON.parse(reader.result)
        const arr = Array.isArray(json) ? json : [json]
        this.routes = arr.map((r,i) => ({
          name: r.name || `Ruta ${i+1}`,
          points: (r.waypoints||[]).map(w => [w.lat, w.lng]),
          color: r.color || this.colors[i % this.colors.length],
          visible: true,
          stops: (r.stops||[]).map(s => [s.lat, s.lng]),
          stopsLabels: (r.stops||[]).map(() => 'Buscando...')
        }))
        this.selectedRouteIdx = 0
        for (const route of this.routes) {
          await this.geocodeAllStops(route)
        }
        console.log('onFileChange:', this.routes)
      }
      reader.readAsText(f)
      e.target.value = ''
    },
    exportAllRoutes() {
      const data = this.routes.map(r => ({
        name: r.name,
        color: r.color,
        waypoints: r.points.map(p => ({ lat:p[0], lng:p[1] })),
        stops: r.stops.map(s => ({ lat:s[0], lng:s[1] }))
      }))
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'routes.json'
      a.click()
      URL.revokeObjectURL(url)
      console.log('exportAllRoutes')
    },
    exportRoute(idx) {
      const r = this.routes[idx]
      const data = {
        name: r.name,
        color: r.color,
        waypoints: r.points.map(p => ({ lat:p[0], lng:p[1] })),
        stops: r.stops.map(s => ({ lat:s[0], lng:s[1] }))
      }
      const blob = new Blob([JSON.stringify(data, null,2)], { type:'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${r.name}.json`
      a.click()
      URL.revokeObjectURL(url)
      console.log('exportRoute:', idx)
    },
    async updateStops(newSt) {
      if (!this.currentRoute) return
      this.currentRoute.stops = newSt
      this.currentRoute.stopsLabels = newSt.map(() => 'Buscando...')
      await this.geocodeAllStops(this.currentRoute)
      this.recalcRoute(this.selectedRouteIdx)
      console.log('updateStops:', newSt)
    },
    removeStop(i) {
      this.updateStops(this.stops.filter((_, j) => j !== i))
      console.log('removeStop:', i)
    },
    async geocodeAllStops(route) {
      for (let i = 0; i < route.stops.length; i++) {
        const [lat, lng] = route.stops[i]
        try {
          const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`
          )
          const js = await res.json()
          route.stopsLabels[i] = js.address.road || js.display_name || `(${lat.toFixed(5)}, ${lng.toFixed(5)})`
        } catch {
          route.stopsLabels[i] = `(${lat.toFixed(5)}, ${lng.toFixed(5)})`
        }
      }
    },
    setInstructions(idx, steps) {
      if (idx === this.selectedRouteIdx) {
        this.instructions = steps
        this.currentStepIndex = 0
        console.log('setInstructions:', steps)
      }
    },
    formatDistance(m) {
      return m >= 1000 ? `${(m/1000).toFixed(1)} km` : `${Math.round(m)} m`
    },
    speakInstruction(text) {
      console.log('speakInstruction:', text)
      if ('speechSynthesis' in window) {
        const u = new SpeechSynthesisUtterance(text)
        window.speechSynthesis.speak(u)
      }
    },
     startGuidance() {
    this.guidanceActive = true
    this.currentStepIndex = 0

    // === Lee la primera instrucción en voz alta ===
    if (this.instructions.length && 'speechSynthesis' in window) {
      const u = new SpeechSynthesisUtterance(this.instructions[0].text)
      u.lang = 'es-ES'
      window.speechSynthesis.cancel()
      window.speechSynthesis.speak(u)
    }
  },

  updateCurrentStep() {
    if (!this.guidanceActive || !this.instructions.length || !this.position) return

    let next = this.currentStepIndex
    for (let i = 0; i < this.instructions.length; i++) {
      const [lat, lng] = this.instructions[i].location
      const d = L.latLng(...this.position).distanceTo(L.latLng(lat, lng))
      if (d < 20) next = i + 1
      else break
    }

    const newIndex = Math.min(next, this.instructions.length - 1)
    if (newIndex !== this.currentStepIndex) {
      this.currentStepIndex = newIndex

      // === Y habla cada nuevo paso ===
      const texto = this.instructions[newIndex].text
      if ('speechSynthesis' in window) {
        const u = new SpeechSynthesisUtterance(texto)
        u.lang = 'es-ES'
        window.speechSynthesis.cancel()
        window.speechSynthesis.speak(u)
      }
    }
  },
    stopGuidance() {
      this.guidanceActive = false
      console.log('stopGuidance')
    }
  },
  watch: {
    currentStepIndex(newIdx, oldIdx) {
      if (newIdx !== oldIdx) this.speakInstruction(this.currentInstruction.text)
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
    if (this.watchId != null) navigator.geolocation.clearWatch(this.watchId)
  }
}
</script>

<style scoped>
.route-color-bar { width:4px; margin-right:8px }
.route-actions-top, .route-actions-bottom { display:flex; align-items:center }
.route-actions-top q-btn, .route-actions-bottom q-btn { margin-left:4px }
.route-actions-bottom { margin-top:4px }
</style>
