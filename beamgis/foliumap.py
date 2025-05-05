"""This module provides a custom Map class that extends folium.Map"""

import folium
import folium.plugins
from localtileserver import get_folium_tile_layer, TileClient
from typing import Optional, List, Union
import folium.plugins as plugins
import pandas as pd


class Map(folium.Map):
    """A custom Map class that extends folium.Map."""

    def __init__(self, center=(0, 0), zoom=2, **kwargs):
        """Initializes the Map object.

        Args:
            center (tuple, optional): The initial center of the map as (latitude, longitude). Defaults to (0, 0).
            zoom (int, optional): The initial zoom level of the map. Defaults to 2.
            **kwargs: Additional keyword arguments for the folium.Map class.
        """
        super().__init__(location=center, zoom_start=zoom, **kwargs)

    def add_geojson(
        self,
        data,
        zoom_to_layer=True,
        hover_style=None,
        **kwargs,
    ):
        """Adds a GeoJSON layer to the map.

        Args:
            data (str or dict): The GeoJSON data. Can be a file path (str) or a dictionary.
            zoom_to_layer (bool, optional): Whether to zoom to the layer's bounds. Defaults to True.
            hover_style (dict, optional): Style to apply when hovering over features. Defaults to {"color": "yellow", "fillOpacity": 0.2}.
            **kwargs: Additional keyword arguments for the folium.GeoJson layer.

        Raises:
            ValueError: If the data type is invalid.
        """
        import geopandas as gpd

        if hover_style is None:
            hover_style = {"color": "yellow", "fillOpacity": 0.2}

        if isinstance(data, str):
            gdf = gpd.read_file(data)
            geojson = gdf.__geo_interface__
        elif isinstance(data, dict):
            geojson = data

        geojson = folium.GeoJson(data=geojson, **kwargs)
        geojson.add_to(self)

        if zoom_to_layer and gdf is not None:
            bounds = gdf.total_bounds
            self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    def add_basemap(self, basemap="OpenStreetMap"):
        """Add basemap to the map using Folium's built-in tiles or a custom TileLayer.

        Args:
            basemap (str or dict, optional): Basemap name (dotted format) or a custom basemap dict.
                Examples:
                    "CartoDB.DarkMatter"
                    {
                        "tiles": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
                        "name": "OpenTopoMap",
                        "attr": "© OpenTopoMap contributors"
                    }
        """
        # Built-in basemap mapping
        basemap_mapping = {
            "OpenStreetMap": "OpenStreetMap",
            "CartoDB.Positron": "CartoDB positron",
            "CartoDB.DarkMatter": "CartoDB dark_matter",
        }

        if isinstance(basemap, str):
            if basemap not in basemap_mapping:
                raise ValueError(
                    f"Basemap '{basemap}' not supported. Available options: {list(basemap_mapping.keys())}"
                )
            tile_name = basemap_mapping[basemap]
            tile_layer = folium.TileLayer(tiles=tile_name, name=basemap, control=True)
        elif isinstance(basemap, dict):
            required_keys = {"tiles", "name", "attr"}
            if not required_keys.issubset(basemap):
                raise ValueError(
                    "Custom basemap dict must include 'tiles', 'name', and 'attr'"
                )
            tile_layer = folium.TileLayer(
                tiles=basemap["tiles"],
                name=basemap["name"],
                attr=basemap["attr"],
                control=True,
            )
        else:
            raise TypeError(
                "Basemap must be a string or a dictionary with 'tiles', 'name', and 'attr'."
            )

        tile_layer.add_to(self)

    def add_shp(self, data, **kwargs):
        """Adds a shapefile to the map.

        Args:
            data (str): The file path to the shapefile.
            **kwargs: Additional keyword arguments for the GeoJSON layer.
        """
        import geopandas as gpd

        gdf = gpd.read_file(data)
        gdf = gdf.to_crs(epsg=4326)
        geojson = gdf.__geo_interface__
        self.add_geojson(geojson, **kwargs)

    def add_gdf(self, gdf, **kwargs):
        """Adds a GeoDataFrame to the map.

        Args:
            gdf (geopandas.GeoDataFrame): The GeoDataFrame to add.
            **kwargs: Additional keyword arguments for the GeoJSON layer.
        """
        gdf = gdf.to_crs(epsg=4326)
        geojson = gdf.__geo_interface__
        self.add_geojson(geojson, **kwargs)

    def add_vector(self, data, **kwargs):
        """Adds vector data to the map.

        Args:
            data (str, geopandas.GeoDataFrame, or dict): The vector data. Can be a file path, GeoDataFrame, or GeoJSON dictionary.
            **kwargs: Additional keyword arguments for the GeoJSON layer.

        Raises:
            ValueError: If the data type is invalid.
        """
        import geopandas as gpd

        if isinstance(data, str):
            gdf = gpd.read_file(data)
            self.add_gdf(gdf, **kwargs)
        elif isinstance(data, gpd.GeoDataFrame):
            self.add_gdf(data, **kwargs)
        elif isinstance(data, dict):
            self.add_geojson(data, **kwargs)
        else:
            raise ValueError("Invalid data type")

    def add_layer_control(self):
        """Adds a layer control widget to the map."""
        folium.LayerControl().add_to(self)

    def add_split_map(
        self,
        left="openstreetmap",
        right="cartodbpositron",
        colormap_left=None,
        colormap_right=None,
        opacity_left=1.0,
        opacity_right=1.0,
        **kwargs,
    ):
        """
        Adds a split map view to the current map, allowing users to compare two different map layers side by side.

        Parameters:
            left (str): The tile layer or path to a raster file for the left side of the map.
            right (str): The tile layer or path to a raster file for the right side of the map.
            colormap_left (callable): Colormap function for the left raster layer (if applicable).
            colormap_right (callable): Colormap function for the right raster layer (if applicable).
            opacity_left (float): Opacity for the left layer.
            opacity_right (float): Opacity for the right layer.
            **kwargs: Additional keyword arguments to customize the tile layers.

        Returns:
            None
        """

        # Handle left layer
        if isinstance(left, str) and left.lower().endswith((".tif", ".tiff")):
            client_left = TileClient(left)
            layer_left = get_folium_tile_layer(
                client_left,
                name="Left Layer",
                colormap=colormap_left,
                opacity=opacity_left,
                **kwargs,
            )
        else:
            layer_left = folium.TileLayer(
                left, name="Left Layer", opacity=opacity_left, **kwargs
            )

        # Handle right layer
        if isinstance(right, str) and right.lower().endswith((".tif", ".tiff")):
            client_right = TileClient(right)
            layer_right = get_folium_tile_layer(
                client_right,
                name="Right Layer",
                colormap=colormap_right,
                opacity=opacity_right,
                **kwargs,
            )
        else:
            layer_right = folium.TileLayer(
                right, name="Right Layer", opacity=opacity_right, **kwargs
            )

        # Add layers to map
        layer_left.add_to(self)
        layer_right.add_to(self)

        # Add split map control
        sbs = folium.plugins.SideBySideLayers(
            layer_left=layer_left, layer_right=layer_right
        )
        sbs.add_to(self)

    def add_heatmap(
        self,
        data: Union[str, List[List[float]], pd.DataFrame],
        latitude: Optional[str] = "latitude",
        longitude: Optional[str] = "longitude",
        value: Optional[str] = "value",
        name: Optional[str] = "Heat map",
        radius: Optional[int] = 25,
        **kwargs,
    ):
        """Adds a heat map to the map. Reference: https://stackoverflow.com/a/54756617

        Args:
            data (str | list | pd.DataFrame): File path or HTTP URL to the input file or a list of data points in the format of [[x1, y1, z1], [x2, y2, z2]]. For example, https://raw.githubusercontent.com/opengeos/leafmap/master/examples/data/world_cities.csv
            latitude (str, optional): The column name of latitude. Defaults to "latitude".
            longitude (str, optional): The column name of longitude. Defaults to "longitude".
            value (str, optional): The column name of values. Defaults to "value".
            name (str, optional): Layer name to use. Defaults to "Heat map".
            radius (int, optional): Radius of each “point” of the heatmap. Defaults to 25.

        Raises:
            ValueError: If data is not a list.
        """
        import pandas as pd

        try:
            if isinstance(data, str):
                df = pd.read_csv(data)
                data = df[[latitude, longitude, value]].values.tolist()
            elif isinstance(data, pd.DataFrame):
                data = data[[latitude, longitude, value]].values.tolist()
            elif isinstance(data, list):
                pass
            else:
                raise ValueError("data must be a list, a DataFrame, or a file path.")

            plugins.HeatMap(data, name=name, radius=radius, **kwargs).add_to(
                folium.FeatureGroup(name=name).add_to(self)
            )
        except Exception as e:
            raise Exception(e)
