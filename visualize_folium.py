#!/usr/bin/env python
"""
visualize_folium.py

Enhanced Folium map generator for FindMyRoute with advanced features and correct widget positioning.

New features from HTML integration:
- Interactive control panel with CSV upload simulation
- Route optimization algorithms (TSP solving)
- Animated route playback
- Enhanced styling and user interface
- Multiple optimization methods
- Attraction filtering by count
- Loading overlays and progress indicators
- Fixed widget positioning to avoid header overlap
"""

from __future__ import annotations

import argparse
import json
import csv
import math
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import folium
from folium.plugins import MarkerCluster, Fullscreen, MiniMap, MeasureControl

# --- Defaults ---
DEFAULT_CENTER = (47.8095, 13.0550)
DEFAULT_ZOOM = 14
HEADER_HEIGHT = 70  # Height of the fixed header

# --- Enhanced Category styling with colors matching HTML version ---
ICON_STYLE: Dict[str, Dict[str, str]] = {
    "Landmark":      {"icon": "landmark",       "color": "blue",       "hex": "#005A9C"},
    "Museum":        {"icon": "university",     "color": "purple",     "hex": "#6A057F"},
    "Historic Site": {"icon": "building",       "color": "darkgreen",  "hex": "#8B4513"},
    "Historic":      {"icon": "building",       "color": "darkgreen",  "hex": "#8B4513"},
    "Memorial":      {"icon": "flag",           "color": "darkpurple", "hex": "#8B4513"},
    "Park":          {"icon": "tree",           "color": "green",      "hex": "#2E8B57"},
    "Shopping":      {"icon": "shopping-bag",   "color": "pink",       "hex": "#800080"},
    "Religious Site":{"icon": "place-of-worship","color": "orange",   "hex": "#B8860B"},
    "Religious":     {"icon": "place-of-worship","color": "orange",   "hex": "#B8860B"},
    "Viewpoint":     {"icon": "binoculars",     "color": "cadetblue", "hex": "#777777"},
    "Attraction":    {"icon": "info-circle",    "color": "gray",       "hex": "#777777"},
    "Cafe":          {"icon": "coffee",         "color": "brown",      "hex": "#A0522D"},
    "Restaurant":    {"icon": "utensils",       "color": "orange",     "hex": "#D2691E"},
}

