<template>
  <q-page class="relative-position no-padding">
    <div class="absolute-full" :class="{ 'clean-mode': cleaning }">
      <l-map ref="mapRef" :use-global-leaflet="true" :zoom="zoom" :center="center" style="width:100%;height:100%"
        @click="onMapClick" @mousemove="onMapMouseMove" @mouseout="onMapMouseOut" @ready="onMapReady($event)">

        <l-tile-layer v-for="(layer, i) in tileLayers" :key="i" :url="layer.url" v-bind="layer.options" />

        <!-- Route markers -->
        <l-marker v-for="(pt, idx) in points" :key="idx" :lat-lng="pt" :icon="getMarkerIcon(idx)" :draggable="editing"
          @dragend="onMarkerDragEnd($event, idx)" @click="onMarkerClick(idx, $event)" />

        <!-- Route lines -->
        <l-polyline v-for="item in routeLines" :key="item.idx" :lat-lngs="item.geom" :color="item.route.color"
          :weight="item.idx === selectedRouteIdx ? 5 : 2" :opacity="item.idx === selectedRouteIdx ? 1 : 0.7"
          @click="onPolylineClick(item, $event)" />

        <!-- Hover/delete circle para limpiar ruta -->
        <l-circle v-if="cleaning && hoverCircle" :lat-lng="hoverCircle" :radius="500" :clickable="false" />

        <!-- User location -->
        <l-marker v-if="position" :lat-lng="position" :icon="userIcon" />

        <!-- Hover circle para definir paradas o limpiar paradas -->
        <l-circle v-if="(stopsMode || stopsCleaning) && hoverCircle" :lat-lng="hoverCircle" :radius="stopsRadius"
          :color="stopCircleColor" :fill-color="stopCircleColor" :fill-opacity="0.2" :clickable="false" />

        <!-- Círculos fijos de paradas -->
        <l-circle v-for="(s, i) in localStops" :key="'stop-circle-' + i" :lat-lng="s" :radius="stopsRadius"
          :color="stopCircleColor" :fill-color="stopCircleColor" :fill-opacity="0.2" :clickable="false" />

        <!-- Marcadores de paradas -->
        <l-marker v-for="(s, i) in localStops" :key="'stop-' + i" :lat-lng="s" :icon="busIcon" :draggable="stopsEditing"
          @dragend="onStopDragEnd($event, i)" @click.stop="removeLocalStop(i)" />

        <!-- ————————————————————————————— Capas de datos ————————————————————————————— -->

        <!-- Most Frequent Points -->
        <template v-if="layers.most_frequent_points">
          <l-marker v-for="(p, i) in datos.most_frequent_points" :key="`mfp-${i}`" :lat-lng="[p.lat, p.lon]"
            :icon="starIcon" />
        </template>


        <!-- Most Frequent Points Barrio -->
        <template v-if="layers.most_frequent_points_barrio">
          <l-marker v-for="(p, i) in datos.most_frequent_points_barrio" :key="`mfpb-${i}`" :lat-lng="[p.lat, p.lon]"
            :icon="flagIcon" />
        </template>

        <!-- Grouped Barrios (marcador + círculo) -->
        <template v-if="layers.grouped_barrios">
          <l-marker v-for="(b, i) in datos.grouped_barrios" :key="`gb-${i}`" :lat-lng="[b.lat, b.lon]"
            :icon="streetViewIcon" />
          <l-circle v-for="(b, i) in datos.grouped_barrios" :key="`gbc-${i}`" :lat-lng="[b.lat, b.lon]" :radius="500"
            color="#00ABFF" fill-color="#00ABFF" :fill-opacity="0.1" />
        </template>

        <!-- Decesos (iconos fantasma) -->
        <template v-if="layers.decesos_points">
          <l-marker v-for="(c, i) in decesosCoords" :key="`dec-${i}`" :lat-lng="c" :icon="ghostIcon" />
        </template>
      </l-map>
    </div>
  </q-page>
