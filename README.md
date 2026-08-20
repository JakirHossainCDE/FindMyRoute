# FindMyRoute: A City Path Optimizer

## Overview  of the Project

FindMyRoute is an interactive web application designed to help users discover and optimize travel paths through a city. The current implementation focuses on the city of Salzburg, Austria, but it is built to be extensible to any city by simply uploading a CSV file of attractions.

The application allows users to:

* Visualize key attractions on an interactive map using Leaflet.js.

* Upload a custom CSV file to load attractions for any city.

* Select a set of attractions and find the most efficient route connecting them.

* See key route metrics like total distance and estimated time.

* Animate the calculated route on the map to visualize the journey.

WebMap
<img width="1358" height="655" alt="image" src="https://github.com/user-attachments/assets/48d6cd76-402c-4b47-ba74-b50684ffe552" />

## Route Optimization Algorithms

This application solves the classic Traveling Salesperson Problem (TSP) to find the shortest path between selected attractions. It features three distinct optimization algorithms:

* **Nearest Neighbor:**  A fast heuristic algorithm for quick results.
* **Simulated Annealing:**  A metaheuristic approach for better, near-optimal solutions.
* **Genetic Algorithm:**  An evolutionary algorithm that "evolves" high-quality routes over generations.
  
## Technologies Used

### Frontend

* **HTML5:** For the core structure of the web page.

* **CSS3:** For styling, with a focus on a clean and modern user interface.

* **JavaScript:** Powers all interactive features, including map manipulation and route calculation.

* **Tailwind CSS:** A utility-first CSS framework for rapid UI development.

* **Leaflet.js:** An open-source JavaScript library for mobile-friendly interactive maps.

* **Leaflet Routing Machine:** A plugin for Leaflet to handle routing, distance, and time calculations.

* **Font Awesome:** For icons used throughout the interface.

* **PapaParse:** A powerful CSV parser for the browser to handle user file uploads.

### Backend (Python Scripts)

* **Python 3:** The scripting language for the backend data extraction.

* **OSMnx:** A Python library to download, construct, project, and visualize street networks from OpenStreetMap.

* **dataclasses:** Used to create simple, structured data objects for attractions.

* **json & csv:** Standard libraries for handling data serialization.

## Getting Started

### Prerequisites

To run the Python scripts for data extraction, you will need to have Python 3 installed. You can install the necessary libraries using `pip`:

```
pip install osmnx

```

### File Structure

The project is structured with the following key files:

* `index.html`: The main web page for the application {output folder}.

* `findmyroute.py`: A Python script for extracting and saving tourist attraction data from OpenStreetMap.

* `run_route.py`: A simple script to demonstrate how to run `findmyroute.py`.

### Running the Application

1. **Clone the Repository:**

   ```
   git clone https://github.com/JakirHossainCDE/FindMyRoute.git
   cd FindMyRoute
   
   ```

2. **Generate Attraction Data:**

   * The application is pre-configured with a small set of attractions, but you can generate a more comprehensive list using the Python script.

   * Run the `run_route.py` script to generate a `salzburg_austria_attractions.json` and a `salzburg_austria_attractions.csv` file in an `output` directory.

   ```
   python run_route.py
   
   ```

   * The `findmyroute.py` script can be modified to extract data for other cities by changing the `city` parameter in the `extract_attractions()` function.

3. **Open the Web Page:**

   * Simply open the `index.html` file in your web browser. The application will load and be ready to use.

## Usage

### Using the App

1. **Load Attractions:**

   * The app starts with a default list of Salzburg attractions.

   * To load a custom set of attractions, click the **"Upload Attractions CSV"** button and select a CSV file. The file should have columns for `name`, `latitude`, `longitude`, and optionally `category`.

2. **Select and Optimize:**

   * Use the slider to display a specific number of attractions on the map and in the list.

   * Click on attractions in the list to select them. Selected attractions are highlighted with a checkmark.

   * Once you have selected at least two attractions, click the **"Optimize Route"** button to calculate the shortest path connecting them. The route will be displayed on the map, and metrics like distance and time will be updated.

3. **Animate the Route:**

   * After optimizing a route, click the **"Animate Route"** button to watch a marker move along the calculated path.

## Code Details

### `index.html`

The `index.html` file contains the full frontend code, including HTML, CSS, and JavaScript. The CSS is handled with Tailwind and a dedicated `<style>` block for custom styles. The JavaScript is contained within a `<script>` tag at the bottom of the body. Key JavaScript functions include:

