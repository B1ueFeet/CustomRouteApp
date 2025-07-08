<template>
  <q-page class="relative-position no-padding">
    <div class="absolute-full">
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
          :draggable="editing"
          @dragend="onMarkerDragEnd($event, idx)"
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
          :radius="50"
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

export default {
  name: 'IndexPage',
  components: { LMap, LTileLayer, LMarker, LPolyline, LCircle },
  props: {
    routes: { type: Array, required: true },
    selectedRouteIdx: { type: Number, default: null },
    recalcIdx: { type: Number, default: null },
    currentRoute: { type: Object, default: null },
    editing: { type: Boolean, default: false }
  },
  data() {
    return {
      zoom: 13,
      center: [-0.180653, -78.467838],
      tileUrl: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      points: [],
      routeGeometries: [],
      hoverCircle: null
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
        console.log('Routes changed, updating routeGeometries', newRoutes)
        this.routeGeometries = newRoutes.map(r => r.points ? r.points.slice() : [])
      },
      deep: true,
      immediate: true
    },
    currentRoute: {
      handler(newRoute) {
        console.log('Current route changed, updating points', newRoute)
        this.points = newRoute && newRoute.points ? newRoute.points.slice() : []
      },
      immediate: true,
      deep: true
    },
    recalcIdx(val) {
      if (val === this.selectedRouteIdx && this.points.length >= 2) {
        console.log('Recalculating route geometry for current route', val)
        this.calcRoute(val, this.points)
      }
    }
  },
  methods: {
    isNearAnySegment(latlng, radius) {
      for (let i = 0; i < this.points.length - 1; i++) {
        const p1 = L.latLng(this.points[i][0], this.points[i][1])
        const p2 = L.latLng(this.points[i + 1][0], this.points[i + 1][1])
        const mid = L.latLng((p1.lat + p2.lat) / 2, (p1.lng + p2.lng) / 2)
        if (latlng.distanceTo(mid) <= radius) return true
      }
      return false
    },
    onMapClick(evt) {
      console.log('Map clicked', evt.latlng)
      const { lat, lng } = evt.latlng
      if (this.editing && this.points.length >= 2) {
        const insertIndex = this.findInsertIndex(this.points, evt.latlng)
        const p1 = this.points[insertIndex - 1]
        const p2 = this.points[insertIndex]
        const mid = L.latLng((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
        if (evt.latlng.distanceTo(mid) <= 50) {
          console.log('Adding intermediate point', insertIndex, evt.latlng)
          this.points.splice(insertIndex, 0, [lat, lng])
          this.$emit('update-route', this.points)
          this.calcRoute(this.selectedRouteIdx, this.points)
          return
        }
      }
      this.points.push([lat, lng])
      this.$emit('update-route', this.points)
      if (this.points.length >= 2) this.calcRoute(this.selectedRouteIdx, this.points)
      this.center = [lat, lng]
    },
    onMapMouseMove(evt) {
      const latlng = evt.latlng
      if (this.editing && this.points.length >= 2 && this.isNearAnySegment(latlng, 50)) {
        this.hoverCircle = [latlng.lat, latlng.lng]
      } else {
        this.hoverCircle = null
      }
    },
    onMapMouseOut() {
      this.hoverCircle = null
    },
    onMarkerDragEnd(evt, idx) {
      const latlng = evt.target.getLatLng()
      console.log('Marker dragged', idx, latlng)
      this.points.splice(idx, 1, [latlng.lat, latlng.lng])
      this.$emit('update-route', this.points)
      if (this.points.length >= 2) this.calcRoute(this.selectedRouteIdx, this.points)
    },
    onPolylineClick(item, evt) {
      console.log('Polyline clicked', item.idx, evt.latlng)
      const newPt = [evt.latlng.lat, evt.latlng.lng]
      const insertIndex = this.findInsertIndex(this.points, evt.latlng)
      this.points.splice(insertIndex, 0, newPt)
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
      console.log(`Calculating route ${idx}`, pts)
      const coords = pts.map(p => `${p[1]},${p[0]}`).join(';')
      try {
        const res = await fetch(`http://localhost:8000/api/route?coords=${coords}`)
        const data = await res.json()
        if (data.routes && data.routes.length) {
          const coordsGeo = data.routes[0].geometry.coordinates
          const latlngs = coordsGeo.map(c => [c[1], c[0]])
          this.routeGeometries.splice(idx, 1, latlngs)
        }
      } catch (err) {
        console.error('Error fetching route', err)
      }
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
</style>
