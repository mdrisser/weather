#!/usr/bin/env python3

import json
import logging
import requests
import tomllib

import convert.convert as Convert
import convert.temperature as temp
import convert.speed as speed
import utilities.terminal as term

from rich import box
from rich import print
from rich.console import Console
from rich.layout import Layout
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from simple_term_menu import TerminalMenu
from tabulate import tabulate


CONFIG_DIR = "/home/mrisser/.config/weather/"
DEBUG = False

# Read the TOML configuration file
with open(f"{CONFIG_DIR}weather.toml", "rb") as f:
    config = tomllib.load(f)
    stations = config['stations']

# Set a couple of variable defaults
default = "N/A"
places = []
noaa_office = ""
#location = ""

# These are the styles to be used when building the menus later
menu_highlight = ("fg_black", "bg_yellow", "bold")
menu_cursor = ("fg_yellow", "bold")

layout = Layout()

"""Prepare loggers """
logger = logging.getLogger(__name__)

# Create a formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if DEBUG:
    debug_handler = logging.getLogger(__name__ + '-debug_logger')
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    logger.addHandler(debug_handler)

# Prepare a file logger for warnings and errors
file_handler = logging.FileHandler(config['log']['file'])
file_handler.setLevel(logging.WARNING)

file_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)


def addrow(tbl,d):
    """Adds a row to the specified table. This function exists because list(map(lambda))
    does not call functions of objects (e.g. table.add_row())

    Args:
        tbl : the table to add the row to
        d (dict): a dictionary of values to be added to the table row
    """
    # Check to see if there is a value for precipitation
    if d['probabilityOfPrecipitation']['value'] is None:
        # If there isn't set precip to 0%
        precip = '0%'
    else:
        # Otherwise, set precip to the value provided in the dictionary
        precip = f"{d['probabilityOfPrecipitation']['value']}%"

    # Finally, add the row to the table that was passed in the function arguments
    tbl.add_row(d['name'], str(d['temperature']) + d['temperatureUnit'], str(d['windSpeed']) + ' ' + d['windDirection'], d['shortForecast'], precip)


def fetch_results(url):
    """Sends a request to the provided URL and returns the result of that request

    Args:
        url (string): the URL to send the request to

    Returns:
        request result: the result of the request
    """

    req_headers = {'user-agent': 'weather.py/mdrisser@gmail.com'}

    try:
        result = requests.get(url, headers=req_headers, timeout=5)
        result.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e}")
        print(f"HTTP Error: {e}")
        exit
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection Error: {e}")
        print(f"Connection Error: {e}")
        exit
    except requests.exceptions.Timeout as e:
        logger.error(f"Request timed out. {e}")
        print(f"Request timed out. {e}")
        exit
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occured: {e}")
        print(f"An error occured: {e}")
        exit

    return result


def get_forecast(location):
    """
    Takes the chosen location, retrieves the items needed for the API call,
    puts them all together then fetches the weather forecast as a JSON file.
    Once the forecast is retrieved, parses the JSON, prepares the output
    and prints it to the screen.
    """

    # Grab the logger we prepared when the script was started
    global logger

    # Loop through the stations...
    for station in stations:
        #...get the information for the selected station
        if station['name'] == location:
            locale = station['locale']
            noaa_office = station['noaa_office']
            noaa_grid_x = station['noaa_grid_x']
            noaa_grid_y = station['noaa_grid_y']

    # Get things ready to fetch the forecast
    logger.info(f"Fetching current conditions for: {locale}")
    wx_url = f"https://api.weather.gov/gridpoints/{noaa_office}/{noaa_grid_x},{noaa_grid_y}/forecast"

    # Add a blank line to make the whole thing look a little cleaner
    print()

    try:
        # Fetch the forecast
        r = fetch_results(wx_url)
        r.raise_for_status()
    except Exception as err:
        # If there was some type of error, shows the user and log it
        logger.error(err)
        print(f"Error: [bold red]{err}[/bold red]")
        exit
    else:
        # Load the JSON data
        wx_json = json.loads(r.text)

        # Create the table to hold the forecast information
        table = Table(title=locale, box=box.SIMPLE_HEAD, padding=0)
        table.add_column("Day", justify="right", style="white", no_wrap=True)
        table.add_column("Temp", justify="left", style="bold red", no_wrap=True)
        table.add_column("Wind", justify="left", style="cyan", no_wrap=True)
        table.add_column("Forecast", justify="left", no_wrap=False)
        table.add_column("Chance of Precip.", justify="left", style="bold blue")

        periods = wx_json['properties']['periods']

        # Loop through each day/night in the forecast and add a row to the table for each day/night
        # Had to create a custom function to do this as lambda doesn't like calling functions of objects (e.g. table.add_row())
        list(map(lambda day: addrow(table, day), periods))

        return table


