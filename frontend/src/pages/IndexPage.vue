<template>
  <q-page class="relative-position no-padding">
    <div class="absolute-full" :class="{ 'clean-mode': cleaning }">
      <l-map
        ref="mapRef"
        :use-global-leaflet="false"
        :zoom="zoom"
        :center="center"
        style="width: 100%; height: 100%;"
        @click="onMapClick"
        @mousemove="onMapMouseMove"
        @mouseout="onMapMouseOut"
      >
        <l-tile-layer :url="tileUrl" />
        <l-marker
          v-for="(pt, idx) in points"
          :key="idx"
          :lat-lng="pt"
          :icon="getMarkerIcon(idx)"
          :draggable="editing"
          @dragend="onMarkerDragEnd($event, idx)"
          @click="onMarkerClick(idx, $event)"
        />
        <l-polyline
          v-for="item in routeLines"
          :key="item.idx"
          :lat-lngs="item.geom"
          :color="item.route.color"
          :weight="item.idx === selectedRouteIdx ? 5 : 2"
          :opacity="item.idx === selectedRouteIdx ? 1 : 0.7"
          @click="onPolylineClick(item, $event)"
        />
        <l-circle
          v-if="hoverCircle"
          :center="hoverCircle"
          :radius="cleaning ? 200 : 50"
          :clickable="false"
        />
      </l-map>
    </div>
  </q-page>
</template>

<script>
import L from 'leaflet'
import {
  LMap,
  LTileLayer,
  LMarker,
  LPolyline,
  LCircle
} from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'

// marker icons
const defaultIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});
const greenIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});
const redIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

