import ipywidgets as widgets
import pandas as pd
from ipyleaflet import Map, Heatmap


class HeatmapWidget(widgets.VBox):
    def __init__(self, map_obj):
        super().__init__()
        self.map_obj = map_obj
        self.df = None

        # Widgets
        self.csv_url = widgets.Text(
            value="https://raw.githubusercontent.com/opengeos/leafmap/master/examples/data/world_cities.csv",
            placeholder="Enter CSV URL",
            description="CSV URL:",
            layout=widgets.Layout(width="100%"),
        )

        self.load_button = widgets.Button(description="Load CSV", button_style="info")
        self.lat_dropdown = widgets.Dropdown(description="Latitude:")
        self.lon_dropdown = widgets.Dropdown(description="Longitude:")
        self.val_dropdown = widgets.Dropdown(description="Value:")
        self.radius_slider = widgets.IntSlider(
            value=25, min=1, max=50, step=1, description="Radius:"
        )
        self.name_text = widgets.Text(value="Heat map", description="Layer Name:")
        self.add_button = widgets.Button(
            description="Add Heatmap", button_style="success"
        )

        self.load_button.on_click(self._load_csv)
        self.add_button.on_click(self._add_heatmap)

        self.children = [
            self.csv_url,
            self.load_button,
            self.lat_dropdown,
            self.lon_dropdown,
            self.val_dropdown,
            self.radius_slider,
            self.name_text,
            self.add_button,
        ]

    def _load_csv(self, b):
        try:
            self.df = pd.read_csv(self.csv_url.value)
            cols = self.df.columns.tolist()
            self.lat_dropdown.options = cols
            self.lon_dropdown.options = cols
            self.val_dropdown.options = cols
        except Exception as e:
            print(f"Error loading CSV: {e}")

    def _add_heatmap(self, b):
        try:
            lat = self.lat_dropdown.value
            lon = self.lon_dropdown.value
            val = self.val_dropdown.value
            radius = self.radius_slider.value
            name = self.name_text.value

            data = self.df[[lat, lon, val]].values.tolist()
            heatmap = Heatmap(locations=data, radius=radius, name=name)
            self.map_obj.add(heatmap)
        except Exception as e:
            print(f"Error adding heatmap: {e}")
