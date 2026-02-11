from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfTime,
    UnitOfElectricPotential,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT
)
from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Setup der Eberspächer Sensoren."""
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]

    devices = await api.get_devices()
    entities = []

    for device in devices:
        entities.append(EberspaecherTempSensor(api, device))
        entities.append(EberspaecherStateSensor(api, device))
        entities.append(EberspaecherRuntimeSensor(api, device))
        entities.append(EberspaecherVoltageSensor(api, device))
        entities.append(EberspaecherSignalSensor(api, device))

    async_add_entities(entities, True)


class EberspaecherBaseSensor(SensorEntity):
    """Basisklasse für alle Sensoren, hält API und Device-ID."""

    def __init__(self, api, device):
        self._api = api
        self._device = device
        self._imei = device.get("imei")
        self._name_prefix = device.get("name", "Eberspächer")

    async def async_update(self):
        """Standard-Update für Sensoren, die Daten aus der Hauptliste (/calls) holen."""
        devices = await self._api.get_devices()
        for dev in devices:
            if dev.get("imei") == self._imei:
                self._device = dev


class EberspaecherTempSensor(EberspaecherBaseSensor):
    """Zeigt die gemessene Innenraumtemperatur an."""

    def __init__(self, api, device):
        super().__init__(api, device)
        self._attr_unique_id = f"{self._imei}_temperature"
        self._attr_name = f"{self._name_prefix} Temperatur"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        # Pfad: heaters[0] -> lastMeasuredTemperature -> temperature
        heaters = self._device.get("heaters", [{}])
        if not heaters: return None

        temp_data = heaters[0].get("lastMeasuredTemperature")
        if isinstance(temp_data, dict):
            return temp_data.get("temperature")
        # Manchmal ist es auch direkt der Wert
        if isinstance(temp_data, (int, float)):
            return temp_data
        return None


class EberspaecherStateSensor(EberspaecherBaseSensor):
    """Zeigt den aktuellen Status (HEATING, VENTILATION, OFF)."""

    def __init__(self, api, device):
        super().__init__(api, device)
        self._attr_unique_id = f"{self._imei}_status"
        self._attr_name = f"{self._name_prefix} Status"
        self._attr_icon = "mdi:list-status"

    @property
    def native_value(self):
        heaters = self._device.get("heaters", [{}])
        if not heaters: return "Unknown"
        return heaters[0].get("heaterState", "OFF")


class EberspaecherRuntimeSensor(EberspaecherBaseSensor):
    """Zeigt die verbleibende Laufzeit an, wenn die Heizung läuft."""

    def __init__(self, api, device):
        super().__init__(api, device)
        self._attr_unique_id = f"{self._imei}_remaining_runtime"
        self._attr_name = f"{self._name_prefix} Restlaufzeit"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_native_unit_of_measurement = UnitOfTime.MINUTES
        self._attr_icon = "mdi:timer-sand"

    @property
    def native_value(self):
        heaters = self._device.get("heaters", [{}])
        if not heaters: return 0

        current_op = heaters[0].get("currentOperation")
        if isinstance(current_op, dict):
            return current_op.get("remainingRuntime", 0)
        return 0


class EberspaecherVoltageSensor(EberspaecherBaseSensor):
    """Zeigt die Batteriespannung (holt Daten vom Heartbeat)."""

    def __init__(self, api, device):
        super().__init__(api, device)
        self._attr_unique_id = f"{self._imei}_voltage"
        self._attr_name = f"{self._name_prefix} Batteriespannung"
        self._attr_device_class = SensorDeviceClass.VOLTAGE
        self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:car-battery"

    async def async_update(self):
        """Spezial-Update: Ruft get_diagnostics (Heartbeat) auf."""
        diag = await self._api.get_diagnostics(self._imei)
        if diag and "voltage" in diag:
            # Wert kommt in Millivolt (z.B. 12559 -> 12.56 V)
            val = diag["voltage"]
            if val:
                self._attr_native_value = round(val / 1000, 2)


class EberspaecherSignalSensor(EberspaecherBaseSensor):
    """Zeigt die GSM-Signalstärke an."""

    def __init__(self, api, device):
        super().__init__(api, device)
        self._attr_unique_id = f"{self._imei}_rssi"
        self._attr_name = f"{self._name_prefix} Signalstärke"
        self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
        self._attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:signal"

    async def async_update(self):
        """Spezial-Update: Ruft get_diagnostics (Heartbeat) auf."""
        diag = await self._api.get_diagnostics(self._imei)
        if diag and "rssi" in diag:
            csq = diag["rssi"]
            # Umrechnung von CSQ (0-31) in dBm
            # Formel: (CSQ * 2) - 113
            # Beispiel: 12 -> -89 dBm
            if isinstance(csq, int) and 0 <= csq <= 31:
                self._attr_native_value = (csq * 2) - 113
            else:
                # Falls schon dBm oder anderer Wert
                self._attr_native_value = csq