<template>
  <q-layout view="hHh lpr lFr">
    <!-- HEADER -->
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-btn dense flat round icon="menu" @click="toggleLeftDrawer">
          <q-tooltip>Mostrar menú izquierdo</q-tooltip>
        </q-btn>
        <q-toolbar-title>
          <q-avatar>
            <img src="https://cdn.quasar.dev/logo-v2/svg/logo-mono-white.svg" />
          </q-avatar>
          Title
        </q-toolbar-title>
        <q-btn dense flat round icon="menu" @click="toggleRightDrawer">
          <q-tooltip>Mostrar menú derecho</q-tooltip>
        </q-btn>
      </q-toolbar>
    </q-header>

    <!-- LEFT DRAWER -->
    <q-drawer v-model="leftDrawerOpen" side="left" overlay elevated>
      <q-tabs v-model="leftTab" dense>
        <q-tab name="rutas"  label="Rutas"  icon="route" />
        <q-tab name="paradas" label="Paradas" icon="directions_bus" />
      </q-tabs>
      <q-separator spaced />
      <q-tab-panels v-model="leftTab" animated>

        <!-- RUTAS -->
        <q-tab-panel name="rutas" class="q-pa-md">
          <q-btn label="Nueva ruta" color="primary" @click="addRoute" class="full-width" />
          <q-separator spaced />
          <q-btn dense flat icon="file_upload" @click="triggerFileInput" class="full-width">
            <q-tooltip>Importar rutas</q-tooltip>
          </q-btn>
          <q-btn dense flat icon="cloud_download" @click="exportAllRoutes" class="full-width">
            <q-tooltip>Exportar todas las rutas</q-tooltip>
          </q-btn>
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
                  <q-tooltip>Deshacer punto</q-tooltip>
                </q-btn>
              </q-item-section>

              <q-item-section side bottom class="route-actions-bottom">
                <q-btn dense flat icon="clear_all" @click.stop="clearRoute(idx)">
                  <q-tooltip>Limpiar ruta</q-tooltip>
                </q-btn>
                <q-btn dense flat icon="swap_vert" @click.stop="invertRoute(idx)">
                  <q-tooltip>Invertir ruta</q-tooltip>
                </q-btn>
                <q-btn dense flat icon="file_download" @click.stop="exportRoute(idx)">
                  <q-tooltip>Exportar ruta</q-tooltip>
                </q-btn>
                <q-toggle v-model="route.visible" dense>
                  <q-tooltip>Mostrar/Ocultar ruta</q-tooltip>
                </q-toggle>
              </q-item-section>
            </q-item>
          </q-list>
          <q-separator spaced />
          <q-toggle v-model="editing" label="Modo edición" class="full-width" dense />
          <q-toggle v-model="cleaning" label="Eliminar puntos" class="full-width" dense />
        </q-tab-panel>

        <!-- PARADAS -->
        <q-tab-panel name="paradas" class="q-pa-md">
          <q-toggle v-model="stopsMode"     label="Definir paradas"        class="full-width" dense />
          <q-toggle v-model="stopsEditing"  label="Modo edición de paradas" class="full-width" dense />
          <q-toggle v-model="stopsCleaning" label="Eliminar paradas"        class="full-width" dense />
          <q-slider
            v-model="stopsRadius"
            :label="`Radio: ${stopsRadius} m`"
            label-always
            :min="50"
            :max="1000"
            :step="10"
          />
          <q-btn label="Limpiar paradas" color="negative" @click="updateStops([])" class="full-width">
            <q-tooltip>Eliminar todas las paradas</q-tooltip>
          </q-btn>
          <q-separator spaced />
          <q-list bordered padding v-if="stops.length">
            <q-item v-for="(label, i) in stopsLabels" :key="i">
              <q-item-section>{{ label }}</q-item-section>
              <q-item-section side>
                <q-btn dense flat icon="delete" @click="removeStop(i)">
                  <q-tooltip>Eliminar parada</q-tooltip>
                </q-btn>
              </q-item-section>
            </q-item>
          </q-list>
          <div v-else class="text-grey">No hay paradas</div>
        </q-tab-panel>

      </q-tab-panels>
    </q-drawer>

    <!-- RIGHT DRAWER (INDICACIONES) -->
    <q-drawer v-model="rightDrawerOpen" side="right" overlay elevated>
      <div class="q-pa-md">
        <div v-if="instructions.length">
          <q-btn
            v-if="!guidanceActive"
            label="Iniciar ruta"
            color="primary"
            class="full-width q-mb-sm"
            @click="startGuidance"
          />
          <q-btn
            v-else
            label="Detener ruta"
            color="secondary"
            class="full-width q-mb-sm"
            @click="stopGuidance"
          />
          <h6>Indicaciones</h6>
          <q-list bordered>
            <q-item
              v-for="(step, i) in instructions"
              :key="i"
              :active="i === currentStepIndex"
            >
              <q-item-section>
                {{ i+1 }}. {{ step.text }}
              </q-item-section>
              <q-item-section side>
                {{ Math.round(step.distance) }} m
              </q-item-section>
            </q-item>
          </q-list>
        </div>
        <div v-else class="text-grey">Calcula o selecciona una ruta</div>
      </div>
    </q-drawer>

    <!-- MAPA -->
    <q-page-container class="bg-grey-1">
      <router-view
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
        @update-route="updateRoute"
        @update-stops="updateStops"
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
      leftDrawerOpen:  ref(false),
      rightDrawerOpen: ref(false),
      leftTab:         ref('rutas')
    }
  },
  data() {
    return {
      colors: ['red','blue','green','orange','purple','yellow','teal','magenta','cyan','brown','gray'],
      routes: [
        { name:'Ruta 1', points:[], color:'red', visible:true, stops:[], stopsLabels:[] }
      ],
      selectedRouteIdx: null,
      recalcIdx:        null,
      editing:          false,
      cleaning:         false,
      instructions:     [],
      currentStepIndex: 0,
      stopsMode:        false,
      stopsRadius:      200,
      stopsEditing:     false,
      stopsCleaning:    false,
      position:         null,
      guidanceActive:   false,
      watchId:          null
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
    }
  },
  watch: {
    routes: {
      handler(r) {
        if ((this.selectedRouteIdx === null || this.selectedRouteIdx >= r.length) && r.length) {
          this.selectedRouteIdx = 0
        }
      },
      deep: true,
      immediate: true
    }
  },
  methods: {
    /* RUTAS */
    addRoute() { /* ...igual... */ },
    selectRoute(i) { this.selectedRouteIdx = i },
    deleteRoute(i) { /* ...igual... */ },
    recalcRoute(i) { this.recalcIdx = i; setTimeout(() => this.recalcIdx = null, 0) },
    updateRoute(pts) { if (this.currentRoute) this.currentRoute.points = pts },
    undoRoute(i) { /* ...igual... */ },
    clearRoute(i) { /* ...igual... */ },
    invertRoute(i) { /* ...igual... */ },

    /* IMPORT/EXPORT */
    triggerFileInput() { this.$refs.fileInput.click() },
    async onFileChange(e) { /* ...igual... */ },
    exportAllRoutes() { /* ...igual... */ },
    exportRoute(idx) { /* ...igual... */ },

    /* PARADAS */
    async updateStops(newStops) {
      if (!this.currentRoute) return
      this.currentRoute.stops = newStops
      this.currentRoute.stopsLabels = newStops.map(()=>'Buscando...')
      await this.geocodeAllStops(this.currentRoute)
      this.recalcRoute(this.selectedRouteIdx)
    },
    removeStop(i) {
      this.updateStops(this.stops.filter((_,j)=>j!==i))
    },
    async geocodeAllStops(route) { /* ...igual... */ },

    /* INDICACIONES / GUIDANCE */
    setInstructions(idx, steps) {
      if (idx === this.selectedRouteIdx) {
        this.instructions = steps
        this.currentStepIndex = 0
      }
    },
    startGuidance() {
      this.guidanceActive = true
      this.currentStepIndex = 0
    },
    stopGuidance() {
      this.guidanceActive = false
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
      this.currentStepIndex = Math.min(next, this.instructions.length - 1)
    },

    toggleLeftDrawer()  { this.leftDrawerOpen  = !this.leftDrawerOpen  },
    toggleRightDrawer() { this.rightDrawerOpen = !this.rightDrawerOpen }
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
