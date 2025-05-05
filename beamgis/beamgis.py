"""Main module."""

import os
from typing import Any, Dict, List, Optional, Tuple, Type, Union, Callable, Sequence

import ipyleaflet
import ipywidgets as widgets
import pandas as pd
from IPython.display import display
from .common import *


class Map(ipyleaflet.Map):
    def __init__(self, center=[20, 0], zoom=2, height="600px", **kwargs):

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

    def add_heatmap_gui(
        self, position="topright", latitude=None, longitude=None, value=None, radius=25
    ):
        """
        Adds an inline GUI to the map for generating a heatmap from a CSV URL.

        Args:
            position (str): Position of the widget on the map. Defaults to "topright".
            latitude (str, optional): The default latitude column name.
            longitude (str, optional): The default longitude column name.
            value (str, optional): The default value (intensity) column name.
            radius (int, optional): Default radius of each point on the heatmap. Defaults to 25.
        """
        import pandas as pd
        from ipyleaflet import Heatmap

        # --- Core UI Components ---
        toggle = widgets.ToggleButton(
            value=True,
            tooltip="Show/hide heatmap panel",
            icon="fire",
            layout=widgets.Layout(width="45px", height="45px"),
        )

        url_text = widgets.Text(
            placeholder="Paste CSV URL",
            description="CSV URL:",
            layout=widgets.Layout(width="350px"),
            style={"description_width": "initial"},
        )

        lat_dd = widgets.Dropdown(
            description="Lat", layout=widgets.Layout(width="150px")
        )
        lon_dd = widgets.Dropdown(
            description="Lon", layout=widgets.Layout(width="150px")
        )
        val_dd = widgets.Dropdown(
            description="Value", layout=widgets.Layout(width="150px")
        )

        radius_slider = widgets.IntSlider(
            value=radius,
            min=1,
            max=50,
            step=1,
            description="Radius:",
            continuous_update=False,
            layout=widgets.Layout(width="250px"),
        )

        load_button = widgets.Button(
            description="Load CSV", icon="download", button_style="info"
        )
        heatmap_button = widgets.Button(
            description="Add Heatmap", icon="plus", button_style="success"
        )
        close_button = widgets.Button(icon="times", layout=widgets.Layout(width="40px"))

        # --- Layout Containers ---
        controls_box = widgets.VBox(
            [
                url_text,
                load_button,
                widgets.HBox([lat_dd, lon_dd, val_dd]),
                radius_slider,
                heatmap_button,
            ]
        )

        hbox = widgets.VBox([toggle, controls_box, close_button])

        # --- Behavior Handlers ---
        def on_toggle_change(change):
            hbox.children = (
                [toggle, controls_box, close_button] if change["new"] else [toggle]
            )

        toggle.observe(on_toggle_change, names="value")

        def on_close_click(b):
            hbox.close()

        close_button.on_click(on_close_click)

        def on_load_click(b):
            try:
                df = pd.read_csv(url_text.value)
                options = df.columns.tolist()
                lat_dd.options = options
                lon_dd.options = options
                val_dd.options = options

                # Preselect columns if provided
                if latitude in options:
                    lat_dd.value = latitude
                if longitude in options:
                    lon_dd.value = longitude
                if value in options:
                    val_dd.value = value

                hbox.df = df  # attach df to widget
            except Exception as e:
                print(f"Error loading CSV: {e}")

        load_button.on_click(on_load_click)

        def on_add_click(b):
            try:
                df = hbox.df
                lat, lon, val = lat_dd.value, lon_dd.value, val_dd.value
                data = df[[lat, lon, val]].values.tolist()
                heatmap = Heatmap(
                    locations=data, radius=radius_slider.value, name="Heat map"
                )
                self.add(heatmap)
            except Exception as e:
                print(f"Error adding heatmap: {e}")

        heatmap_button.on_click(on_add_click)

        control = ipyleaflet.WidgetControl(widget=hbox, position=position)
        self.add(control)

    def add_google_map(self, map_type="ROADMAP"):
        """Add Google Map to the map.

        Args:
            map_type (str, optional): Map type. Defaults to "ROADMAP".
        """
        map_types = {
            "ROADMAP": "m",
            "SATELLITE": "s",
            "HYBRID": "y",
            "TERRAIN": "p",
        }
        map_type = map_types[map_type.upper()]

        url = (
            f"https://mt1.google.com/vt/lyrs={map_type.lower()}&x={{x}}&y={{y}}&z={{z}}"
        )
        layer = ipyleaflet.TileLayer(url=url, name="Google Map")
        self.add(layer)

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
            hover_style (dict, optional): Style to apply when hovering over features.
            Defaults to {"color": "yellow", "fillOpacity": 0.2}.
            **kwargs: Additional keyword arguments for the ipyleaflet.GeoJSON layer.

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
        layer = ipyleaflet.GeoJSON(data=geojson, hover_style=hover_style, **kwargs)
        self.add_layer(layer)

        if zoom_to_layer:
            bounds = gdf.total_bounds
            self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

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
        control = ipyleaflet.LayersControl(position="topright")
        self.add_control(control)

    def add_raster(self, url, name="Raster", colormap=None, opacity=None, **kwargs):
        """Adds a raster layer to the map.

        Args:
            url (str): The file path or URL to the raster data.
            name (str, optional): The name of the layer. Defaults to "Raster".
            colormap (str, optional): The colormap to apply. Defaults to None.
            opacity (float, optional): The opacity of the layer. Defaults to None.
            **kwargs: Additional keyword arguments for the tile layer.
        """
        from localtileserver import TileClient, get_leaflet_tile_layer

        client = TileClient(url)
        tile_layer = get_leaflet_tile_layer(
            client, name=name, colormap=colormap, opacity=opacity, **kwargs
        )

        self.add(tile_layer)
        self.center = client.center()
        self.zoom = client.default_zoom

    def add_image(self, image, bounds=None, **kwargs):
        """Adds an image to the map.

        Args:
            image (str): The file path to the image.
            bounds (list, optional): The bounds for the image. Defaults to None.
            **kwargs: Additional keyword arguments for the ipyleaflet.ImageOverlay layer.
        """

        if bounds is None:
            bounds = [[-90, -180], [90, 180]]
        overlay = ipyleaflet.ImageOverlay(url=image, bounds=bounds, **kwargs)
        self.add(overlay)

    def add_video(self, video, bounds=None, opacity=1.0, **kwargs):
        """Adds a video to the map.

        Args:
            video (str): The file path to the video.
            bounds (list, optional): The bounds for the video. Defaults to None.
            **kwargs: Additional keyword arguments for the ipyleaflet.VideoOverlay layer.
        """

        if bounds is None or not bounds:
            raise ValueError("Bounds must be specified for the video overlay.")
        overlay = ipyleaflet.VideoOverlay(
            url=video, bounds=bounds, opacity=opacity, **kwargs
        )
        self.add(overlay)

    def add_wms_layer(
        self, url, layers, name, format="image/png", transparent=True, **kwargs
    ):
        """Adds a WMS layer to the map.

        Args:
            url (str): The WMS service URL.
            layers (str): The layers to display.
            **kwargs: Additional keyword arguments for the ipyleaflet.WMSLayer layer.
        """
        layer = ipyleaflet.WMSLayer(
            url=url,
            layers=layers,
            name=name,
            format=format,
            transparent=transparent,
            **kwargs,
        )
        self.add(layer)

    def add_search_control(
        self,
        url: str,
        marker: Optional[ipyleaflet.Marker] = None,
        zoom: Optional[int] = None,
        position: Optional[str] = "topleft",
        **kwargs,
    ) -> None:
        """Adds a search control to the map.

        Args:
            url (str): The url to the search API. For example, "https://nominatim.openstreetmap.org/search?format=json&q={s}".
            marker (ipyleaflet.Marker, optional): The marker to be used for the search result. Defaults to None.
            zoom (int, optional): The zoom level to be used for the search result. Defaults to None.
            position (str, optional): The position of the search control. Defaults to "topleft".
            kwargs (dict, optional): Additional keyword arguments to be passed to the search control. See https://ipyleaflet.readthedocs.io/en/latest/api_reference/search_control.html
        """
        if marker is None:
            marker = ipyleaflet.Marker(
                icon=ipyleaflet.AwesomeIcon(
                    name="check", marker_color="green", icon_color="darkred"
                )
            )
        search_control = ipyleaflet.SearchControl(
            position=position,
            url=url,
            zoom=zoom,
            marker=marker,
            **kwargs,
        )
        self.add(search_control)
        self.search_control = search_control

    def add_time_slider(
        self,
        layers: dict = {},
        labels: list = None,
        time_interval: int = 1,
        position: str = "bottomright",
        slider_length: str = "150px",
        zoom_to_layer: Optional[bool] = False,
        **kwargs,
    ) -> None:
        """Adds a time slider to the map.

        Args:
            layers (dict, optional): The dictionary containing a set of XYZ tile layers.
            labels (list, optional): The list of labels to be used for the time series. Defaults to None.
            time_interval (int, optional): Time interval in seconds. Defaults to 1.
            position (str, optional): Position to place the time slider, can be any of ['topleft', 'topright', 'bottomleft', 'bottomright']. Defaults to "bottomright".
            slider_length (str, optional): Length of the time slider. Defaults to "150px".
            zoom_to_layer (bool, optional): Whether to zoom to the extent of the selected layer. Defaults to False.

        """
        from .toolbar import time_slider

        time_slider(
            self,
            layers,
            labels,
            time_interval,
            position,
            slider_length,
            zoom_to_layer,
            **kwargs,
        )

    def add_heatmap(
        self,
        data: Union[str, list, pd.DataFrame],
        latitude: Optional[str] = "latitude",
        longitude: Optional[str] = "longitude",
        value: Optional[str] = "value",
        name: Optional[str] = "Heat map",
        radius: Optional[int] = 25,
        **kwargs,
    ) -> None:
        """Adds a heat map to the map. Reference: https://ipyleaflet.readthedocs.io/en/latest/api_reference/heatmap.html

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
        from ipyleaflet import Heatmap

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

            heatmap = Heatmap(locations=data, radius=radius, name=name, **kwargs)
            self.add(heatmap)

        except Exception as e:
            raise Exception(e)


def basemap_xyz_tiles():
    """Returns a dictionary containing a set of basemaps that are XYZ tile layers.

    Returns:
        dict: A dictionary of XYZ tile layers.
    """
    from leafmap import basemaps

    layers_dict = {}
    keys = dict(basemaps).keys()
    for key in keys:
        if isinstance(basemaps[key], ipyleaflet.WMSLayer):
            pass
        else:
            layers_dict[key] = basemaps[key]
    return layers_dict


def csv_to_df(in_csv, **kwargs):
    """Converts a CSV file to pandas dataframe.

    Args:
        in_csv (str): File path to the input CSV.

    Returns:
        pd.DataFrame: pandas DataFrame
    """
    import pandas as pd

    try:
        return pd.read_csv(in_csv, **kwargs)
    except Exception as e:
        raise Exception(e)


def stac_assets(
    url: str = None,
    collection: str = None,
    item: str = None,
    titiler_endpoint: Optional[str] = None,
    **kwargs,
) -> List:
    """Get all assets of a STAC item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        list: A list of assets.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if isinstance(url, pystac.Item):
        try:
            url = url.self_href
        except Exception as e:
            print(e)

    if url is not None:
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if item is not None:
        kwargs["item"] = item

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(f"{titiler_endpoint}/stac/assets", params=kwargs).json()
    else:
        r = requests.get(titiler_endpoint.url_for_stac_assets(), params=kwargs).json()

    return r


