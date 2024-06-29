#!/usr/bin/env python3
import requests
import json
import logging
import tomllib

import convert.convert as Convert
import convert.temperature as temp
import convert.speed as speed
import utilities.terminal as term

from rich import print
from rich.prompt import Prompt
from tabulate import tabulate

default = "N/A"

with open("weather.toml", "rb") as f:
    config = tomllib.load(f)
    stations = config['stations']

def prep_logger():
    lg = logging.getLogger(__name__)
    logging.basicConfig(
        filename = config['log']['file'],
        level = logging.INFO
    )

    return lg


def get_places():
    global default

    places = []

    for station in stations:
        places.append(station['name'])

        if station['default'] == 'True':
            default = station['name']
    
    return places


def get_wxcondix():
    global logger

    places = get_places()

    location = Prompt.ask("Get weather for which city?", choices=places, default=default)

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
    logger = prep_logger()
    get_wxcondix()
    print()