def get_conditions(location):
    """
    Similar to get_forecast(), except the URL is different.

    Takes the chosen location, retrieves the items needed for the API call,
    puts them all together then fetches the weather forecast as a JSON file.
    Once the forecast is retrieved, parses the JSON, prepares the output
    and prints it to the screen.
    """

    # Grab the logger we prepared when the script was started
    global logger

    # Check our list of stations...
    for station in stations:
        #...once we find it...
        if location == station['name']:
            #...grab the info we need for the API request
            locale = station['locale']
            station_id = station['station_id']

    # Prepare the API request
    wx_url = f"https://api.weather.gov/stations/{station_id}/observations/latest"

    # A blank line to make things look a little cleaner
    print()

    try:
        # Attempt tho fetch the weather conditions
        r = fetch_results(wx_url)
        r.raise_for_status()
    except Exception as err:
        logger.error(err)
        print(f"Error: [bold red]{err}[/bold red]")
        exit
    else:
        wx_json = json.loads(r.text)

    # Start putting together the table to display to the user
    observations = wx_json['properties']
    #title = f"NOAA Current Weather Conditions\nin {locale}"

     # The following statements really should be self-explanitory
    if observations['temperature']['value'] is not None:
        temperature = f"{round(temp.c_to_f(observations['temperature']['value']))}{term.deg_sign} F"
    else:
        temperature = "N/A"

    if observations['dewpoint']['value'] is not None:
        dewpoint = f"{round(temp.c_to_f(observations['dewpoint']['value']))}{term.deg_sign} F"
    else:
        dewpoint = "N/A"

    if observations['relativeHumidity']['value'] is not None:
        humidity = f"{round(observations['relativeHumidity']['value'])}%"
    else:
        humidity = "N/A"

    wind_dir = observations['windDirection']['value']

    if wind_dir is None:
        wind_dir = 0

    # Converts the direction in degrees to a cardinal value (i.e. N or NE)
    cardinal = Convert.angle_to_card(wind_dir)
    wind_direction = f"{cardinal} ({wind_dir}{term.deg_sign})"

    wind_speed = observations['windSpeed']['value']

    if wind_speed is None:
        wind_speed = "0 mph"
    else:
        wind_speed = f"{round(speed.kph_to_mph(wind_speed))} mph"

    gust = observations['windGust']['value']
    if gust:
        gust = f"{round(speed.kph_to_mph(gust))}"
    else:
        gust = "None"

    table = Table(title=locale, box=box.SIMPLE_HEAD, padding=0)
    table.add_row('Temperature', temperature)
    table.add_row('Dewpoint', dewpoint)
    table.add_row('Humidity', humidity)
    table.add_row('Wind Direction', wind_direction)
    table.add_row('Wind Speed', wind_speed)
    table.add_row('Wind Gust', gust)

    return table


def draw_layout():
    global layout

    TITLE = """
    # LOCAL WEATHER
    """
    title = Markdown(TITLE)

    layout.split_column(
        Layout(name="upper"),
        Layout(name="lower")
    )

    layout['upper'].size = None
    layout['upper'].ratio = 1
    layout['upper'].update(title)
    
    layout['lower'].size = None
    layout['lower'].ratio = 5
    layout['lower'].split_row(
        Layout(name="lower_left"),
        Layout(name="lower_right")
    )


def update_layout(wx_condx, wx_forcst, location):
    global layout

    layout['lower_left'].update(
        Panel(wx_condx, title="[bold yellow]NOAA CURRENT CONDITIONS[/bold yellow]")
    )

    layout['lower_right'].update(
        Panel(wx_forcst, title="[bold green]NOAA FORECAST[/bold green]")
    )


def main_menu() -> None:
    global location
    opts = ["Bullhead", "Flagstaff", "Havasu", "Kingman", "Kearny", "Payson", "Phoenix", "Prescott", "Quit"]
    term_menu = TerminalMenu(opts, title="Locations", menu_highlight_style=menu_highlight, menu_cursor_style=menu_cursor)
    menu_choice = term_menu.show()
    location = opts[menu_choice]

    if location == "Quit":
        exit()

    #wx_type_menu()
    return location


if __name__ == "__main__":
    loc = main_menu()
    condx = get_conditions(loc)
    frcst = get_forecast(loc)

    draw_layout()
    update_layout(condx, frcst, loc)
    print(layout)
