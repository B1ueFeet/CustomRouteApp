<template>
  <q-page class="relative-position no-padding">
    <div class="absolute-full" :class="{ 'clean-mode': cleaning }">
      <l-map
        ref="mapRef"
        :use-global-leaflet="false"
        :zoom="zoom"
        :center="center"
        style="width:100%;height:100%"
        @click="onMapClick"
        @mousemove="onMapMouseMove"
        @mouseout="onMapMouseOut"
      >
        <l-tile-layer :url="tileUrl" />

        <!-- Route markers -->
        <l-marker
          v-for="(pt, idx) in points"
          :key="idx"
          :lat-lng="pt"
          :icon="getMarkerIcon(idx)"
          :draggable="editing"
          @dragend="onMarkerDragEnd($event, idx)"
          @click="onMarkerClick(idx, $event)"
        />

        <!-- Route lines -->
        <l-polyline
          v-for="item in routeLines"
          :key="item.idx"
          :lat-lngs="item.geom"
          :color="item.route.color"
          :weight="item.idx === selectedRouteIdx ? 5 : 2"
          :opacity="item.idx === selectedRouteIdx ? 1 : 0.7"
          @click="onPolylineClick(item, $event)"
        />

        <!-- Hover/delete circle para limpiar ruta -->
        <l-circle
          v-if="cleaning && hoverCircle"
          :lat-lng="hoverCircle"
          :radius="500"
          :clickable="false"
        />

        <!-- User location -->
        <l-marker v-if="position" :lat-lng="position" :icon="userIcon" />

        <!-- Hover circle para definir paradas o limpiar paradas -->
        <l-circle
          v-if="(stopsMode || stopsCleaning) && hoverCircle"
          :lat-lng="hoverCircle"
          :radius="stopsRadius"
          :color="stopCircleColor"
          :fill-color="stopCircleColor"
          :fill-opacity="0.2"
          :clickable="false"
        />

        <!-- Círculos fijos de paradas -->
        <l-circle
          v-for="(s, i) in localStops"
          :key="'stop-circle-' + i"
          :lat-lng="s"
          :radius="stopsRadius"
          :color="stopCircleColor"
          :fill-color="stopCircleColor"
          :fill-opacity="0.2"
          :clickable="false"
        />

        <!-- Marcadores de paradas -->
        <l-marker
          v-for="(s, i) in localStops"
          :key="'stop-' + i"
          :lat-lng="s"
          :icon="busIcon"
          :draggable="stopsEditing"
          @dragend="onStopDragEnd($event, i)"
          @click.stop="removeLocalStop(i)"
        />
      </l-map>
    </div>
  </q-page>
</template> 

<script>
import L from 'leaflet'
import {
  LMap, LTileLayer, LMarker, LPolyline, LCircle
} from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'

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
const userIcon = L.divIcon({
  className: '',
  html:
    '<i class="fa-solid fa-person" style="color:#63E6BE;font-size:30px"></i>',
  iconSize: [24, 24],
  iconAnchor: [12, 12]
})
const busIcon = L.divIcon({
  className: '',
  html:
    '<i class="fa-solid fa-bus" style="color:#86158e;font-size:30px"></i>',
  iconSize: [24, 24],
  iconAnchor: [12, 12]
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
    stopsCleaning: { type: Boolean, default: false }
  },
  data() {
    return {
      zoom: 13,
      center: [-0.180653, -78.467838],
      tileUrl: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      points: [],
      routeGeometries: [],
      hoverCircle: null,
      skipMapClick: false,
      localStops: this.stops.slice(),
      userIcon,
      busIcon,  
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
    }
  },
  computed: {
    routeLines() {
      return this.routeGeometries
        .map((geom, idx) => ({ geom, idx, route: this.routes[idx] }))
        .filter(i => i.route.visible && i.geom.length > 1)
    }
  },
  methods: {
    getMarkerIcon(i) {
      const last = this.points.length - 1
      if (i === 0) return greenIcon
      if (i === last) return redIcon
      return defaultIcon
    },
    onMapClick(evt) {
      const ll = evt.latlng
      if (this.stopsCleaning) { this.handleStopCleaning(ll); return }
      if (this.stopsMode)    { this.handleStopClick(ll);    return }
      if (this.cleaning)     { this.handleRouteCleaning(ll);return }
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
      const res  = await fetch(`/api/route?coords=${coords}&steps=true&overview=full`)
      const data = await res.json()
      if (!data.routes?.length) return

      // 1) Dibuja la polilínea completa
      const geo = data.routes[0].geometry.coordinates
      const latlngs = geo.map(c => [c[1], c[0]])
      this.routeGeometries.splice(idx, 1, latlngs)

      // 2) Genera instrucciones de TODOS los legs
      const legs = data.routes[0].legs
      const steps = legs.flatMap((leg, legIndex) =>
        leg.steps.map(s => {
          const { type, modifier } = s.maneuver
          let text = ''

          switch (type) {
            case 'depart':
              // Primer leg vs intermedios
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
              if (modifier === 'left')  text = `Gira a la izquierda en ${s.name || 'la calle'}`
              else if (modifier === 'right') text = `Gira a la derecha en ${s.name || 'la calle'}`
              else text = `Gira ${modifier || ''} en ${s.name || 'la calle'}`
              break

            case 'arrive':
              // Leg intermedio vs último destino
              if (legIndex < legs.length - 1) {
                text = `Has llegado al punto de ruta ${legIndex + 1}` +
                       (s.name ? ` en ${s.name}` : '')
              } else {
                text = `Has llegado a tu destino` +
                       (s.name ? ` en ${s.name}` : '')
              }
              break

            default:
              // new name, fork, end of road, etc.
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
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.resize)
  }
}
</script>

<style scoped>
.q-page.no-padding { padding:0!important }
.clean-mode .leaflet-container { cursor:crosshair!important }
</style>
