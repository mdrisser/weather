#!/usr/bin/python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "ansiwrap==0.8.4",
#     "certifi==2024.7.4",
#     "charset-normalizer==3.3.2",
#     "idna==3.7",
#     "markdown-it-py==3.0.0",
#     "mdurl==0.1.2",
#     "pygments==2.18.0",
#     "requests==2.32.3",
#     "rich==13.7.1",
#     "simple-term-menu==1.6.6",
#     "six==1.17.0",
#     "tabulate==0.9.0",
#     "textwrap3==0.9.2",
#     "urllib3==2.2.2",
# ]
# ///

import json
import logging
import requests
import tomllib

from rich.prompt import Prompt
from rich.prompt import IntPrompt
from simple_term_menu import TerminalMenu


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
location = ""

# These are the styles to be used when building the menus later
menu_highlight = ("fg_black", "bg_yellow", "bold")
menu_cursor = ("fg_yellow", "bold")


def prep_loggers():
    """Prepare loggers """
    logger = logging.getLogger('weather_logger')

    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if DEBUG:
        debug_handler = logging.getLogger('debug_logger')
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        logger.addHandler(debug_handler)

    # Prepare a file logger for warnings and errors
    file_handler = logging.FileHandler(config['log']['file'])
    file_handler.setLevel(logging.WARNING)

    file_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)

    return logger


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


def get_forecast():
    """
    Takes the chosen location, retrieves the items needed for the API call,
    puts them all together then fetches the weather forecast as a JSON file.
    Once the forecast is retrieved, parses the JSON, prepares the output
    and prints it to the screen.
    """
    import rich.box
    from rich import print
    from rich.console import Console
    from rich.table import Table

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
        table = Table(title=f"NOAA Weather Forecast for {locale}", box=rich.box.SIMPLE_HEAD, padding=0)
        table.add_column("Day", justify="right", style="white", no_wrap=True)
        table.add_column("Temp", justify="left", style="bold red", no_wrap=True)
        table.add_column("Wind", justify="left", style="cyan", no_wrap=True)
        table.add_column("Forecast", justify="left", no_wrap=False)
        table.add_column("Chance of Precip.", justify="left", style="bold blue")

        periods = wx_json['properties']['periods']

        # Loop through each day/night in the forecast and add a row to the table for each day/night
        # Had to create a custom function to do this as lambda doesn't like calling functions of objects (e.g. table.add_row())
        list(map(lambda day: addrow(table, day), periods))

        # Print the table out to the screen
        console = Console()
        console.print(table)
        print()


def get_conditions():
    """
    Similar to get_forecast(), excpet the URL is different.

    Takes the chosen location, retrieves the items needed for the API call,
    puts them all together then fetches the weather forecast as a JSON file.
    Once the forecast is retrieved, parses the JSON, prepares the output
    and prints it to the screen.
    """
    import convert.convert as Convert
    import convert.temperature as temp
    import convert.speed as speed
    import utilities.terminal as term

    from rich import print
    from rich.prompt import Prompt
    from tabulate import tabulate

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
    title = f"NOAA Current Weather Conditions\nin {locale}"

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

    # Put it all together so that tabulate() can generate the table
    wx_data = [
        ['Temperature', temperature],
        ['Dewpoint', dewpoint],
        ['Humidity', humidity],
        ['Wind Direction', wind_direction],
        ['Wind Speed', wind_speed],
        ['Wind Gust', gust],
    ]

    print(title)

    # Generate the table and print it to the screen
    print(tabulate(wx_data))
    print()


def wx_type_menu():
    opts = ["Forecast", "Conditions", "Quit"]
    term_menu = TerminalMenu(opts, title="Weather Type", menu_highlight_style=menu_highlight, menu_cursor_style=menu_cursor)
    menu_choice = term_menu.show()
    wx_type = opts[menu_choice]

    if wx_type == "Forecast":
        get_forecast()
    elif wx_type == "Conditions":
        get_conditions()
    else:
        exit()


def main_menu() -> None:
    global location
    opts = ["Bullhead", "Flagstaff", "Havasu", "Kingman", "Kearny", "Payson", "Phoenix", "Prescott", "Quit"]
    term_menu = TerminalMenu(opts, title="Locations", menu_highlight_style=menu_highlight, menu_cursor_style=menu_cursor)
    menu_choice = term_menu.show()
    location = opts[menu_choice]

    if location == "Quit":
        exit()

    wx_type_menu()

if __name__ == "__main__":
    # Prepare the logger
    logger = prep_loggers()
    print()
    main_menu()
