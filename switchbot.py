from dataclasses import dataclass
from typing import Self

import requests


@dataclass(frozen=True)
class Device:
    device_id: str
    device_name: str
    device_type: str | None
    hub_device_id: str | None

    @classmethod
    def from_json(cls, data) -> list[Self]:
        device_list = []
        for device_info in data["body"]["deviceList"]:
            device = Device(
                device_id=device_info["deviceId"],
                device_name=device_info["deviceName"],
                device_type=device_info.get("deviceType", None),
                hub_device_id=device_info.get("hubDeviceId", None),
            )
            device_list.append(device)
        return device_list


@dataclass(frozen=True)
class DeviceStatus:
    temperature: float
    humidity: float
    battery: int | None

    @classmethod
    def from_json(cls, data) -> "DeviceStatus":
        return cls(
            temperature=data["body"]["temperature"],
            humidity=data["body"]["humidity"],
            battery=data["body"].get("battery", None),
        )


class SwitchBotClient:
    BASE_URL = "https://api.switch-bot.com/v1.0"

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json; charset=utf8",
        }

    def get_devices(self) -> list[Device]:
        url = f"{self.BASE_URL}/devices"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        if data["statusCode"] != 100:
            raise Exception(f"Error fetching devices: {data['message']}")
        else:
            return Device.from_json(data)

    def get_device_status(self, device_id: str):
        url = f"{self.BASE_URL}/devices/{device_id}/status"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return DeviceStatus.from_json(response.json())
