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

        <!-- Route polylines -->
        <l-polyline
          v-for="item in routeLines"
          :key="item.idx"
          :lat-lngs="item.geom"
          :color="item.route.color"
          :weight="item.idx === selectedRouteIdx ? 5 : 2"
          :opacity="item.idx === selectedRouteIdx ? 1 : 0.7"
          @click="onPolylineClick(item, $event)"
        />

        <!-- Hover/delete circle -->
        <l-circle
          v-if="hoverCircle"
          :center="hoverCircle"
          :radius="cleaning ? 200 : 50"
          :clickable="false"
        />

        <!-- User location arrow -->
        <l-marker
          v-if="position"
          :lat-lng="position"
          :icon="userIcon"
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

// Default, start, end icons
const defaultIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-shadow.png',
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
})
const greenIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-shadow.png',
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
})
const redIcon = L.icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-shadow.png',
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
})

// Google-style arrow for user location
const userIcon = L.divIcon({
  className: 'user-location-arrow',
  iconSize: [24, 24],
  iconAnchor: [12, 12]
})

export default {
  name: 'IndexPage',
  components: { LMap, LTileLayer, LMarker, LPolyline, LCircle },
  props: {
    routes:     { type: Array,  required: true },
    selectedRouteIdx: { type: Number, default: null },
    recalcIdx:  { type: Number, default: null },
    currentRoute:     { type: Object, default: null },
    editing:    { type: Boolean, default: false },
    cleaning:   { type: Boolean, default: false },
    position:   { type: Array,  default: null }
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
        .filter(item => item.route.visible && item.geom.length > 1)
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
      if (val === this.selectedRouteIdx && this.points.length >= 2) {
        this.calcRoute(val, this.points)
      }
    }
  },
  methods: {
    getMarkerIcon(i) {
      const last = this.points.length - 1
      if (i === 0)       return greenIcon
      if (i === last)    return redIcon
      return defaultIcon
    },
    isNearAnySegment(latlng, r) {
      for (let i = 0; i < this.points.length - 1; i++) {
        const p1 = L.latLng(...this.points[i])
        const p2 = L.latLng(...this.points[i+1])
        const mid = L.latLng((p1.lat+p2.lat)/2, (p1.lng+p2.lng)/2)
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
    onMapClick(evt) {
      if (this.skipMapClick) { this.skipMapClick = false; return }
      const ll = evt.latlng
      if (this.cleaning) {
        const rem = this.findNearbyPointIndex(ll, 200)
        if (rem !== -1) {
          this.points.splice(rem, 1)
          this.$emit('update-route', this.points)
          if (this.points.length >= 2) this.calcRoute(this.selectedRouteIdx, this.points)
          return
        }
      }
      if (this.editing && this.points.length >= 2) {
        const ins = this.findInsertIndex(this.points, ll)
        const [p1,p2] = [this.points[ins-1], this.points[ins]]
        const mid = L.latLng((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
        if (ll.distanceTo(mid) <= 50) {
          this.points.splice(ins, 0, [ll.lat, ll.lng])
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
      if (this.cleaning)         this.hoverCircle = [ll.lat, ll.lng]
      else if (this.editing && this.points.length >= 2 && this.isNearAnySegment(ll, 50))
                                 this.hoverCircle = [ll.lat, ll.lng]
      else                       this.hoverCircle = null
    },
    onMapMouseOut() { this.hoverCircle = null },
    onMarkerDragEnd(evt, i) {
      const ll = evt.target.getLatLng()
      this.points.splice(i, 1, [ll.lat, ll.lng])
      this.$emit('update-route', this.points)
      if (this.points.length >= 2) this.calcRoute(this.selectedRouteIdx, this.points)
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
      const ll = evt.latlng
      const ins = this.findInsertIndex(this.points, ll)
      this.points.splice(ins, 0, [ll.lat, ll.lng])
      this.$emit('update-route', this.points)
      this.calcRoute(this.selectedRouteIdx, this.points)
    },
    findInsertIndex(pts, latlng) {
      let md = Infinity, idx = 1
      pts.forEach((p, i) => {
        if (i < pts.length - 1) {
          const mid = L.latLng(
            (p[0] + pts[i+1][0]) / 2,
            (p[1] + pts[i+1][1]) / 2
          )
          const d = latlng.distanceTo(mid)
          if (d < md) { md = d; idx = i+1 }
        }
      })
      return idx
    },
    async calcRoute(idx, pts) {
      const coords = pts.map(p => `${p[1]},${p[0]}`).join(';')
      try {
        const res = await fetch(`http://localhost:8000/api/route?coords=${coords}&steps=true&overview=full`)
        const data = await res.json()
        if (data.routes?.length) {
          const geo = data.routes[0].geometry.coordinates
          const latlngs = geo.map(c => [c[1], c[0]])
          this.routeGeometries.splice(idx, 1, latlngs)
          const steps = data.routes[0].legs[0].steps.map(s => ({
            text: s.maneuver.instruction,
            distance: s.distance,
            duration: s.duration,
            location: [s.maneuver.location[1], s.maneuver.location[0]]
          }))
          this.$emit('update-instructions', idx, steps)
        }
      } catch (e) {
        console.error(e)
      }
    }
  },
  mounted() {
    const resize = () => {
      this.$nextTick(() => this.$refs.mapRef?.mapObject.invalidateSize())
    }
    setTimeout(resize, 300)
    window.addEventListener('resize', resize)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.resizeMap)
  }
}
</script>

<style scoped>
.q-page.no-padding { padding: 0 !important; }
.clean-mode .leaflet-container { cursor: crosshair !important; }

/* Google-style blue arrow */
.user-location-arrow {
  width: 0;
  height: 0;
  border-left: 12px solid transparent;
  border-right: 12px solid transparent;
  border-bottom: 24px solid #4285F4;
  transform: rotate(0deg);
}
</style>
