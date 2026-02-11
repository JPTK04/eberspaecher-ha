import asyncio
import aiohttp
import sys
import os
import importlib.util


# --- IMPORT TRICK ---
def import_api_module():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "custom_components", "eberspaecher-ha", "api.py")
    spec = importlib.util.spec_from_file_location("api_module", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["api_module"] = module
    spec.loader.exec_module(module)
    return module.EberspaecherAPI


try:
    EberspaecherAPI = import_api_module()
except Exception as e:
    print(f"Fehler beim Laden der API: {e}")
    sys.exit(1)
# --------------------

try:
    from secrets import MY_USERNAME, MY_PASSWORD
except ImportError:
    print("Bitte secrets.py erstellen!")
    sys.exit(1)


async def main():
    print(f"\n--- Eberspächer Finale Diagnose ---")

    conn = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=conn) as session:
        api = EberspaecherAPI(MY_USERNAME, MY_PASSWORD, session)

        print("1. Login...")
        if not await api.login():
            return

        print("2. Hole Fahrzeugdaten...")
        devices = await api.get_devices()

        if not devices:
            print("❌ Keine Geräte gefunden.")
            return

        car = devices[0]
        imei = car.get("imei")
        name = car.get("name", "Unbekannt")

        # Heizungsdaten (Standard)
        heaters = car.get("heaters", [{}])
        heater = heaters[0] if heaters else {}
        status = heater.get("heaterState", "UNKNOWN")

        # Temperatur
        temp_raw = heater.get("lastMeasuredTemperature")
        temp_str = "N/A"
        if isinstance(temp_raw, dict):
            temp_str = f"{temp_raw.get('temperature')}°C"

        print(f"\n🚙 Fahrzeug: {name} (IMEI: {imei})")
        print(f"   Status:     {status}")
        print(f"   Temperatur: {temp_str}")

        # DIAGNOSE (Heartbeat)
        print("\n3. Hole Diagnose (Heartbeat)...")
        diag = await api.get_diagnostics(imei)

        if diag:
            # Spannung
            volt_mv = diag.get("voltage", 0)
            volt_str = f"{volt_mv / 1000:.2f} V" if volt_mv else "N/A"

            # Signal
            rssi = diag.get("rssi", "N/A")
            # Umrechnung falls gewünscht
            if isinstance(rssi, int):
                dbm = (rssi * 2) - 113
                rssi_str = f"{rssi} ({dbm} dBm)"
            else:
                rssi_str = str(rssi)

            print(f"   🔋 Batterie: {volt_str}")
            print(f"   📶 Signal:   {rssi_str}")
            print(f"   🕒 Zeitstempel: {diag.get('timestamp')}")
        else:
            print("❌ Kein Heartbeat empfangen.")

        print("\n" + "=" * 30)


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())