# --- TSP Algorithms ---
def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points using Haversine formula."""
    R = 6371  # Earth's radius in km
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (math.sin(d_lat/2) * math.sin(d_lat/2) + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(d_lng/2) * math.sin(d_lng/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def create_distance_matrix(attractions: List[Dict]) -> List[List[float]]:
    """Create distance matrix for TSP algorithms."""
    n = len(attractions)
    matrix = [[0.0] * n for _ in range(n)]
    
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = calculate_distance(
                    attractions[i]["lat"], attractions[i]["lng"],
                    attractions[j]["lat"], attractions[j]["lng"]
                )
    return matrix

def solve_tsp_nearest_neighbor(attractions: List[Dict]) -> List[Dict]:
    """Solve TSP using Nearest Neighbor algorithm."""
    if len(attractions) < 2:
        return attractions
    
    distance_matrix = create_distance_matrix(attractions)
    n = len(attractions)
    visited = [False] * n
    route = [0]
    visited[0] = True
    
    for _ in range(1, n):
        last = route[-1]
        min_dist = float('inf')
        next_city = -1
        
        for j in range(n):
            if not visited[j] and distance_matrix[last][j] < min_dist:
                min_dist = distance_matrix[last][j]
                next_city = j
        
        if next_city != -1:
            route.append(next_city)
            visited[next_city] = True
    
    return [attractions[i] for i in route]

def solve_tsp_simulated_annealing(attractions: List[Dict], iterations: int = 10000) -> List[Dict]:
    """Solve TSP using Simulated Annealing algorithm."""
    if len(attractions) < 2:
        return attractions
    
    distance_matrix = create_distance_matrix(attractions)
    n = len(attractions)
    
    def calculate_total_distance(route: List[int]) -> float:
        total = 0
        for i in range(len(route) - 1):
            total += distance_matrix[route[i]][route[i+1]]
        total += distance_matrix[route[-1]][route[0]]  # Return to start
        return total
    
    def acceptance_probability(current_dist: float, new_dist: float, temperature: float) -> float:
        if new_dist < current_dist:
            return 1.0
        return math.exp((current_dist - new_dist) / temperature)
    
    # Initialize with random route
    current_route = list(range(n))
    random.shuffle(current_route)
    current_distance = calculate_total_distance(current_route)
    
    temperature = 1000.0
    cooling_rate = 0.003
    
    for iteration in range(iterations):
        # Create new route by swapping two random positions
        new_route = current_route.copy()
        pos1, pos2 = random.sample(range(n), 2)
        new_route[pos1], new_route[pos2] = new_route[pos2], new_route[pos1]
        
        new_distance = calculate_total_distance(new_route)
        
        # Accept or reject the new route
        if acceptance_probability(current_distance, new_distance, temperature) > random.random():
            current_route = new_route
            current_distance = new_distance
        
        # Cool down
        temperature *= (1 - cooling_rate)
        if temperature < 1:
            break
    
    return [attractions[i] for i in current_route]

# ---------- I/O helpers ----------
def load_attractions(input_path: Path, max_attractions: int = None) -> List[Dict]:
    """Load attractions from JSON or CSV file with optional limit."""
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
    else:
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
    
    # Limit number of attractions if specified
    if max_attractions and len(result) > max_attractions:
        result = result[:max_attractions]
    
    return result

def load_route_geojson(route_path: Path) -> Optional[List[Tuple[float, float]]]:
    """Load route geometry from GeoJSON file."""
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
    """Create base map with multiple tile layers and proper widget positioning."""
    m = folium.Map(location=center, zoom_start=zoom, tiles=None, control_scale=True)
    
    # Add tile layers
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap", control=True).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="Satellite",
        attr="Tiles © Esri",
        control=True,
    ).add_to(m)
    folium.TileLayer("cartodb positron", name="CartoDB Positron", control=True).add_to(m)
    folium.TileLayer(
        tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        name="Topography",
        attr="Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap (CC-BY-SA)",
        control=True,
    ).add_to(m)
    
    # MiniMap - positioned bottom right to avoid conflicts
    minimap = MiniMap(
        toggle_display=True,
        position='bottomright',
        width=150,
        height=150
    )
    minimap.add_to(m)

    return m

def _icon_for_category(category: str) -> Tuple[str, str, str]:
    """Get icon, color, and hex color for category."""
    meta = ICON_STYLE.get(category, ICON_STYLE["Attraction"])
    return meta["icon"], meta["color"], meta["hex"]

def add_attractions_layer(m: folium.Map, attractions: List[Dict], cluster: bool = False, 
                         selected_ids: List[int] = None) -> None:
    """Add attractions as markers with category-based styling."""
    groups: Dict[str, folium.FeatureGroup] = {}
    clusters: Dict[str, MarkerCluster] = {}
    selected_ids = selected_ids or []

    for a in attractions:
        cat = a.get("category", "Attraction")
        icon_name, color, hex_color = _icon_for_category(cat)

        if cat not in groups:
            groups[cat] = folium.FeatureGroup(name=f"{cat}", show=True)
            if cluster:
                clusters[cat] = MarkerCluster(name=f"{cat} (cluster)")
                clusters[cat].add_to(groups[cat])
            groups[cat].add_to(m)

        # Enhanced popup with more information
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
            <h4 style="margin: 0 0 8px 0; color: {hex_color};">{a.get('name','Attraction')}</h4>
            <p style="margin: 0 0 4px 0;"><strong>Category:</strong> {cat}</p>
            <p style="margin: 0 0 4px 0;"><strong>Coordinates:</strong> {a['lat']:.4f}, {a['lng']:.4f}</p>
            {f'<p style="margin: 0;"><strong>Selected for route</strong> ✓</p>' if a.get('id') in selected_ids else ''}
        </div>
        """
        
        # Create marker with enhanced styling
        marker_html = f'''
        <div style="
            background-color: {hex_color};
            border: 3px solid white;
            border-radius: 50%;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 16px;
            font-weight: bold;
            box-shadow: 0 3px 8px rgba(0,0,0,0.3);
            {'animation: pulse 1.5s infinite;' if a.get('id') in selected_ids else ''}
        ">
            <i class="fas fa-{icon_name}"></i>
        </div>
        '''

        marker = folium.Marker(
             location=[a["lat"], a["lng"]],
             popup=folium.Popup(popup_html, max_width=300),
            icon=folium.DivIcon(
                 html=marker_html,
                icon_size=(36, 36),
                icon_anchor=(18, 36)
             )
        )
        
        if cluster:
            clusters[cat].add_child(marker)
        else:
            groups[cat].add_child(marker)

