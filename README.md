# Eberspächer EasyStart Web for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![version](https://img.shields.io/github/v/release/JPTK04/eberspaecher-ha)](https://github.com/JPTK04/eberspaecher-ha/releases)

A custom Home Assistant integration for **Eberspächer auxiliary heaters** (Standheizungen) controlled via the **EasyStart Web** portal (myeberspaecher.com).

This integration creates a connection between your car and Home Assistant, allowing you to control heating/ventilation, set runtimes, and monitor vehicle status like battery voltage and temperature.

---

## ✨ Features

* **Control:** Turn heater **On/Off**.
* **Modes:** Switch between **Heating** (🔥) and **Ventilation** (❄️).
* **Runtime:** Set the target runtime (10 - 120 minutes) via a number slider.
* **Sensors:**
    * 🌡️ Interior Temperature
    * 🔋 Battery Voltage (fetched via Heartbeat)
    * 📶 GSM Signal Strength (dBm)
    * ⏳ Remaining Runtime
    * 📋 Current Status

## 📦 Installation

### Option 1: HACS (Recommended)

1.  Open **Home Assistant** > **HACS** > **Integrations**.
2.  Click the **3 dots** in the top right corner -> **Custom repositories**.
3.  Paste the repository URL:
    ```
    [https://github.com/JPTK04/eberspaecher-ha](https://github.com/JPTK04/eberspaecher-ha)
    ```
4.  Select Category: **Integration**.
5.  Click **Add**.
6.  Click **Download** on the new "Eberspächer EasyStart Web" card.
7.  **Restart Home Assistant**.

### Option 2: Manual

1.  Download the latest release zip from GitHub.
2.  Copy the `eberspaecher` folder from `custom_components/` into your Home Assistant's `/config/custom_components/` directory.
3.  Restart Home Assistant.

## ⚙️ Configuration

1.  Go to **Settings** > **Devices & Services**.
2.  Click **Add Integration** in the bottom right.
3.  Search for **Eberspächer**.
4.  Enter your **Email** and **Password** (the same used for [myeberspaecher.com](https://myeberspaecher.com)).
5.  The integration will automatically discover your vehicle(s) using the name defined in the Eberspächer app.

## 📱 Usage

This integration creates dynamic entities based on your car's name.
*Example: If your car is named "Golf", the entities will be `switch.golf_heater`, `sensor.golf_temperature`, etc.*

### How to control:
1.  **Select Mode:** Use the dropdown (`select.*_mode`) to choose **Heating** or **Ventilation**.
2.  **Set Time:** Use the number slider (`number.*_runtime`) to set the duration (e.g., 30 mins).
3.  **Start:** Toggle the switch (`switch.*_heater`) to **On**.

*Note: The integration remembers your Mode and Runtime settings locally in Home Assistant.*

### Example Dashboard Card (YAML)

Replace `my_car` with the actual name of your vehicle entity.

```yaml
type: entities
title: Standheizung
entities:
  - entity: switch.my_car_heater
    name: Power
  - entity: select.my_car_mode
    name: Mode
  - entity: number.my_car_runtime
    name: Runtime
  - type: divider
  - entity: sensor.my_car_temperature
  - entity: sensor.my_car_voltage
  - entity: sensor.my_car_status
  - entity: sensor.my_car_remaining_runtime