* `updateAttractionsListDisplay()`: Renders attraction markers on the map and populates the list in the control panel.

* `showOptimizedRoute()`: Uses the classic Traveling Salesperson Problem (TSP)  to calculate and display the route.

* `animateRoute()`: Animates a marker along the route's path.

### `findmyroute.py`

This script is responsible for the data collection and processing.

* It uses the `osmnx` library to query OpenStreetMap for tourism and amenity data for a specified city.

* It filters the results to ensure valid data and a consistent number of attractions (defaulting to 20).

* It categorizes attractions based on their tags and assigns a corresponding icon.

* Finally, it saves the processed data into both JSON and CSV formats.

### `run_route.py`

A simple wrapper script to make the `findmyroute.py` script easy to use. It imports the main function and calls it with a specified city name.

## Python/Folium Approach

### Installation Requirements

```bash
pip install folium
```

### Usage

#### Basic Usage
```bash
python visualize_folium.py
```

#### Advanced Usage
```bash
python visualize_folium.py \
    --city "Vienna, Austria" \
    --input "data/vienna_attractions.json" \
    --max-attractions 20 \
    --optimization "simulated_annealing" \
    --selected "1,3,5,7,9" \
    --out "maps/vienna_route.html"
```

### Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--city` | "Salzburg, Austria" | City name for display |
| `--input` | "output/salzburg_austria_attractions.json" | Input file (JSON/CSV) |
| `--route` | "output/optimized_route.geojson" | Optional route GeoJSON |
| `--max-attractions` | 15 | Maximum attractions to display |
| `--optimization` | "simulated_annealing" | Algorithm choice |
| `--cluster` | False | Enable marker clustering |
| `--selected` | "1,4,8,12,5" | Comma-separated attraction IDs |
| `--out` | "maps/salzburg_optimized.html" | Output HTML file |

### Input Data Formats

#### JSON Format
```json
[
    {
        "id": 1,
        "name": "Hohensalzburg Fortress",
        "lat": 47.7945,
        "lng": 13.0467,
        "category": "Historic",
        "icon": "building"
    }
]
```

#### CSV Format
```csv
id,name,lat,lng,category,icon
1,Hohensalzburg Fortress,47.7945,13.0467,Historic,building
2,Mirabell Palace,47.8065,13.0424,Historic,building
```

### Supported Categories

The system recognizes the following attraction categories with custom styling:

- **Landmark** (blue) - Major city landmarks
- **Museum** (purple) - Museums and cultural sites  
- **Historic/Historic Site** (dark green) - Historical buildings and sites
- **Memorial** (dark purple) - Monuments and memorials
- **Park** (green) - Parks and natural areas
- **Shopping** (pink) - Shopping districts and markets
- **Religious/Religious Site** (orange) - Churches and religious sites
- **Viewpoint** (cadet blue) - Scenic viewpoints
- **Cafe** (brown) - Cafes and coffee shops
- **Restaurant** (orange) - Dining establishments
- **Attraction** (gray) - General attractions

### Customization

#### Adding New Cities

1. **Create attraction data** in JSON or CSV format
2. **Update default configuration** in the script:
```python
DEFAULT_CONFIG = {
    "city": "Your City, Country",
    "input": "data/your_city_attractions.json",
    "max_attractions": 20,
    "optimization": "simulated_annealing",
    "selected": "1,2,3,4,5",
    "out": "maps/your_city_route.html"
}
```

#### Adding New Optimization Algorithms

1. **Implement algorithm function**:
```python
def solve_tsp_your_algorithm(attractions: List[Dict]) -> List[Dict]:
    # Your optimization logic here
    return optimized_attractions
```

2. **Add to optimization choices**:
```python
parser.add_argument("--optimization", 
    choices=["nearest_neighbor", "simulated_annealing", "your_algorithm"])
```

3. **Update algorithm descriptions**:
```python
algorithm_descriptions = {
    "your_algorithm": "Description of your algorithm"
}
```

#### Custom Styling

Modify the `ICON_STYLE` dictionary to add new categories or change colors:

```python
ICON_STYLE["Your Category"] = {
    "icon": "your-fontawesome-icon",
    "color": "leaflet-color",
    "hex": "#HEXCOLOR"
}
```

## License

This project is open-source and available under the MIT License.



## Copyright
© 2025 – FindMyRoute Development Team: Amna Azeem, Annabelle Kiefer, Demet Akbaba, Most Sanjida Anjum Suchi and Md Jakir Hossain.  
Distributed under the GNU General Public License v3.0.
