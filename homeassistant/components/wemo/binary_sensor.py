"""Support for WeMo binary sensors."""
import asyncio

from pywemo import Insight, Maker

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN as WEMO_DOMAIN
from .entity import WemoEntity
from .wemo_device import DeviceCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WeMo binary sensors."""

    async def _discovered_wemo(coordinator: DeviceCoordinator) -> None:
        """Handle a discovered Wemo device."""
        if isinstance(coordinator.wemo, Insight):
            async_add_entities([InsightBinarySensor(coordinator)])
        elif isinstance(coordinator.wemo, Maker):
            async_add_entities([MakerBinarySensor(coordinator)])
        else:
            async_add_entities([WemoBinarySensor(coordinator)])

    async_dispatcher_connect(hass, f"{WEMO_DOMAIN}.binary_sensor", _discovered_wemo)

    await asyncio.gather(
        *(
            _discovered_wemo(coordinator)
            for coordinator in hass.data[WEMO_DOMAIN]["pending"].pop("binary_sensor")
        )
    )


class WemoBinarySensor(WemoEntity, BinarySensorEntity):
    """Representation a WeMo binary sensor."""

    @property
    def is_on(self) -> bool:
        """Return true if the state is on. Standby is on."""
        return bool(self.wemo.get_state())


class MakerBinarySensor(WemoEntity, BinarySensorEntity):
    """Maker device's sensor port."""

    _name_suffix = "Sensor"

    @property
    def is_on(self) -> bool:
        """Return true if the Maker's sensor is pulled low."""
        return bool(self.wemo.has_sensor) and self.wemo.sensor_state == 0


class InsightBinarySensor(WemoBinarySensor):
    """Sensor representing the device connected to the Insight Switch."""

    _name_suffix = "Device"

    @property
    def is_on(self) -> bool:
        """Return true device connected to the Insight Switch is on."""
        return super().is_on and self.wemo.insight_params["state"] == "1"
