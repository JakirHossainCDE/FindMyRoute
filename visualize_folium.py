#!/usr/bin/env python
"""
visualize_folium.py

Generate a Folium map for FindMyRoute.

- Reads attractions from JSON/CSV produced by findmyroute.py (extract_attractions).
- Adds category-colored markers with Font Awesome icons.
- Optionally fetches POIs (cafes, parks) from OSM via osmnx.
- Optionally draws an optimized route if a GeoJSON is provided.
- Exports a single self-contained HTML map you can publish (e.g., GitHub Pages).
"""

from __future__ import annotations

import argparse
import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import folium
from folium.plugins import MarkerCluster, Fullscreen, MiniMap, MeasureControl

# --- Defaults ---
DEFAULT_CENTER = (47.8095, 13.0550)
DEFAULT_ZOOM = 14

# --- Category styling ---
ICON_STYLE: Dict[str, Dict[str, str]] = {
    "Landmark":      {"icon": "landmark",       "color": "blue"},
    "Museum":        {"icon": "university",     "color": "purple"},
    "Historic Site": {"icon": "building",       "color": "darkgreen"},
    "Memorial":      {"icon": "flag",           "color": "darkpurple"},
    "Park":          {"icon": "tree",           "color": "green"},
    "Shopping":      {"icon": "shopping-bag",   "color": "pink"},
    "Religious Site":{"icon": "place-of-worship","color": "orange"},
    "Viewpoint":     {"icon": "binoculars",     "color": "cadetblue"},
    "Attraction":    {"icon": "info-circle",    "color": "gray"},
}

# ---------- I/O helpers ----------

def load_attractions(input_path: Path) -> List[Dict]:
    if not input_path.exists():
        raise FileNotFoundError(f"Attractions file not found: {input_path}")

    if input_path.suffix.lower() == ".json":
        data = json.loads(input_path.read_text(encoding="utf-8"))
        result = []
        for i, a in enumerate(data, start=1):
            lat = a.get("lat") or a.get("latitude")
            lng = a.get("lng") or a.get("longitude")
            if lat is None or lng is None:
                continue
            result.append({
                "id": a.get("id", i),
                "name": a.get("name", f"Attraction {i}"),
                "lat": float(lat),
                "lng": float(lng),
                "category": a.get("category", "Attraction"),
                "icon": a.get("icon") or None
            })
        return result

    result = []
    with input_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            name = row.get("name") or row.get("Name") or row.get("attraction") or f"Attraction {i}"
            lat = row.get("lat") or row.get("latitude") or row.get("Latitude")
            lng = row.get("lng") or row.get("longitude") or row.get("Longitude")
            if not lat or not lng:
                continue
            category = row.get("category") or row.get("type") or "Attraction"
            icon = row.get("icon") or None
            result.append({
                "id": i,
                "name": name,
                "lat": float(lat),
                "lng": float(lng),
                "category": category,
                "icon": icon
            })
    return result


def load_route_geojson(route_path: Path) -> Optional[List[Tuple[float, float]]]:
    if not route_path or not route_path.exists():
        return None
    data = json.loads(route_path.read_text(encoding="utf-8"))
    coords = []

    def _coords_to_latlng(c):
        return (float(c[1]), float(c[0]))

    try:
        geom_type = data.get("features", [{}])[0]["geometry"]["type"]
        geometry = data["features"][0]["geometry"]
        if geom_type == "LineString":
            coords = [_coords_to_latlng(c) for c in geometry["coordinates"]]
        elif geom_type == "MultiLineString":
            for line in geometry["coordinates"]:
                coords.extend([_coords_to_latlng(c) for c in line])
        return coords if coords else None
    except Exception as e:
        print(f"[WARN] Failed to parse route GeoJSON: {e}")
        return None


# ---------- Map builders ----------

def make_base_map(center: Tuple[float, float], zoom: int = DEFAULT_ZOOM) -> folium.Map:
    m = folium.Map(location=center, zoom_start=zoom, tiles=None, control_scale=True)
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap", control=True).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="Esri Satellite",
        attr="Tiles © Esri",
        control=True,
    ).add_to(m)
    folium.TileLayer("cartodb positron", name="CartoDB Positron", control=True).add_to(m)

    Fullscreen().add_to(m)
    MiniMap(toggle_display=True).add_to(m)

    return m


