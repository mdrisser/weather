# Weather
A pair of Python scripts to collect weather information from weather.gov. One script retrieves forecasts, the second retrieves current weather observations.

The script share a common configuration files, written in TOML to determine which stations to collect the information from.
## Scripts
### weather.py
This script pulls the weather information for the configured weather stations

### wx_condix.py
This script pulls the latest weather observations from the selected weather station.

### weather.toml
This is the configuration file that is shared by both scripts.

