# Azzurro ZCS Home Assistant integration

This is a simple integration for Home Assistent to interface with Azzurro ZCS inverters (tested on ZCS AZZURRO ZS1 3680TLM-WS),
it is derived from https://github.com/sdesalve/zcsazzurro, but differently from it this
one works locally without going on cloud. 
This integrations sends a GET request to the local webserver of the Inverter and parses the data in the response.

## Installation
In order to install it on home assistant just copy the files from this repository inside a new folder in the custom_components path:

<home assistant config folder>/custom_components/azzurrozcs

then add these lines in the configuration.yaml file:
```
sensor:
  - platform: azzurrozcs
    name: solarinverter
    ip_address: <ip address of your inverter>
    username: "username of the local webgui of the inverter"
    password: "password of the local webgui of the inverter"


template:
  - sensor:
      - name: "Power Now"
        unit_of_measurement: "W"
        state: >
          {% set power = state_attr('sensor.solarinverter','power_now') | float(0) %}
          {{ power }}
        state_class: measurement
        device_class: power
        icon: mdi:solar-power
      - name: "Energy today"
        unit_of_measurement: "kWh"
        state: >
          {% set energy = state_attr('sensor.solarinverter','energy_today') | float(0) %}
          {{ energy | round(2) }}
        state_class: measurement
        device_class: energy
        icon: mdi:power-socket-it
      - name: "Energy total"
        unit_of_measurement: "kWh"
        state: >
          {% set energy = state_attr('sensor.solarinverter','energy_total') | float(0) %}
          {{ energy | round(2) }}
        state_class: measurement
        device_class: energy
        icon: mdi:power-socket-it
```