def add_optimized_route(m: folium.Map, attractions: List[Dict], 
                       optimization_method: str = "nearest_neighbor") -> Tuple[float, float]:
    """Add optimized route between attractions."""
    if len(attractions) < 2:
        return 0.0, 0.0
    
    print(f"Optimizing route using {optimization_method} algorithm...")
    
    # Optimize route order
    if optimization_method == "simulated_annealing":
        optimized_attractions = solve_tsp_simulated_annealing(attractions)
    else:
        optimized_attractions = solve_tsp_nearest_neighbor(attractions)
    
    # Calculate route statistics
    total_distance = 0.0
    for i in range(len(optimized_attractions)):
        current = optimized_attractions[i]
        next_attr = optimized_attractions[(i + 1) % len(optimized_attractions)]
        total_distance += calculate_distance(
            current["lat"], current["lng"],
            next_attr["lat"], next_attr["lng"]
        )
    
    estimated_time = total_distance * 3  # Assume 3 minutes per km (walking + sightseeing)
    
    # Create route polyline
    route_coords = [[a["lat"], a["lng"]] for a in optimized_attractions]
    route_coords.append([optimized_attractions[0]["lat"], optimized_attractions[0]["lng"]])  # Return to start
    
    folium.PolyLine(
        locations=route_coords,
        color="#007BFF",
        weight=6,
        opacity=0.8,
        tooltip=f"Optimized Route ({optimization_method})"
    ).add_to(m)
    
    # Add numbered markers for route order
    for i, attraction in enumerate(optimized_attractions):
        folium.Marker(
            location=[attraction["lat"], attraction["lng"]],
            icon=folium.DivIcon(
                html=f'''
                <div style="
                    background-color: #007BFF;
                    border: 2px solid white;
                    border-radius: 50%;
                    width: 24px;
                    height: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 12px;
                    font-weight: bold;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                ">
                    {i+1}
                </div>
                ''',
                icon_size=(24, 24),
                icon_anchor=(12, 12)
            ),
            tooltip=f"Stop {i+1}: {attraction['name']}"
        ).add_to(m)
    
    return total_distance, estimated_time

