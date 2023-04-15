from __future__ import annotations
import re
from inspect import signature
from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.components.rest.data import RestData
from requests.auth import HTTPBasicAuth
from homeassistant.components.sensor import (
    DEVICE_CLASS_ENERGY,
    PLATFORM_SCHEMA,
    STATE_CLASS_MEASUREMENT,
    SensorEntity,
)
from homeassistant.const import (
    ATTR_DATE,
    ATTR_TEMPERATURE,
    ATTR_TIME,
    CONF_NAME,
    ENERGY_WATT_HOUR,
)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

import json

_LOGGER = logging.getLogger(__name__)

CONF_IP_ADDR = "ip_address"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

DEFAULT_NAME = "azzurrozcs"
DEFAULT_VERIFY_SSL = False

SCAN_INTERVAL = timedelta(minutes=2)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_IP_ADDR): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    #Azzurro ZCS Setup
    name = config.get(CONF_NAME)
    zcs_username = config.get(CONF_USERNAME)
    zcs_password = config.get(CONF_PASSWORD)
    zcs_address = "http://" + config.get(CONF_IP_ADDR) + "/status.html"
    method = "GET"
    auth = HTTPBasicAuth(zcs_username, zcs_password)
    verify_ssl = DEFAULT_VERIFY_SSL
    timeout = 60
    headers = None



    _LOGGER.info("method: %s", method)

    sig = signature(RestData)
    if len(sig.parameters) > 9:
        #for compatibility with Home Assistant 2023
        rest = RestData(hass, method, zcs_address,'utf-8', auth, headers, None, None, verify_ssl, timeout)
    else:
        rest = RestData(hass, method, zcs_address, auth, headers, None, None, verify_ssl, timeout)
    
    await rest.async_update()

    if rest.data is None:
        _LOGGER.error("Unable to start fetching data from Azzurro ZCS")
        # return False

    async_add_entities([ZCSSensor(rest, name)],update_before_add=True)

class ZCSSensor(SensorEntity):
    """Representation of a ZCSAzzurro sensor."""

    _attr_state_class = STATE_CLASS_MEASUREMENT
    _attr_device_class = DEVICE_CLASS_ENERGY
    _attr_native_unit_of_measurement = ENERGY_WATT_HOUR

    def __init__(self, rest, name):
        """Initialize a ZCSAzzurro sensor."""
        self.rest = rest
        self.req_retries = 0
        self._attr_name = name
        self._attributes = None
        self.zcs_sensor = {}
        self._state = False

    @property
    def state(self):
        """Return the state of the device."""
        value = self._state
        _LOGGER.info("Return the state: %s", value)
        return value


    @property
    def extra_state_attributes(self):
        """Return the state attributes of the monitored installation."""
        if self.zcs_sensor is not None:
            _LOGGER.info("Return the state attributes")
            
            try: power_now = self.zcs_sensor["power_now"]
            except: power_now = 0
            try: energy_today = self.zcs_sensor["energy_today"]
            except: energy_today = 0
            try: energy_total = self.zcs_sensor["energy_total"]
            except: energy_total = 0
            _LOGGER.info("Power_now = " + str(power_now))
            return {"power_now": power_now,"energy_today":energy_today,"energy_total":energy_total}


    async def async_update(self):
        await self.rest.async_update()
        self._async_update_from_rest_data()

    async def async_added_to_hass(self):
        """Ensure the data from the initial update is reflected in the state."""
        self._async_update_from_rest_data()

    @callback
    def _async_update_from_rest_data(self):
        """Update state from the rest data."""
        _LOGGER.info("ZCS Rest response")
        try:
            rest_data = self.rest.data
            if rest_data is not None:
                self.req_retries = 0
                self._state = True
                for line in rest_data.splitlines():
                    if("var webdata_now_p" in line):
                        self.zcs_sensor["power_now"] = float(re.search(r'\"(.*?)\"',line).group(1))
                        _LOGGER.info(self.zcs_sensor["power_now"])
                    if("var webdata_today_e" in line):
                        self.zcs_sensor["energy_today"] = float(re.search(r'\"(.*?)\"',line).group(1))
                        _LOGGER.info(self.zcs_sensor["energy_today"])
                    if("var webdata_total_e" in line):
                        self.zcs_sensor["energy_total"] = float(re.search(r'\"(.*?)\"',line).group(1))
                        _LOGGER.info(self.zcs_sensor["energy_total"])
            else:
                _LOGGER.warning("Empty reply")
                if(self.req_retries < 5):
                    self.req_retries += 1
                else:
                    self.zcs_sensor["power_now"] = 0.0
                    self._state = False

        except TypeError:
            _LOGGER.warning("REST result not valid")
            _LOGGER.info("Erroneous data: %s", rest_data)


