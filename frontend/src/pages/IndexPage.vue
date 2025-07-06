<template>
  <q-page class="column items-center q-pa-md">
    <h4>Mini‐Maps con Quasar + Leaflet</h4>

    <div class="q-mb-md" style="width: 100%; max-width: 500px;">
      <q-input v-model="from" label="Origen (lon,lat)" outlined />
      <q-input v-model="to"   label="Destino (lon,lat)" outlined class="q-mt-sm"/>
      <q-btn color="primary" label="Calcular ruta" @click="calcRoute" class="q-mt-sm" />
    </div>

        <div style="width: 100%; max-width: 800px; height: 500px;">
      <l-map
        :use-global-leaflet="false"
        :zoom="zoom"
        :center="center"
        style="height: 100%; width: 100%"
      >
        <l-tile-layer :url="tileUrl" />
        <l-polyline v-if="route" :lat-lngs="route" />
      </l-map>
    </div>

  </q-page>
</template>

<script>
import { LMap, LTileLayer, LPolyline } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'

export default {
  name: 'PageIndex',
  components: { LMap, LTileLayer, LPolyline },
  data() {
    return {
      from: '-78.467838,-0.180653',  // Por defecto Quito
      to:   '-78.500000,-0.200000',
      tileUrl: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      zoom:  13,
      center: [ -0.180653, -78.467838 ], // [lat, lon]
      route: null
    }
  },
  methods: {
    async calcRoute() {
      try {
        const coords = `${this.from};${this.to}`
        const res = await fetch(`http://localhost:8000/api/route?coords=${coords}`)
        const data = await res.json()
        const coordsGeo = data.routes[0].geometry.coordinates
        // Transformar [lon,lat] → [lat,lon]
        this.route = coordsGeo.map(pt => [pt[1], pt[0]])
        // Centrar en el origen
        const [lon, lat] = this.from.split(',').map(Number)
        this.center = [lat, lon]
      }
      catch (err) {
        console.error(err)
        this.$q.notify({ type: 'negative', message: 'Error calculando ruta' })
      }
    }
  }
}
</script>

