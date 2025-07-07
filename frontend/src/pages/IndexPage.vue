<!-- IndexPage.vue -->
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
      >
        <l-tile-layer :url="tileUrl" />
        <l-marker
          v-for="(pt, idx) in points"
          :key="idx"
          :lat-lng="pt"
        />
        <l-polyline
          v-for="item in routeLines"
          :key="item.idx"
          :lat-lngs="item.geom"
          :color="item.route.color"
          :weight=" item.idx === selectedRouteIdx ? 5 : 2"
          :opacity=" item.idx === selectedRouteIdx ? 1 : 0.7"
        />
      </l-map>
    </div>
  </q-page>
</template>

<script>
import {
  LMap,
  LTileLayer,
  LMarker,
  LPolyline
} from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'

export default {
  name: 'IndexPage',
  components: { LMap, LTileLayer, LMarker, LPolyline },

  props: {
    routes: {
      type: Array,
      required: true
    },
    selectedRouteIdx: {
      type: Number,
      default: null
    },
    recalcIdx: {
      type: Number,
      default: null
    }
  },

  data() {
    return {
      zoom: 13,
      center: [-0.180653, -78.467838],
      tileUrl: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      points: [],
      routeGeometries: []
    }
  },

  watch: {
    routes: {
      handler(list) {
        console.log('Routes changed', list)
        const old = this.routeGeometries.slice()
        this.routeGeometries = list.map((r,i) => old[i] ?? null)
        list.forEach((r, i) => {
          if (r.points.length >= 2 && this.routeGeometries[i] == null) {
            this.calcRoute(i, r.points)
          }
        })
        const sel = list[this.selectedRouteIdx]
        this.points = sel ? sel.points.slice() : []
      },
      immediate: true,
      deep: true
    },
    selectedRouteIdx(idx) {
      console.log('Selected route', idx)
      const route = this.routes[idx]
      this.points = route ? route.points.slice() : []
      if (route && route.points.length >= 2 && this.routeGeometries[idx] == null) {
        this.calcRoute(idx, route.points)
      }
    },
    recalcIdx(idx) {
      if (idx === this.selectedRouteIdx && this.routes[idx]?.points.length >= 2) {
        console.log('Force recalculating route', idx)
        this.calcRoute(idx, this.routes[idx].points)
      }
    }
  },

  methods: {
    onMapClick(evt) {
      console.log('Map clicked', evt.latlng)
      const { lat, lng } = evt.latlng
      this.points.push([lat, lng])
      this.$emit('update-route', this.points)
      if (this.points.length >= 2) {
        this.calcRoute(this.selectedRouteIdx, this.points)
      }
      this.center = [lat, lng]
    },

    async calcRoute(idx, pts) {
      console.log(`Calculating route ${idx}`, pts)
      const coords = pts.map(([la, lo]) => `${lo},${la}`).join(';')
      try {
        const res = await fetch(`http://localhost:8000/api/route?coords=${coords}`)
        const data = await res.json()
        const geom = data.routes[0].geometry.coordinates.map(p => [p[1], p[0]])
        this.routeGeometries.splice(idx, 1, geom)
      }
      catch {
        this.routeGeometries.splice(idx, 1, null)
      }
    }
  },

  computed: {
    routeLines() {
      return this.routeGeometries
        .map((geom, idx) => ({ geom, idx, route: this.routes[idx] }))
        .filter(item => item.geom && item.route.visible)
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