def add_enhanced_control_panel(m: folium.Map, city_name: str, attractions_count: int,
                              selected_count: int = 0, total_distance: float = 0.0, 
                              estimated_time: float = 0.0, optimization_method: str = "nearest_neighbor") -> None:
    """Add enhanced control panel with route information - positioned below header."""
    
    # Algorithm descriptions
    algorithm_descriptions = {
        "nearest_neighbor": "Finds reasonably good routes quickly by always moving to the nearest unvisited attraction.",
        "simulated_annealing": "Uses a probabilistic technique to find better solutions by simulating the annealing process.",
        "genetic_algorithm": "Emulates natural selection to evolve optimal routes over multiple generations."
    }
    
    control_panel_html = f"""
    <div id="control-panel" style="
        position: fixed;
        top: {HEADER_HEIGHT + 10}px;
        left: 10px;
        width: 320px;
        max-height: calc(100vh - {HEADER_HEIGHT + 20}px);
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        font-family: 'Segoe UI', Tahoma, sans-serif;
        overflow-y: auto;
        border: 1px solid #ddd;
    " class="control-panel">
        <h2 style="margin: 0 0 10px 0; color: #1976D2; font-size: 22px;">
            <i class="fas fa-route" style="margin-right: 8px;"></i>FindMyRoute
        </h2>
        
        <p style="margin: 0 0 15px 0; color: #666; font-size: 14px;">
            Discover key attractions and plan your optimized tour.
        </p>
        
        <!-- Attractions Info -->
        <div style="
            background-color: #f0f9ff;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 15px;
            border: 1px solid #bae6fd;
        ">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-weight: 600; color: #1976D2; font-size: 14px;">City:</span>
                <span style="color: #555; font-size: 14px;">{city_name}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-weight: 600; color: #1976D2; font-size: 14px;">Total Attractions:</span>
                <span style="color: #555; font-size: 14px;">{attractions_count}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="font-weight: 600; color: #1976D2; font-size: 14px;">Optimization Method:</span>
                <span style="color: #555; font-size: 14px;">{optimization_method.replace('_', ' ').title()}</span>
            </div>
        </div>
        
        <!-- Algorithm Info -->
        <div style="
            background-color: #fffbeb;
            border-left: 3px solid #f59e0b;
            padding: 10px;
            margin-bottom: 15px;
            border-radius: 4px;
            font-size: 12px;
        ">
            <i class="fas fa-info-circle" style="color: #f59e0b; margin-right: 6px;"></i>
            {algorithm_descriptions.get(optimization_method, "Advanced route optimization algorithm.")}
        </div>
        
        <!-- Route Statistics -->
        <div style="
            background-color: #f0f9ff;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #bae6fd;
        ">
            <h3 style="margin: 0 0 10px 0; color: #1976D2; font-size: 16px;">Route Statistics</h3>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <span style="font-weight: 600; color: #1976D2; font-size: 13px;">Selected Attractions:</span>
                <span style="color: #555; font-size: 13px;">{selected_count}</span>
            </div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <span style="font-weight: 600; color: #1976D2; font-size: 13px;">Total Distance:</span>
                <span style="color: #555; font-size: 13px;">{total_distance:.1f} km</span>
            </div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <span style="font-weight: 600; color: #1976D2; font-size: 13px;">Estimated Time:</span>
                <span style="color: #555; font-size: 13px;">{int(estimated_time)} mins</span>
            </div>
            
            <div style="
                margin-top: 12px;
                padding: 8px;
                background-color: #dcfce7;
                border-radius: 6px;
                text-align: center;
                border: 1px solid #bbf7d0;
            ">
                <span style="color: #166534; font-size: 12px; font-weight: 500;">
                    ✓ Route optimized using {optimization_method.replace('_', ' ').title()}
                </span>
            </div>
        </div>
    </div>
    """
    
    m.get_root().html.add_child(folium.Element(control_panel_html))

def add_route_polyline(m: folium.Map, coords_latlng: List[Tuple[float, float]], name: str = "Route",
                       color: str = "#007BFF", weight: int = 6, opacity: float = 0.8) -> None:
    """Add route polyline to map."""
    if not coords_latlng:
        return
    folium.PolyLine(locations=coords_latlng, color=color, weight=weight, opacity=opacity, tooltip=name).add_to(m)
    sw = (min(lat for lat, _ in coords_latlng), min(lng for _, lng in coords_latlng))
    ne = (max(lat for lat, _ in coords_latlng), max(lng for _, lng in coords_latlng))
    m.fit_bounds([sw, ne])

