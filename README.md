# FindMyRoute: A City Path Optimizer

## Project Overview

FindMyRoute is an interactive web application designed to help users discover and optimize travel paths through a city. The current implementation focuses on the city of Salzburg, Austria, but it is built to be extensible to any city by simply uploading a CSV file of attractions.

The application allows users to:

* Visualize key attractions on an interactive map using Leaflet.js.

* Upload a custom CSV file to load attractions for any city.

* Select a set of attractions and find the most efficient route connecting them.

* See key route metrics like total distance and estimated time.

* Animate the calculated route on the map to visualize the journey.


  <img width="1360" height="654" alt="image" src="https://github.com/user-attachments/assets/c0ca9454-c952-4f66-8999-e4fe7c625225" />


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

* `index.html`: The main web page for the application.

* `findmyroute.py`: A Python script for extracting and saving tourist attraction data from OpenStreetMap.

* `run_route.py`: A simple script to demonstrate how to run `findmyroute.py`.

### Running the Application

1. **Clone the Repository:**

   ```
   git clone [https://github.com/your-username/FindMyRoute.git](https://github.com/your-username/FindMyRoute.git)
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

* `showOptimizedRoute()`: Uses the Leaflet Routing Machine to calculate and display the route.

* `animateRoute()`: Animates a marker along the route's path.

### `findmyroute.py`

This script is responsible for the data collection and processing.

* It uses the `osmnx` library to query OpenStreetMap for tourism and amenity data for a specified city.

* It filters the results to ensure valid data and a consistent number of attractions (defaulting to 20).

* It categorizes attractions based on their tags and assigns a corresponding icon.

* Finally, it saves the processed data into both JSON and CSV formats.

### `run_route.py`

A simple wrapper script to make the `findmyroute.py` script easy to use. It imports the main function and calls it with a specified city name.

## License

This project is open-source and available under the MIT License.
