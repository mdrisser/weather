# Weather
A small Python command line application that fetches weather information from weather.gov and displays it in the terminal.

A TOML config file allows for a customized list of locations to fetch weather information for. Please read the coonfig file carefully as it contains the steps necessary to get the required information for each location. Future versions may automatically retrieve this information, but for now it must be done manually.

## Usage
weather.py [OPTION]
Fetch either a weather forecast or the current weather conditions for a given location.

    -l,    --location    the location to pull the weather for, must be in the list of stations in the TOML config file
    -t,    --type        the type of weather information to pull, either forecast or current

If either, or both, of the command line arguments are omitted, the script will prompt for the missing information.

## Files
### weather.py
Fetches the desired weather forecast or current conditions from the select place.

Uses the [convert](https://github.com/mdrisser/convert) and [utilities](https://github.com/mdrisser/utilities) libraries

### weather.toml
This is the configuration file.

## Installation

1. Download the latest release
2. Open weather.py in a text editor and change the location for CONFIG_DIR
3. Copy/move weather.toml to the location of CONFIG_DIR
4. Copy/move weather.py to a location in your PATH
5. On Unix/Linux make weather.py executable. (chmod +x weather.py)
6. Run weather.py either, both, or none of the commandline arguments (-l <LOCATION> -t [current | forecast]) If you do not provide either or both of the commandline arguments, the script will prompt you for the missing information.

## Screenshots
![weather-screenshot-01](https://github.com/user-attachments/assets/92d38921-5f8f-4f9a-b365-7b191567f046)

_(Above) Using the commandline arguments for current conditions_


![weather-screenshot-02](https://github.com/user-attachments/assets/b158c7d6-bc27-429a-a6c7-ca2cc89a2149)

_(Above) Using the commandline arguments for forecast_


![weather-screenshot-03](https://github.com/user-attachments/assets/420e9643-298c-4f82-9fdc-c28373a3a3c5)

_(Above) Omitting commandline arguments and being prompted for the missing information. Notice that items shown in parenthesis are defaults and you can just hit Enter to accept them. Defaults are set in the weather.toml file._


