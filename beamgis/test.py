"""This module is for testing new features and functions."""

import os
import csv
import ipyleaflet
import ipywidgets as widgets
import pandas as pd
import whitebox


class BeamMap(ipyleaflet.Map):
    def __init__(self, center=(20, 0), zoom=2, height="600px", **kwargs):

        super().__init__(center=center, zoom=zoom, **kwargs)
        self.layout.height = height
        self.scroll_wheel_zoom = True

    def add_basemap(self, basemap="OpenTopoMap"):
        """Add basemap to the map.

        Args:
            basemap (str, optional): Basemap name. Defaults to "OpenTopoMap".
        """

        url = eval(f"ipyleaflet.basemaps.{basemap}").build_url()
        layer = ipyleaflet.TileLayer(url=url, name=basemap)
        self.add(layer)

    def add_basemap_gui(self, options=None, position="topright"):
        """
        Adds a graphical user interface (GUI) for selecting basemaps.

        Args:
            options (list, optional): A list of basemap options to display in the dropdown.
                Defaults to ["OpenStreetMap.Mapnik", "OpenTopoMap", "Esri.WorldImagery", "CartoDB.DarkMatter"].
            position (str, optional): The position of the widget on the map. Defaults to "topright".

        Behavior:
            - A toggle button is used to show or hide the dropdown and close button.
            - The dropdown allows users to select a basemap from the provided options.
            - The close button removes the widget from the map.

        Event Handlers:
            - `on_toggle_change`: Toggles the visibility of the dropdown and close button.
            - `on_button_click`: Closes and removes the widget from the map.
            - `on_dropdown_change`: Updates the map's basemap when a new option is selected.

        Example:
            >>> m = BeamMap(center=[20, 0], zoom=2)
            >>> m.add_basemap_gui()
            >>> m
        """
        if options is None:
            options = [
                "OpenStreetMap.Mapnik",
                "OpenTopoMap",
                "Esri.WorldImagery",
                "CartoDB.DarkMatter",
            ]

        toggle = widgets.ToggleButton(
            value=True,
            button_style="",
            tooltip="Click me",
            icon="map",
        )
        toggle.layout = widgets.Layout(width="45px", height="45px")

        dropdown = widgets.Dropdown(
            options=options,
            value=options[0],
            description="Basemap:",
            style={"description_width": "initial"},
        )
        dropdown.layout = widgets.Layout(width="250px", height="40px")

        button = widgets.Button(
            icon="times",
        )
        button.layout = widgets.Layout(width="40px", height="40px")

        hbox = widgets.HBox([toggle, dropdown, button])

        def on_toggle_change(change):
            """
            Toggles the visibility of the dropdown and close button.

            Args:
                change (dict): The change event containing the new value of the toggle button.
            """
            if change["new"]:
                hbox.children = [toggle, dropdown, button]
            else:
                hbox.children = [toggle]

        toggle.observe(on_toggle_change, names="value")

        def on_button_click(b):
            """
            Closes and removes the widget from the map.

            Args:
                b (ipywidgets.Button): The button click event.
            """
            hbox.close()
            toggle.close()
            dropdown.close()
            button.close()

        button.on_click(on_button_click)

        def on_dropdown_change(change):
            """
            Updates the map's basemap when a new option is selected.

            Args:
                change (dict): The change event containing the new value of the dropdown.
            """
            if change["new"]:
                self.layers = self.layers[:-2]
                self.add_basemap(change["new"])

        dropdown.observe(on_dropdown_change, names="value")

        control = ipyleaflet.WidgetControl(widget=hbox, position=position)
        self.add(control)

    def csv_points_to_shp(
        self, csv_path, out_shp, latitude="latitude", longitude="longitude"
    ):
        """
        Converts a CSV file with latitude/longitude points to a shapefile and adds it to the map.

        Args:
            csv_path (str): File path or URL to the input CSV file.
            out_shp (str): Path for the output shapefile.
            latitude (str): Name of the latitude column.
            longitude (str): Name of the longitude column.
        """
        import geopandas as gpd
        from ipyleaflet import GeoJSON
        from urllib.request import urlretrieve

        # Download if it's a URL
        if csv_path.startswith("http") and csv_path.endswith(".csv"):
            out_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(out_dir, exist_ok=True)
            local_csv = os.path.join(out_dir, os.path.basename(csv_path))
            urlretrieve(csv_path, local_csv)
            csv_path = local_csv

        # Ensure absolute paths
        csv_path = os.path.abspath(csv_path)
        out_shp = os.path.abspath(out_shp)

        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"The file {csv_path} does not exist.")

        # Read CSV header to get field indexes
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fields = reader.fieldnames
            xfield = fields.index(longitude)
            yfield = fields.index(latitude)

        # Convert to shapefile using WhiteboxTools
        wbt = whitebox.WhiteboxTools()
        wbt.csv_points_to_vector(
            csv_path, out_shp, xfield=xfield, yfield=yfield, epsg=4326
        )

        # Read shapefile into GeoPandas
        gdf = gpd.read_file(out_shp)

        # Add to map as GeoJSON
        geojson_data = gdf.__geo_interface__
        layer = GeoJSON(data=geojson_data, name="CSV Points")
        self.add_layer(layer)

    def add_csv_to_shp(self, csv_file, lat_col, lon_col, **kwargs):
        """Adds a CSV file to the map as a GeoJSON layer.

        Args:
            csv_file (str): The path to the CSV file.
            lat_col (str): The name of the latitude column in the CSV file.
            lon_col (str): The name of the longitude column in the CSV file.
            **kwargs: Additional keyword arguments for the GeoJSON layer.
        """
        import geopandas as gpd
        from shapely.geometry import Point

        df = pd.read_csv(csv_file)
        df["geometry"] = [Point(xy) for xy in zip(df[lon_col], df[lat_col])]
        gdf = gpd.GeoDataFrame(df, geometry="geometry")
        geojson = gdf.__geo_interface__
        geojson_layer = ipyleaflet.GeoJSON(data=geojson, **kwargs)
        self.add_layer(geojson_layer)

    def add_csv_to_df(self, csv_path):
        """
        Loads a CSV file into a pandas DataFrame.

        Args:
            csv_path (str): Path to the CSV file.

        Returns:
            pd.DataFrame: The loaded DataFrame.
        """

        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"{csv_path} not found.")
        return pd.read_csv(csv_path)
