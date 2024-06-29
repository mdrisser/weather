#!/usr/bin/python3

import requests
import json
import rich.box
import tomllib
import logging

from rich import print
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

# Read the TOML configuration file
with open("weather.toml", "rb") as f:
    config = tomllib.load(f)
    stations = config['stations']

# Set a couple of variable defaults
default = "N/A"
places = []
noaa_office = ""

def prep_logger():
    # Prepare the logger
    logger = logging.getLogger(__name__)

    logging.basicConfig(
        filename=config['log']['file'],
        level=logging.INFO,
        format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
    )

    return logger


def get_places():
    global default
    global logger

    places = []
    
    # Loop through all of the stations and get the names to use in our prompt
    for station in stations:
        places.append(station['name'])
        
        # Determine which station should be our default
        if station['default'] == "True":
            default = station['name']
            logger.info(f"Default station: {default}")
    
    return places


def get_weather():
    global logger

    logger.info("Started weather.py")

    places = get_places()

    # Ask the user which station to get the information from
    location = Prompt.ask("Get weather for which city?", choices=places, default=default)

    # Loop through the stations...
    for station in stations:
        #...get the information for the selected station
        if station['name'] == location:
            locale = station['locale']
            noaa_office = station['noaa_office']
            noaa_grid_x = station['noaa_grid_x']
            noaa_grid_y = station['noaa_grid_y']

    # Fetch the weather forecast
    logger.info(f"Fetching weather for: {locale}")
    wx_url = f"https://api.weather.gov/gridpoints/{noaa_office}/{noaa_grid_x},{noaa_grid_y}/forecast"
    req_headers = {'user-agent': 'weather.py/mdrisser@gmail.com'}

    print()

    try:
        r = requests.get(wx_url, headers=req_headers)
        r.raise_for_status()
    except Exception as err:
        logger.error(err)
        print(f"Error: [bold red]{err}[/bold red]")
    else:
        # Load the JSON data
        wx_json = json.loads(r.text)

        # Create the table to hold the forecast information
        table = Table(title=f"Weather Forecast for {locale}", box=rich.box.SIMPLE_HEAD, padding=0)
        table.add_column("Day", justify="right", style="white", no_wrap=True)
        table.add_column("Temp", justify="left", style="bold red", no_wrap=True)
        table.add_column("Wind", justify="left", style="cyan", no_wrap=True)
        table.add_column("Forecast", justify="left", no_wrap=False)
        
        # Loop through each day/night in the forecast...
        for day in wx_json['properties']['periods']:
            #...add a row to the table for the day/night
            table.add_row(day['name'], str(day['temperature']) + day['temperatureUnit'], str(day['windSpeed']) + ' ' + day['windDirection'], day['shortForecast'])
        
        # Print the table out to the screen
        console = Console()
        console.print(table)

if __name__ == "__main__":
    logger = prep_logger()
    get_weather()
    print()