def _icon_for_category(category: str) -> Tuple[str, str]:
    meta = ICON_STYLE.get(category, ICON_STYLE["Attraction"])
    return meta["icon"], meta["color"]


def add_attractions_layer(m: folium.Map, attractions: List[Dict], cluster: bool = True) -> None:
    groups: Dict[str, folium.FeatureGroup] = {}
    clusters: Dict[str, MarkerCluster] = {}

    for a in attractions:
        cat = a.get("category", "Attraction")
        icon_name, color = _icon_for_category(cat)

        if cat not in groups:
            groups[cat] = folium.FeatureGroup(name=f"{cat}", show=True)
            if cluster:
                clusters[cat] = MarkerCluster(name=f"{cat} (cluster)")
                clusters[cat].add_to(groups[cat])
            groups[cat].add_to(m)

        popup_html = f"<b>{a.get('name','Attraction')}</b><br>{cat}"
        marker = folium.Marker(
            location=[a["lat"], a["lng"]],
            popup=popup_html,
            icon=folium.Icon(color=color, icon=icon_name, prefix="fa"),
        )
        if cluster:
            clusters[cat].add_child(marker)
        else:
            groups[cat].add_child(marker)


def add_route_polyline(m: folium.Map, coords_latlng: List[Tuple[float, float]], name: str = "Optimized Route",
                       color: str = "#007BFF", weight: int = 6, opacity: float = 0.8) -> None:
    if not coords_latlng:
        return
    folium.PolyLine(locations=coords_latlng, color=color, weight=weight, opacity=opacity, tooltip=name).add_to(m)
    sw = (min(lat for lat, _ in coords_latlng), min(lng for _, lng in coords_latlng))
    ne = (max(lat for lat, _ in coords_latlng), max(lng for _, lng in coords_latlng))
    m.fit_bounds([sw, ne])


# ---------- Main ----------

def main():
    parser = argparse.ArgumentParser(description="Generate a Folium map for FindMyRoute.")
    parser.add_argument("--city", default="Salzburg, Austria")
    parser.add_argument("--input", required=False, default="output/salzburg_austria_attractions.json")
    parser.add_argument("--route", required=False, default=None)
    parser.add_argument("--add-pois", action="store_true")
    parser.add_argument("--out", default="maps/findmyroute_salzburg.html")
    args = parser.parse_args()

    input_path = Path(args.input)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    attractions = load_attractions(input_path)
    if not attractions:
        raise SystemExit("[ERROR] No attractions loaded. Check your input file.")

    mean_lat = sum(a["lat"] for a in attractions) / len(attractions)
    mean_lng = sum(a["lng"] for a in attractions) / len(attractions)
    center = (mean_lat, mean_lng)

    m = make_base_map(center=center, zoom=DEFAULT_ZOOM)
    add_attractions_layer(m, attractions, cluster=False)

    if args.route:
        route_coords = load_route_geojson(Path(args.route))
        if route_coords:
            add_route_polyline(m, route_coords)

    folium.LayerControl(collapsed=True).add_to(m)

    # --- Full-width header ---
    header_html = f"""
    <div style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: rgba(25, 118, 210, 0.95);
        color: white;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        font-family: 'Segoe UI', Tahoma, sans-serif;
        padding: 12px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.25);
        z-index: 9999;
    ">
        FindMyRoute – {args.city}
    </div>
    """
    m.get_root().html.add_child(folium.Element(header_html))

    # --- Push top-left controls below header ---
    header_height = 60  # px
    css_offset = f"""
    <style>
        .leaflet-top.leaflet-left,
        .leaflet-control.measure,
        .leaflet-control-minimap {{
            top: {header_height}px !important;
        }}
    </style>
    """
    m.get_root().html.add_child(folium.Element(css_offset))

    layer_control_css = """
    <style>
    .leaflet-control-layers {
        margin-top: 60px !important; /* move it below header */
    }
    </style>
    """
    m.get_root().html.add_child(folium.Element(layer_control_css))


    m.save(str(out_path))
    print(f"✓ Map saved to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
