// src/boot/leaflet.js
import { boot } from 'quasar/wrappers'
import L from 'leaflet'

import 'leaflet/dist/leaflet.css'
import 'leaflet.heat'                // <-- importamos el plugin tras haber traído L

// Importar los assets de los iconos como ES Modules
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png'
import iconUrl       from 'leaflet/dist/images/marker-icon.png'
import shadowUrl     from 'leaflet/dist/images/marker-shadow.png'

// Ajustar la ruta de los iconos por defecto de Leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl,
  iconUrl,
  shadowUrl
})
window.L = L
export default boot(({ app }) => {
  // no necesitas nada más aquí
})
