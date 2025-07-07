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
        <template v-if="currentRoute.visible">
          <l-marker
            v-for="(pt, idx) in points"
            :key="idx"
            :lat-lng="pt"
          />
          <l-polyline
            v-if="route"
            :lat-lngs="route"
            :color="currentRoute.color"
            :weight="5"
            :opacity="1"
          />
        </template>
        <l-polyline
          v-else-if="route"
          :lat-lngs="route"
          :color="currentRoute.color"
          :weight="2"
          :opacity="0.4"
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
    currentRoute: {
      type: Object,
      default: () => ({ points: [], color: 'blue', visible: true })
    }
  },

  data() {
    return {
      zoom: 13,
      center: [-0.180653, -78.467838],
      tileUrl: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      points: [],
      route: null
    }
  },

  watch: {
    currentRoute: {
      handler(route) {
        console.log('Route changed', route)
        this.points = route.points.slice()
        if (this.points.length >= 2) {
          this.calcRoute(this.points)
        } else {
          this.route = null
        }
      },
      immediate: true,
      deep: true
    }
  },

  methods: {
    onMapClick(evt) {
      console.log('Map clicked at', evt.latlng)
      const { lat, lng } = evt.latlng
      this.points.push([lat, lng])
      this.$emit('update-route', this.points)
      if (this.points.length >= 2) {
        this.calcRoute(this.points)
      }
      this.center = [lat, lng]
    },

    async calcRoute(ptArr) {
      console.log('Calculating current route', ptArr)
      const coords = ptArr.map(([la, lo]) => `${lo},${la}`).join(';')
      try {
        const res = await fetch(`http://localhost:8000/api/route?coords=${coords}`)
        const data = await res.json()
        this.route = data.routes[0].geometry.coordinates.map(p => [p[1], p[0]])
      }
      catch {
        this.route = null
      }
    }
  },

  mounted() {
    const resizeMap = () => {
      this.$nextTick(() => {
        const mapObj = this.$refs.mapRef?.mapObject
        if (mapObj) mapObj.invalidateSize()
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
