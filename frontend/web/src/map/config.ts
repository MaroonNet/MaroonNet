import type { ViewState } from 'react-map-gl/maplibre'

// Online basemap for now; swap for local tiles once the team settles the tile format
export const MAP_STYLE_URL = 'https://tiles.openfreemap.org/styles/liberty'

// Placeholder center (Denver) until the search region is picked.
export const INITIAL_VIEW: Pick<ViewState, 'longitude' | 'latitude' | 'zoom'> = {
    longitude: -105.0,
    latitude: 39.74,
    zoom: 11
}

