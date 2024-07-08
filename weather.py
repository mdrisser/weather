#!/usr/bin/python3

import requests
import json
import tomllib
import logging

from rich.prompt import Prompt


CONFIG_DIR = "/home/mike/.config/weather/"


location = ""

# Read the TOML configuration file
with open(f"{CONFIG_DIR}weather.toml", "rb") as f:
    config = tomllib.load(f)
    stations = config['stations']

# Set a couple of variable defaults
default = "N/A"
places = []
noaa_office = ""


def prep_logger():
    """Prepare a logger """
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
    import rich.box
    from rich import print
    from rich.console import Console
    from rich.table import Table

    global logger

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
        
        periods = wx_json['properties']['periods']
        #print(periods)
        # Loop through each day/night in the forecast and add a row to the table for each day/night
        # Loop through each day/night in the forecast...
        for day in wx_json['properties']['periods']:
            #...add a row to the table for the day/night
            table.add_row(day['name'], str(day['temperature']) + day['temperatureUnit'], str(day['windSpeed']) + ' ' + day['windDirection'], day['shortForecast'])
            
        #list(map(lambda day: table.add_row(day['name'], str(day['temperature'])+day['temperatureUnit'], str(day['windSpeed'])+' '+day['windDirection'], day['shortForecast']),
        #   periods))   
        
        # Print the table out to the screen
        console = Console()
        console.print(table)


def get_wxcondix():
    import convert.convert as Convert
    import convert.temperature as temp
    import convert.speed as speed
    import utilities.terminal as term

    from rich import print
    from rich.prompt import Prompt
    from tabulate import tabulate

    global logger

    for station in stations:
        if location == station['name']:
            locale = station['locale']
            noaa_office = station['noaa_office']
            noaa_grid_x = station['noaa_grid_x']
            noaa_grid_y = station['noaa_grid_y']
            station_id = station['station_id']

    wx_url = f"https://api.weather.gov/stations/{station_id}/observations/latest"

    req_headers = {'user-agent': 'weather.py/mdrisser@gmail.com'}

    print()

    try:
        r = requests.get(wx_url, headers=req_headers)
        r.raise_for_status()
    except Exception as err:
        logger.error(err)
        print(f"Error: [bold red]{err}[/bold red]")
    else:
        wx_json = json.loads(r.text)
        
        observations = wx_json['properties']
        title = f"Current Weather Conditions\nin {locale}"

        if observations['temperature']['value'] != None:
            temperature = f"{round(temp.c_to_f(observations['temperature']['value']))}{term.deg_sign} F"
        else:
            temperature = "N/A"

        if observations['dewpoint']['value'] != None:
            dewpoint = f"{round(temp.c_to_f(observations['dewpoint']['value']))}{term.deg_sign} F"
        else:
            dewpoint = "N/A"

        if observations['relativeHumidity']['value'] != None:
            humidity = f"{round(observations['relativeHumidity']['value'])}%"
        else:
            humidity = "N/A"
        
        wind_dir = observations['windDirection']['value']

        if wind_dir == None:
            wind_dir = 0
        
        cardinal = Convert.angle_to_card(wind_dir)
        wind_direction = f"{cardinal} ({wind_dir}{term.deg_sign})"

        wind_speed = observations['windSpeed']['value']

        if wind_speed == None:
            wind_speed = "0 mph"
        else:
            wind_speed = f"{round(speed.kph_to_mph(wind_speed))} mph"

        gust = observations['windGust']['value']
        if gust:
            gust = f"{round(speed.kph_to_mph(gust))}"
        else:
            gust = "None"

        wx_data = [
            ['Temperature', temperature],
            ['Dewpoint', dewpoint],
            ['Humidity', humidity],
            ['Wind Direction', wind_direction],
            ['Wind Speed', wind_speed],
            ['Wind Gust', gust],
        ]

        print(title)
        print(tabulate(wx_data))


if __name__ == "__main__":
    # Prepare the logger
    logger = prep_logger()
    
    # Get the list of places for choices in the prompt
    places = get_places()
    
     # Ask the user which station to get the information from
    location = Prompt.ask("Get weather for which city?", choices=places, default=default)
    
    wx = Prompt.ask("Get?", choices=["Forecast","Conditions"], default="Forecast")
    
    if wx == "Forecast":
        get_weather()
    else:
        get_wxcondix()
    
    print()
