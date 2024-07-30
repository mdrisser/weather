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

