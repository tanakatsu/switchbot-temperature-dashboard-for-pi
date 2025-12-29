import datetime
import os
from time import sleep
from zoneinfo import ZoneInfo

import schedule
from dotenv import load_dotenv
from requests.exceptions import ConnectionError

from amedas import AmedasDataClient
from influxdb import InfluxDB1Writer
from switchbot import Device, SwitchBotClient

load_dotenv()


def task_switchbot(
    switchbot_client: SwitchBotClient,
    device_list: list[Device],
    influxdb_writer: InfluxDB1Writer,
):
    """
    SwitchBotデバイスの状態を取得してInfluxDBに書き込む
    """
    try:
        measurement = "sensor"
        for device in device_list:
            status = switchbot_client.get_device_status(device.device_id)
            print(
                f"デバイス名: {device.device_name}, デバイスID: {device.device_id}, 状態: {status}"
            )
            with influxdb_writer as w:
                w.write(
                    measurement,
                    "sensor_id",
                    device.device_name,
                    status.temperature,
                    status.humidity,
                )
    except ConnectionError as e:
        print(f"ConnectionError occurred: {e}")


def task_amedas(
    amedas_client: AmedasDataClient,
    amedas_location_name: str,
    influxdb_writer: InfluxDB1Writer,
):
    """
    30分前のAMEDASデータを取得してInfluxDBに書き込む
    """
    try:
        measurement = "amedas"
        now = datetime.datetime.now(datetime.UTC).replace(second=0, microsecond=0)
        target_time = now - datetime.timedelta(minutes=30)
        target_time = target_time.replace(
            minute=round(target_time.minute - 5, -1)
        )  # 10分単位に丸める

        local_tz = ZoneInfo("Asia/Tokyo")
        local_target_time = target_time.astimezone(local_tz)

        df = amedas_client.fetch_one(local_target_time)
        temp_c = df.iloc[0]["temp"]
        humidity = df.iloc[0]["humidity"]
        print(
            f"Amedasデータ取得: {local_target_time}, temp_c: {temp_c:.2f}, humidity: {humidity:.2f}"
        )

        with influxdb_writer as w:
            w.write(
                measurement,
                "location_id",
                amedas_location_name,
                temp_c,
                humidity,
                target_time,  # UTC時間で書き込む
            )
    except ConnectionError as e:
        print(f"ConnectionError occurred: {e}")


def main():
    switchbot_client = SwitchBotClient(os.environ["SWITCHBOT_TOKEN"])
    devices = switchbot_client.get_devices()
    if len(devices) == 0:
        raise RuntimeError("No devices found.")
    print("Found devices:")
    for device in devices:
        print(f"- {device.device_name} (ID: {device.device_id})")

    amedas_location_id = os.environ.get("AMEDAS_LOCATION_ID")
    if amedas_location_id is not None:
        amedas_client = AmedasDataClient(amedas_location_id)
        df_observation_points = amedas_client.get_observation_points()
        amedas_location_name = df_observation_points.loc[amedas_location_id, "kjName"]
        print(f"AMEDAS location ID: {amedas_location_id} ({amedas_location_name})")

    influxdb_writer = InfluxDB1Writer(
        url=os.environ["INFLUXDB_URL"],
        db=os.environ["INFLUXDB_DB"],
        username=os.environ.get("INFLUXDB_ADMIN_USER"),
        password=os.environ.get("INFLUXDB_ADMIN_PASSWORD"),
    )

    schedule.every(10).minutes.do(
        task_switchbot, switchbot_client, devices, influxdb_writer
    )
    if amedas_location_id is not None:
        schedule.every(10).minutes.do(
            task_amedas, amedas_client, amedas_location_name, influxdb_writer
        )

    while True:
        schedule.run_pending()
        sleep(1)


if __name__ == "__main__":
    main()
