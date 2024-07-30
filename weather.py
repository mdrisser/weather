#!/usr/bin/python3

import argparse
import json
import logging
import requests
import tomllib

from rich.prompt import Prompt
from rich.prompt import IntPrompt


CONFIG_DIR = "/home/mike/.config/weather/"

DEBUG = False
location = ""
wx = 0

# Read the TOML configuration file
with open(f"{CONFIG_DIR}weather.toml", "rb") as f:
    config = tomllib.load(f)
    stations = config['stations']

# Set a couple of variable defaults
default = "N/A"
places = []
noaa_office = ""


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


def get_places():
    """Creates a list of places to be used in the prompt.
    
    Also finds and sets the default station of the prompt.

    Returns:
        list: List of places to be used in the prompt
    """
    global default
    global logger

    places = [s['name'] for s in stations]
    
    d = [s['name'] for s in stations if s['default'] == 'True']
    default = ''.join(d)
    
    if DEBUG:
        logger.info(f"Default station: {default}")
    
    return places


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
        table = Table(title=f"Weather Forecast for {locale}", box=rich.box.SIMPLE_HEAD, padding=0)
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
    #from rich.prompt import Prompt
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
    title = f"Current Weather Conditions\nin {locale}"
    
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


def get_location():
    # Ask the user which station to get the information from
     # Prompt and IntPrompt both handle invalid input for us
    location = Prompt.ask("Get weather for which city?", choices=places, default=default)
    
    return location


def get_type():
    wx = IntPrompt.ask("Get 1) Forecast or 2) Conditions?", choices=["1","2"], default=2)
    
    return wx


if __name__ == "__main__":
    # Prepare the logger
    logger = prep_loggers()
    
    # Get the list of places for choices in the prompt
    places = get_places()
    
    # Build an argument parser using the built-in argparse module
    parser = argparse.ArgumentParser(
        prog="weather.py",
        description="Fetch weather forecast or current conditions for a location."
    )
    
    parser.add_argument(
        "--location",
        "-l",
        help="Location to retrieve weather for",
        choices=places,
        type=str
    )

    parser.add_argument(
        "--type",
        "-t",
        help="Type of weather information, either forecast or current",
        choices=["forecast", "current"],
        type=str
    )
    
    args = parser.parse_args()
    
    if args.location is not None:
        location = args.location
    else:
        location = get_location()
        
    if args.type is not None:
        type = args.type
        
        if type == "forecast":
            wx = 1
        else:
            wx = 2
    else:
        wx = get_type()
    
    # Get the forecast or current conditions as the user chose
    if wx == 1:
        get_forecast()
    elif wx == 2:
        get_conditions()
    else:
        print("There was an error, please try again.")
    
    # A final blank line to keep things neat and clean
    print()