</template>

<script>
import {
  LMap, LTileLayer, LMarker, LPolyline, LCircle
} from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'
import Papa from 'papaparse'

const defaultIcon = L.icon({
  iconUrl:
    'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl:
    'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})
const greenIcon = L.icon({
  iconUrl:
    'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl:
    'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})
const redIcon = L.icon({
  iconUrl:
    'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl:
    'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

const baseIconOpts = {
  className: 'transparent-div-icon',  // <- aquí van las reglas de CSS
  iconSize: [24, 24],
  iconAnchor: [12, 12]
}


const userIcon = L.divIcon({
  className: '',
  html:
    '<i class="fa-solid fa-person" style="color:#63E6BE;font-size:24px"></i>',
  iconSize: [24, 24],
  iconAnchor: [12, 12]
})
const busIcon = L.divIcon({
  className: '',
  html:
    '<i class="fa-solid fa-bus" style="color:#86158e;font-size:24px"></i>',
  iconSize: [24, 24],
  iconAnchor: [12, 12]
})
const starIcon = L.divIcon({
  ...baseIconOpts,
  html: '<i class="fas fa-star" style="color: #fac845; font-size:24px;"></i>',
  iconSize: [24, 24], iconAnchor: [12, 12]
})

const flagIcon = L.divIcon({
  ...baseIconOpts,
  html: '<i class="fas fa-flag" style="color: #f78a48; font-size:24px;"></i>',
  iconSize: [24, 24], iconAnchor: [12, 12]
})

const streetViewIcon = L.divIcon({
  ...baseIconOpts,
  html: '<i class="fas fa-street-view" style="color: #00ABFF; font-size:24px;"></i>',
  iconSize: [24, 24], iconAnchor: [12, 12]
})

const ghostIcon = L.divIcon({
  ...baseIconOpts,
  html: '<i class="fas fa-ghost" style="color: #000000; font-size:12px;"></i>',
  iconSize: [16, 16], iconAnchor: [8, 8]
})

const stopCircleColor = '#86158e'

export default {
  name: 'IndexPage',
  components: { LMap, LTileLayer, LMarker, LPolyline, LCircle },
  props: {
    routes: { type: Array, required: true },
    selectedRouteIdx: { type: Number, default: null },
    recalcIdx: { type: Number, default: null },
    currentRoute: { type: Object, default: null },
    editing: { type: Boolean, default: false },
    cleaning: { type: Boolean, default: false },
    position: { type: Array, default: null },
    stops: { type: Array, default: () => [] },
    stopsMode: { type: Boolean, default: false },
    stopsRadius: { type: Number, default: 200 },
    stopsEditing: { type: Boolean, default: false },
    stopsCleaning: { type: Boolean, default: false },
    layers: { type: Object, required: true },
    satelliteMode: { type: Boolean, default: false }
  },
  data() {
    return {
      zoom: 13,
      center: [-0.180653, -78.467838],
      points: [],
      routeGeometries: [],
      hoverCircle: null,
      skipMapClick: false,
      localStops: this.stops.slice(),
      userIcon,
      busIcon,
      starIcon,
      flagIcon,
      streetViewIcon,
      ghostIcon,
      layerGroups: {
        most_frequent_points: L.layerGroup(),
        most_frequent_points_barrio: L.layerGroup(),
        grouped_barrios: L.layerGroup(),
        heat_data: L.layerGroup(),
        decesos_heat: L.layerGroup(),
        decesos_points: L.layerGroup()
      },
      resizeHandler: null,
      datos: {
        most_frequent_points: [],
        most_frequent_points_barrio: [],
        grouped_barrios: [],
        heat_data: []
      },
      decesosCoords: [],
      map: null,
      lightNoLabels: 'https://a.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png',
      lightLabels: 'https://a.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}.png',
      darkLabels:     'https://a.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}.png',
      satellite: 'http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      // opcional: tileUrl si quisieras seguir usando OSM puro
      tileUrl: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
    }
  },
  watch: {
    routes: {
      handler(r) {
        this.routeGeometries = r.map(x => x.points ? x.points.slice() : [])
      },
      deep: true,
      immediate: true
    },
    currentRoute: {
      handler(r) {
        this.points = r && r.points ? r.points.slice() : []
      },
      deep: true,
      immediate: true
    },
    recalcIdx(val) {
      if (
        val === this.selectedRouteIdx &&
        this.points.length >= 2
      ) {
        this.calcRoute(val, this.points)
      }
    },
    stops(newVal) {
      this.localStops = newVal.slice()
    },
    layers: {
      handler() {
        this.updateMapLayers();
      },
      deep: true
    }
  },
  computed: {
    routeLines() {
      return this.routeGeometries
        .map((geom, idx) => ({ geom, idx, route: this.routes[idx] }))
        .filter(i => i.route.visible && i.geom.length > 1)
    },
    tileLayers() {
      if (this.satelliteMode) {
        return [
          {
            url: this.satellite,
            options: { attribution: '© Esri & contributors', maxZoom: 18 }
          },
          {
            url: this.lightLabels,
            options: { attribution: '© Carto / OSM', maxZoom: 19 }
          }
        ]
      }
      return [
        { url: this.lightNoLabels, options: { attribution: '© Carto / OSM', maxZoom: 19 } },
        { url: this.lightLabels, options: { attribution: '', maxZoom: 19 } }
      ]
    }
  },
  methods: {

    async onMapReady(mapInstance) {
      this.map = mapInstance

      try {
        const res = await fetch('/datos.json')
        const json = res.ok ? await res.json() : {}
        this.datos = {
          most_frequent_points: json.most_frequent_points || [],
          most_frequent_points_barrio: json.most_frequent_points_barrio || [],
          grouped_barrios: json.grouped_barrios || [],
          heat_data: json.heat_data || []
        }
      } catch (err) {
        console.error('Error cargando datos.json:', err)
      }

      try {
        const res2 = await fetch('/Decesos.csv')
        const text = res2.ok ? await res2.text() : ''
        const rows = text ? Papa.parse(text, { header: true }).data : []
        this.decesosCoords = rows
          .map(r => [parseFloat(r.Latitud), parseFloat(r.Longitud)])
          .filter(([lat, lon]) => Number.isFinite(lat) && Number.isFinite(lon))
      } catch (err) {
        console.error('Error cargando Decesos.csv:', err)
      }

      const heatPts = this.datos.heat_data
        .filter(p => Array.isArray(p) && Number.isFinite(p[0]) && Number.isFinite(p[1]))
      if (heatPts.length) {
        this.layerGroups.heat_data = L.heatLayer(heatPts, {
          radius: 25,
          blur: 15,
          gradient: { 0: 'blue', 0.3: 'green', 0.5: 'yellow', 0.8: 'orange', 1: 'red' },
          minOpacity: 0.3
        })
      }

      if (this.decesosCoords.length) {
        this.layerGroups.decesos_heat = L.heatLayer(this.decesosCoords, {
          radius: 25,
          blur: 15,
          gradient: { 0.3: 'white', 1: 'black' },
          minOpacity: 0.5

        })
      }

      this.updateMapLayers()

      console.log('heat_data layer on map?', this.map.hasLayer(this.layerGroups.heat_data))
    },

    updateMapLayers() {
      if (!this.map) return

      Object.entries(this.layerGroups).forEach(([key, grp]) => {
        if (!grp) return
        if (this.layers[key] && !this.map.hasLayer(grp)) {
          this.map.addLayer(grp)
        }
        else if (!this.layers[key] && this.map.hasLayer(grp)) {
          this.map.removeLayer(grp)
        }
      })
    },

    getMarkerIcon(i) {
      const last = this.points.length - 1
      if (i === 0) return greenIcon
      if (i === last) return redIcon
      return defaultIcon
    },
    onMapClick(evt) {
      const ll = evt.latlng
      if (this.stopsCleaning) { this.handleStopCleaning(ll); return }
      if (this.stopsMode) { this.handleStopClick(ll); return }
      if (this.cleaning) { this.handleRouteCleaning(ll); return }
      if (this.editing && this.points.length >= 2) {
        this.handleRouteEdit(ll)
        return
      }
      this.handleRouteAdd(ll)
    },
    onMapMouseMove(evt) {
      const ll = evt.latlng
      if (this.stopsMode || this.stopsCleaning || this.cleaning) {
        this.hoverCircle = [ll.lat, ll.lng]
      } else if (
        this.editing &&
        this.points.length >= 2 &&
        this.isNearAnySegment(ll, 50)
      ) {
        this.hoverCircle = [ll.lat, ll.lng]
      } else {
        this.hoverCircle = null
      }
    },
    onMapMouseOut() {
      this.hoverCircle = null
    },
    handleStopClick(ll) {
      this.localStops.push([ll.lat, ll.lng])
      this.$emit('update-stops', this.localStops)
    },
    handleStopCleaning(ll) {
      const idx = this.findNearbyStopIndex(ll, this.stopsRadius)
      if (idx !== -1) {
        this.localStops.splice(idx, 1)
        this.$emit('update-stops', this.localStops)
      }
    },
    findNearbyStopIndex(latlng, r) {
      let idx = -1, dmin = r
      this.localStops.forEach((p, i) => {
        const d = latlng.distanceTo(L.latLng(...p))
        if (d < dmin) { dmin = d; idx = i }
      })
      return idx
    },
    handleRouteAdd(ll) {
      this.points.push([ll.lat, ll.lng])
      this.$emit('update-route', this.points)
      if (this.points.length >= 2) this.calcRoute(this.selectedRouteIdx, this.points)
      this.center = [ll.lat, ll.lng]
    },
    handleRouteCleaning(ll) {
      const rem = this.findNearbyPointIndex(ll, 200)
      if (rem !== -1) {
        this.points.splice(rem, 1)
        this.$emit('update-route', this.points)
        if (this.points.length >= 2) this.calcRoute(this.selectedRouteIdx, this.points)
      }
    },
    handleRouteEdit(ll) {
      const ins = this.findInsertIndex(this.points, ll)
      const [p1, p2] = [this.points[ins - 1], this.points[ins]]
      const mid = L.latLng(
        (p1[0] + p2[0]) / 2,
        (p1[1] + p2[1]) / 2
      )
      if (ll.distanceTo(mid) <= 50) {
        this.points.splice(ins, 0, [ll.lat, ll.lng])
        this.$emit('update-route', this.points)
        this.calcRoute(this.selectedRouteIdx, this.points)
      }
    },
    onMarkerDragEnd(evt, i) {
      if (evt.target.options.icon === this.busIcon) return
      const ll = evt.target.getLatLng()
      this.points.splice(i, 1, [ll.lat, ll.lng])
      this.$emit('update-route', this.points)
      if (this.points.length >= 2) this.calcRoute(this.selectedRouteIdx, this.points)
    },
    onStopDragEnd(evt, i) {
      const ll = evt.target.getLatLng()
      this.localStops.splice(i, 1, [ll.lat, ll.lng])
      this.$emit('update-stops', this.localStops)
    },
    onMarkerClick(i, evt) {
      if (!this.cleaning) return
      evt.originalEvent.stopPropagation()
      this.points.splice(i, 1)
      this.$emit('update-route', this.points)
      if (this.points.length >= 2) this.calcRoute(this.selectedRouteIdx, this.points)
    },
    onPolylineClick(item, evt) {
      if (!this.editing) return
      evt.originalEvent.stopPropagation()
      this.skipMapClick = true
      const ins = this.findInsertIndex(this.points, evt.latlng)
      this.points.splice(ins, 0, [evt.latlng.lat, evt.latlng.lng])
      this.$emit('update-route', this.points)
      this.calcRoute(this.selectedRouteIdx, this.points)
    },
    isNearAnySegment(latlng, r) {
      for (let i = 0; i < this.points.length - 1; i++) {
        const p1 = L.latLng(...this.points[i])
        const p2 = L.latLng(...this.points[i + 1])
        const mid = L.latLng(
          (p1.lat + p2.lat) / 2,
          (p1.lng + p2.lng) / 2
        )
        if (latlng.distanceTo(mid) <= r) return true
      }
      return false
    },
    findNearbyPointIndex(latlng, r) {
      let idx = -1, dmin = r
      this.points.forEach((p, i) => {
        const d = latlng.distanceTo(L.latLng(...p))
        if (d < dmin) { dmin = d; idx = i }
      })
      return idx
    },
    findInsertIndex(pts, latlng) {
      let md = Infinity, idx = 1
      pts.forEach((p, i) => {
        if (i < pts.length - 1) {
          const mid = L.latLng(
            (p[0] + pts[i + 1][0]) / 2,
            (p[1] + pts[i + 1][1]) / 2
          )
          const d = latlng.distanceTo(mid)
          if (d < md) { md = d; idx = i + 1 }
        }
      })
      return idx
    },

    async calcRoute(idx, pts) {
      const coords = pts.map(p => `${p[1]},${p[0]}`).join(';')
      try {
        const params = new URLSearchParams({
          coords,
          steps: 'true',
          overview: 'full'
        })
        const res = await fetch(`/api/route?${params.toString()}`)
        const data = await res.json()
        if (!data.routes?.length) return

        const geo = data.routes[0].geometry.coordinates
        const latlngs = geo.map(c => [c[1], c[0]])
        this.routeGeometries.splice(idx, 1, latlngs)

        const legs = data.routes[0].legs
        const steps = legs.flatMap((leg, legIndex) =>
          leg.steps.map(s => {
            const { type, modifier } = s.maneuver
            let text = ''

            switch (type) {
              case 'depart':
                if (legIndex === 0) {
                  text = `Comienza en ${s.name || 'tu posición'}`
                } else {
                  text = `Continúa por ${s.name || 'esta vía'}`
                }
                break

              case 'continue':
                text = `Continúa por ${s.name || 'esta vía'}`
                break

              case 'turn':
                if (modifier === 'left') text = `Gira a la izquierda en ${s.name || 'la calle'}`
                else if (modifier === 'right') text = `Gira a la derecha en ${s.name || 'la calle'}`
                else text = `Gira ${modifier || ''} en ${s.name || 'la calle'}`
                break

              case 'arrive':
                if (legIndex < legs.length - 1) {
                  text = `Has llegado al punto de ruta ${legIndex + 1}` +
                    (s.name ? ` en ${s.name}` : '')
                } else {
                  text = `Has llegado a tu destino` +
                    (s.name ? ` en ${s.name}` : '')
                }
                break

              default:
                text = `Continúa por ${s.name || 'esta vía'}`
            }

            return {
              text,
              distance: s.distance,
              duration: s.duration,
              location: [s.maneuver.location[1], s.maneuver.location[0]]
            }
          })
        )

        this.$emit('update-instructions', idx, steps)
      }
      catch (e) {
        console.error('calcRoute error:', e)
      }
    }
  },
  mounted() {
    const resize = () => this.$refs.mapRef.mapObject.invalidateSize()
    setTimeout(resize, 300)
    window.addEventListener('resize', resize)
    this.resizeHandler = resize
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.resizeHandler)
  },

}
</script>

<style scoped>
.q-page.no-padding {
  padding: 0 !important
}

.clean-mode .leaflet-container {
  cursor: crosshair !important
}

:global(.transparent-div-icon) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

.leaflet-overlay-pane canvas {
  z-index: 600 !important;
}
</style>
