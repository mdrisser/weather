# Weather
A small Python command line application that fetches weather information from weather.gov and displays it in the terminal.

A TOML config file allows for a customized list of locations to fetch weather information for. Please read the coonfig file carefully as it contains the steps necessary to get the required information for each location. Future versions may automatically retrieve this information, but for now it must be done manually.

## Files
### weather.py
This script prompts the user to select one of the stations listed in the config file and also to select either forecast or current conditions to fetch.

Uses the [convert](https://github.com/mdrisser/convert) and [utilities](https://github.com/mdrisser/utilities) libraries

### weather.toml
This is the configuration file.