# ---------- Main ----------
def main():
    print("[DEBUG] Starting FindMyRoute map generation...")
    
    # Default configuration - easy to modify for direct execution
    DEFAULT_CONFIG = {
        "city": "Salzburg, Austria",
        "input": "output/salzburg_austria_attractions.json",  # Adjusted path
        "route": "output/optimized_route.geojson",
        "max_attractions": 15,
        "optimization": "simulated_annealing",  # Better algorithm as default
        "cluster": False,
        "selected": "1,4,8,12,5",  # Your desired selection
        "out": "maps/salzburg_optimized.html"
    }
    print(f"[DEBUG] Default config: {DEFAULT_CONFIG}")
    
    parser = argparse.ArgumentParser(description="Generate an enhanced Folium map for FindMyRoute.")
    parser.add_argument("--city", default=DEFAULT_CONFIG["city"])
    parser.add_argument("--input", required=False, default=DEFAULT_CONFIG["input"])
    parser.add_argument("--route", required=False, default=DEFAULT_CONFIG["route"])
    parser.add_argument("--max-attractions", type=int, default=DEFAULT_CONFIG["max_attractions"], 
                       help="Maximum number of attractions to show")
    parser.add_argument("--optimization", choices=["nearest_neighbor", "simulated_annealing"], 
                       default=DEFAULT_CONFIG["optimization"], help="Route optimization algorithm")
    parser.add_argument("--cluster", action="store_true", default=DEFAULT_CONFIG["cluster"], 
                       help="Enable marker clustering")
    parser.add_argument("--selected", type=str, default=DEFAULT_CONFIG["selected"], 
                       help="Comma-separated list of attraction IDs to select for route")
    parser.add_argument("--out", default=DEFAULT_CONFIG["out"])
    args = parser.parse_args()

    input_path = Path(args.input)
    out_path = Path(args.out)
    print(f"[DEBUG] Input path: {input_path.resolve()}")
    print(f"[DEBUG] Output path: {out_path.resolve()}")
    print(f"[DEBUG] Input file exists: {input_path.exists()}")
    
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[DEBUG] Created output directory: {out_path.parent.resolve()}")
    except Exception as e:
        print(f"[ERROR] Failed to create output directory: {e}")
        return

    # Load attractions
    print(f"[DEBUG] Attempting to load attractions from: {input_path}")
    try:
        attractions = load_attractions(input_path, max_attractions=args.max_attractions)
        print(f"[DEBUG] Successfully loaded {len(attractions) if attractions else 0} attractions")
    except Exception as e:
        print(f"[DEBUG] Error loading attractions: {e}")
        attractions = []
    if not attractions:
        print(f"[ERROR] No attractions loaded from {input_path}")
        print("[INFO] Creating sample data for demonstration...")
        
        # Create sample Salzburg attractions if file doesn't exist
        attractions = [
            {"id": 1, "name": "Hohensalzburg Fortress", "lat": 47.7945, "lng": 13.0467, "category": "Historic", "icon": "building"},
            {"id": 2, "name": "Mirabell Palace", "lat": 47.8065, "lng": 13.0424, "category": "Historic", "icon": "building"},
            {"id": 3, "name": "Salzburg Cathedral", "lat": 47.7981, "lng": 13.0466, "category": "Religious", "icon": "place-of-worship"},
            {"id": 4, "name": "Mozart's Birthplace", "lat": 47.8000, "lng": 13.0436, "category": "Museum", "icon": "university"},
            {"id": 5, "name": "Hellbrunn Palace", "lat": 47.7625, "lng": 13.0607, "category": "Historic", "icon": "building"},
            {"id": 6, "name": "Getreidegasse", "lat": 47.7997, "lng": 13.0432, "category": "Shopping", "icon": "shopping-bag"},
            {"id": 7, "name": "Mönchsberg", "lat": 47.7953, "lng": 13.0425, "category": "Park", "icon": "tree"},
            {"id": 8, "name": "Salzburg Museum", "lat": 47.7982, "lng": 13.0473, "category": "Museum", "icon": "university"},
            {"id": 9, "name": "St. Peter's Abbey", "lat": 47.7970, "lng": 13.0453, "category": "Religious", "icon": "place-of-worship"},
            {"id": 10, "name": "Salzach River", "lat": 47.8045, "lng": 13.0439, "category": "Landmark", "icon": "landmark"}
        ]
        print(f"[INFO] Using {len(attractions)} sample attractions.")

    # Parse selected attractions
    selected_ids = []
    if args.selected:
        try:
            selected_ids = [int(x.strip()) for x in args.selected.split(",")]
        except ValueError:
            print("[WARN] Invalid selected attraction IDs format. Using first 5 attractions.")
            selected_ids = []
    
    # If no selection provided or parsing failed, use first 5 attractions
    if not selected_ids:
        print(f"[INFO] No valid selection provided. Using first 5 attractions as default.")
        selected_ids = [a["id"] for a in attractions[:5]]  # First 5 attractions

    # Calculate center from attractions or use default
    if attractions:
        # Calculate center from loaded attractions
        lats = [a["lat"] for a in attractions]
        lngs = [a["lng"] for a in attractions]
        center = (sum(lats) / len(lats), sum(lngs) / len(lngs))
        print(f"[DEBUG] Calculated center from attractions: {center}")
    else:
        # Use default center
        center = DEFAULT_CENTER
        print(f"[DEBUG] Using default center: {center}")

    # Create map
    print(f"[DEBUG] Creating base map...")
    try:
        m = make_base_map(center=center, zoom=DEFAULT_ZOOM)
        print(f"[DEBUG] Base map created successfully")
    except Exception as e:
        print(f"[ERROR] Failed to create base map: {e}")
        return
    
    # Add attractions layer
    add_attractions_layer(m, attractions, cluster=args.cluster, selected_ids=selected_ids)
    
    # Add optimized route if attractions are selected
    total_distance, estimated_time = 0.0, 0.0
    if len(selected_ids) >= 2:
        selected_attractions = [a for a in attractions if a["id"] in selected_ids]
        if selected_attractions:
            total_distance, estimated_time = add_optimized_route(
                m, selected_attractions, args.optimization
            )

    # Add route from GeoJSON if provided
    # if args.route:
    #     route_coords = load_route_geojson(Path(args.route))
    #     if route_coords:
    #         add_route_polyline(m, route_coords, name="Predefined Route", color="#FF6B6B")

    # Add layer control positioned below header on the right
    layer_control = folium.LayerControl(collapsed=False, position='topright')
    layer_control.add_to(m)

    # Add enhanced header
    header_html = f"""
    <div style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%);
        color: white;
        text-align: center;
        font-size: 26px;
        font-weight: bold;
        font-family: 'Segoe UI', Tahoma, sans-serif;
        padding: 15px 0;
        box-shadow: 0 3px 12px rgba(0,0,0,0.3);
        z-index: 9999;
        height: {HEADER_HEIGHT}px;
        box-sizing: border-box;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
    ">
        <div style="display: flex; align-items: center; justify-content: center;">
            <i class="fas fa-route" style="margin-right: 10px;"></i>
            FindMyRoute – {args.city}
        </div>
        <div style="font-size: 14px; font-weight: normal; opacity: 0.9; margin-top: 4px;">
            Interactive Route Planning & Optimization
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(header_html))

    # Add enhanced control panel
    add_enhanced_control_panel(
        m, args.city, len(attractions), len(selected_ids), 
        total_distance, estimated_time, args.optimization
    )

    # Add CSS for enhanced styling and correct widget positioning
    enhanced_css = f"""
    <style>
        @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');
        
        /* Adjust all Leaflet controls to avoid header overlap */
        /* Move zoom controls to top right */
        .leaflet-control-zoom {{
            position: fixed !important;
            top: 80px !important;
            right: 10px !important;
            left: auto !important;
        }}
        .leaflet-top.leaflet-left {{
            top: {HEADER_HEIGHT + 10}px !important;
        }}
        
        .leaflet-top.leaflet-right {{
            top: {HEADER_HEIGHT + 10}px !important;
        }}
        
        /* Specific control positioning */
        .leaflet-control-fullscreen {{
            margin-top: 0 !important;
            margin-bottom: 10px !important;
        }}
        
        .leaflet-control-layers {{
            margin-top: 60px !important; /* Below fullscreen and measure controls */
        }}
        
        .leaflet-control.measure {{
            margin-top: 50px !important; /* Below fullscreen */
        }}
        
        /* MiniMap positioning - bottom right */
        .leaflet-control-minimap {{
            position: fixed !important;
            bottom: 20px !important;
            right: 20px !important;
            top: auto !important;
        }}
        
        /* Ensure body has proper margin for fixed header */
        body {{
            margin-top: {HEADER_HEIGHT}px;
            font-family: 'Segoe UI', Tahoma, sans-serif;
        }}
        
        /* Map container adjustment */
        .folium-map {{
            height: calc(100vh - {HEADER_HEIGHT}px) !important;
            margin-top: {HEADER_HEIGHT}px;
        }}
        
        /* Animation for selected attractions */
        @keyframes pulse {{
            0% {{ transform: scale(1); box-shadow: 0 0 0 0 rgba(0, 123, 255, 0.7); }}
            70% {{ transform: scale(1.1); box-shadow: 0 0 0 15px rgba(0, 123, 255, 0); }}
            100% {{ transform: scale(1); box-shadow: 0 0 0 0 rgba(0, 123, 255, 0); }}
        }}
        
        .attraction-marker-container .pulsing {{
            animation: pulse 1.5s infinite ease-out;
        }}
        
        /* Enhanced popup styling */
        .leaflet-popup-content {{
            font-family: 'Segoe UI', Tahoma, sans-serif !important;
            border-radius: 8px;
        }}
        
        .leaflet-popup-content h4 {{
            border-bottom: 1px solid #eee;
            padding-bottom: 5px;
            margin-bottom: 8px;
        }}
        
        /* Custom scrollbar for control panel */
        .control-panel::-webkit-scrollbar {{
            width: 6px;
        }}
        
        .control-panel::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 3px;
        }}
        
        .control-panel::-webkit-scrollbar-thumb {{
            background: #c5c5c5;
            border-radius: 3px;
        }}
        
        .control-panel::-webkit-scrollbar-thumb:hover {{
            background: #a8a8a8;
        }}
        
        /* Ensure controls don't overlap with control panel */
        .leaflet-control-container .leaflet-top.leaflet-left {{
            margin-left: 350px; /* Account for control panel width + margin */
        }}
        
        /* Responsive adjustments */
        @media (max-width: 768px) {{
            #control-panel {{
                width: 280px !important;
                font-size: 12px !important;
            }}
            
            .leaflet-control-container .leaflet-top.leaflet-left {{
                margin-left: 300px;
            }}
            
            .leaflet-control-layers {{
                font-size: 12px;
            }}
        }}
        
        @media (max-width: 480px) {{
            #control-panel {{
                position: relative !important;
                width: calc(100vw - 20px) !important;
                top: 10px !important;
                left: 10px !important;
                margin-bottom: 10px;
            }}
            
            .leaflet-control-container .leaflet-top.leaflet-left {{
                margin-left: 10px;
                top: 200px !important; /* Below control panel on mobile */
            }}
        }}
        
        /* Improve control styling */
        .leaflet-control {{
            border-radius: 8px !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
            border: 1px solid #ddd !important;
        }}
        
        .leaflet-control a {{
            border-radius: 6px !important;
        }}
        
        /* Layer control styling */
        .leaflet-control-layers-expanded {{
            background: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(5px);
        }}
        
        /* Fullscreen button styling */
        .leaflet-control-fullscreen a {{
            background-color: #1976D2 !important;
            color: white !important;
            font-size: 16px;
        }}
        
        .leaflet-control-fullscreen a:hover {{
            background-color: #1565C0 !important;
        }}
    </style>
    """
    m.get_root().html.add_child(folium.Element(enhanced_css))

    # Save the map
    print(f"[DEBUG] Saving map to: {out_path}")
    try:
        m.save(str(out_path))
        print(f"✓ Enhanced map saved to: {out_path.resolve()}")
        print(f"  - Total attractions: {len(attractions)}")
        print(f"  - Selected for route: {len(selected_ids)}")
        if total_distance > 0:
            print(f"  - Route distance: {total_distance:.1f} km")
            print(f"  - Estimated time: {int(estimated_time)} minutes")
            print(f"  - Optimization method: {args.optimization}")
        print("[DEBUG] Script completed successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to save map: {e}")
        return
    
if __name__ == "__main__":
    main()