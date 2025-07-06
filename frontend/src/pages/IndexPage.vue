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
          v-if="route"
          :lat-lngs="route"
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
      default: null
    }
  },

  data() {
    return {
      zoom: 13,
      center: [ -0.180653, -78.467838 ],  // Quito
      tileUrl: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      points: [],
      route: null
    }
  },

  watch: {
    currentRoute: {
      handler(route) {
        if (route) {
          // cargar puntos de la ruta seleccionada
          this.points = route.points.slice()
          if (this.points.length >= 2) {
            this.calcRoute(this.points)
          } else {
            this.route = null
          }
        }
        else {
          this.points = []
          this.route  = null
        }
      },
      immediate: true
    }
  },

  methods: {
    onMapClick(evt) {
      const { lat, lng } = evt.latlng
      this.points.push([lat, lng])
      this.$emit('update-route', this.points)

      if (this.points.length >= 2) {
        this.calcRoute(this.points)
      }
      this.center = [lat, lng]
    },

    async calcRoute(ptArr) {
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
    // Forzar recálculo inicial y al hacer resize (drawer toggle)
    const resizeMap = () => {
      this.$nextTick(() => {
        const mapObj = this.$refs.mapRef?.mapObject
        if (mapObj) mapObj.invalidateSize()
      })
    }

    // Una primera vez tras cargar
    setTimeout(resizeMap, 300)
    // Cada vez que cambie el tamaño de ventana
    window.addEventListener('resize', resizeMap)
  },

  beforeUnmount() {
    window.removeEventListener('resize', this.resizeMap)
  }
}
</script>

<style scoped>
.full-page {
  /* ya no la usamos */
}
.q-page.no-padding {
  padding: 0 !important;
}
</style>