export default {
  name: 'IndexPage',
  components: { LMap, LTileLayer, LMarker, LPolyline, LCircle },
  props: {
    routes: { type: Array, required: true },
    selectedRouteIdx: { type: Number, default: null },
    recalcIdx: { type: Number, default: null },
    currentRoute: { type: Object, default: null },
    editing: { type: Boolean, default: false },
    cleaning: { type: Boolean, default: false }
  },
  data() {
    return {
      zoom: 13,
      center: [-0.180653, -78.467838],
      tileUrl: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      points: [],
      routeGeometries: [],
      hoverCircle: null,
      skipMapClick: false
    }
  },
  computed: {
    routeLines() {
      return this.routeGeometries
        .map((geom, idx) => ({ geom, idx, route: this.routes[idx] }))
        .filter(item => item.route.visible && item.geom && item.geom.length > 1)
    }
  },
  watch: {
    routes: {
      handler(newRoutes) {
        this.routeGeometries = newRoutes.map(r => r.points ? r.points.slice() : [])
      },
      deep: true,
      immediate: true
    },
    currentRoute: {
      handler(newRoute) {
        this.points = newRoute && newRoute.points ? newRoute.points.slice() : []
      },
      immediate: true,
      deep: true
    },
    recalcIdx(val) {
      if (val === this.selectedRouteIdx && this.points.length >= 2) {
        this.calcRoute(val, this.points)
      }
    }
  },
  methods: {
    getMarkerIcon(idx) {
      const last = this.points.length - 1
      if (idx === 0) return greenIcon
      if (idx === last) return redIcon
      return defaultIcon
    },
    isNearAnySegment(latlng, radius) {
      for (let i = 0; i < this.points.length - 1; i++) {
        const p1 = L.latLng(this.points[i][0], this.points[i][1])
        const p2 = L.latLng(this.points[i + 1][0], this.points[i + 1][1])
        const mid = L.latLng((p1.lat + p2.lat) / 2, (p1.lng + p2.lng) / 2)
        if (latlng.distanceTo(mid) <= radius) return true
      }
      return false
    },
    findNearbyPointIndex(latlng, radius) {
      let idx = -1, minDist = radius
      this.points.forEach((p, i) => {
        const d = latlng.distanceTo(L.latLng(p[0], p[1]))
        if (d < minDist) { minDist = d; idx = i }
      })
      return idx
    },
    onMapClick(evt) {
      if (this.skipMapClick) { this.skipMapClick = false; return }
      const ll = evt.latlng
      if (this.cleaning) {
        const removeIdx = this.findNearbyPointIndex(ll, 200)
        if (removeIdx !== -1) {
          this.points.splice(removeIdx, 1)
          this.$emit('update-route', this.points)
          if (this.points.length >= 2) this.calcRoute(this.selectedRouteIdx, this.points)
          return
        }
      }
      if (this.editing && this.points.length >= 2) {
        const insertIndex = this.findInsertIndex(this.points, ll)
        const p1 = this.points[insertIndex - 1]
        const p2 = this.points[insertIndex]
        const mid = L.latLng((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
        if (ll.distanceTo(mid) <= 50) {
          this.points.splice(insertIndex, 0, [ll.lat, ll.lng])
          this.$emit('update-route', this.points)
          this.calcRoute(this.selectedRouteIdx, this.points)
          return
        }
      }
      this.points.push([ll.lat, ll.lng])
      this.$emit('update-route', this.points)
      if (this.points.length >= 2) this.calcRoute(this.selectedRouteIdx, this.points)
      this.center = [ll.lat, ll.lng]
    },
    onMapMouseMove(evt) {
      const ll = evt.latlng
      if (this.cleaning) {
        this.hoverCircle = [ll.lat, ll.lng]
      } else if (this.editing && this.points.length >= 2 && this.isNearAnySegment(ll, 50)) {
        this.hoverCircle = [ll.lat, ll.lng]
      } else {
        this.hoverCircle = null
      }
    },
    onMapMouseOut() {
      this.hoverCircle = null
    },
    onMarkerDragEnd(evt, idx) {
      const latlng = evt.target.getLatLng()
      this.points.splice(idx, 1, [latlng.lat, latlng.lng])
      this.$emit('update-route', this.points)
      if (this.points.length >= 2) this.calcRoute(this.selectedRouteIdx, this.points)
    },
    onMarkerClick(idx, evt) {
      if (!this.cleaning) return
      evt.originalEvent.stopPropagation()
      this.points.splice(idx, 1)
      this.$emit('update-route', this.points)
      if (this.points.length >= 2) this.calcRoute(this.selectedRouteIdx, this.points)
    },
    onPolylineClick(item, evt) {
      if (!this.editing) return
      evt.originalEvent.stopPropagation()
      this.skipMapClick = true
      const ll = evt.latlng
      const insertIndex = this.findInsertIndex(this.points, ll)
      this.points.splice(insertIndex, 0, [ll.lat, ll.lng])
      this.$emit('update-route', this.points)
      this.calcRoute(this.selectedRouteIdx, this.points)
    },
    findInsertIndex(pts, latlng) {
      let minDist = Infinity, index = 1
      pts.forEach((p, i) => {
        if (i < pts.length - 1) {
          const mid = L.latLng((p[0] + pts[i + 1][0]) / 2, (p[1] + pts[i + 1][1]) / 2)
          const d = latlng.distanceTo(mid)
          if (d < minDist) { minDist = d; index = i + 1 }
        }
      })
      return index
    },
    async calcRoute(idx, pts) {
      const coords = pts.map(p => `${p[1]},${p[0]}`).join(';')
      try {
        const res = await fetch(`http://localhost:8000/api/route?coords=${coords}`)
        const data = await res.json()
        if (data.routes && data.routes.length) {
          const coordsGeo = data.routes[0].geometry.coordinates
          const latlngs = coordsGeo.map(c => [c[1], c[0]])
          this.routeGeometries.splice(idx, 1, latlngs)
        }
      } catch {}
    }
  },
  mounted() {
    const resizeMap = () => {
      this.$nextTick(() => {
        const m = this.$refs.mapRef?.mapObject
        if (m) m.invalidateSize()
      })
    }
    setTimeout(resizeMap, 300)
    window.addEventListener('resize', resizeMap)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.resizeMap)
  }
}
</script>

<style scoped>
.q-page.no-padding {
  padding: 0 !important;
}
.clean-mode .leaflet-container {
  cursor: crosshair !important;
}
</style>