def planet_quarterly(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet quarterly imagery URLs based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: If the API key could not be found.

    Returns:
        list: A list of tile URLs.
    """
    from datetime import date

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    today = date.today()
    year_now = int(today.strftime("%Y"))
    month_now = int(today.strftime("%m"))
    quarter_now = (month_now - 1) // 3 + 1

    link = []
    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/global_quarterly_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    for year in range(2016, year_now + 1):
        for quarter in range(1, 5):
            m_str = str(year) + "q" + str(quarter)

            if year == year_now and quarter >= quarter_now:
                break

            url = f"{prefix}{m_str}{subfix}{api_key}"
            link.append(url)

    return link


def planet_quarterly_tiles(
    api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"
):
    """Generates Planet  quarterly imagery TileLayer based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    tiles = {}
    links = planet_quarterly(api_key, token_name)

    for url in links:
        index = url.find("20")
        name = "Planet_" + url[index : index + 6]

        if tile_format == "ipyleaflet":
            tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
        else:
            tile = folium.TileLayer(
                tiles=url,
                attr="Planet",
                name=name,
                overlay=True,
                control=True,
            )

        tiles[name] = tile

    return tiles


def planet_monthly(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet monthly imagery URLs based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: If the API key could not be found.

    Returns:
        list: A list of tile URLs.
    """
    from datetime import date

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    today = date.today()
    year_now = int(today.strftime("%Y"))
    month_now = int(today.strftime("%m"))

    link = []
    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/global_monthly_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    for year in range(2016, year_now + 1):
        for month in range(1, 13):
            m_str = str(year) + "_" + str(month).zfill(2)

            if year == year_now and month >= month_now:
                break

            url = f"{prefix}{m_str}{subfix}{api_key}"
            link.append(url)

    return link


def planet_monthly_tiles(
    api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"
):
    """Generates Planet monthly imagery TileLayer based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    tiles = {}
    link = planet_monthly(api_key, token_name)

    for url in link:
        index = url.find("20")
        name = "Planet_" + url[index : index + 7]

        if tile_format == "ipyleaflet":
            tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
        else:
            tile = folium.TileLayer(
                tiles=url,
                attr="Planet",
                name=name,
                overlay=True,
                control=True,
            )

        tiles[name] = tile

    return tiles
