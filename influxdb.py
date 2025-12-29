from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import requests


def _to_ns(dt: datetime) -> int:
    """datetime -> epoch nanoseconds"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return int(dt.timestamp() * 1_000_000_000)


def _escape_tag_value(s: str) -> str:
    # Influx line protocol: tag keys/values escape: comma, space, equals
    return (
        s.replace("\\", "\\\\")
        .replace(" ", "\\ ")
        .replace(",", "\\,")
        .replace("=", "\\=")
    )


def _escape_measurement(s: str) -> str:
    # measurement escapes: comma, space
    return s.replace("\\", "\\\\").replace(" ", "\\ ").replace(",", "\\,")


@dataclass
class InfluxDB1Writer:
    """
    InfluxDB 1.8 writer via HTTP line protocol.

    - url: e.g. http://influxdb:8086
    - db: database name (e.g. switchbot)
    - username/password: set if auth enabled (recommended)
    """

    url: str
    db: str
    username: str | None = None
    password: str | None = None
    timeout_sec: float = 5.0

    def __enter__(self) -> InfluxDB1Writer:
        self._session = requests.Session()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._session.close()

    def write(
        self,
        measurement: str,
        tag_name: str,
        tag: str,
        temp_c: float,
        humidity: float,
        time: datetime | None = None,
    ) -> None:
        if time is None:
            time = datetime.now(UTC)

        m = _escape_measurement(measurement)
        tn = _escape_tag_value(tag_name)
        tv = _escape_tag_value(tag)

        # fields: numbers are unquoted
        # timestamp: ns
        line = f"{m},{tn}={tv} temp_c={float(temp_c)},humidity={float(humidity)} {_to_ns(time)}"

        endpoint = f"{self.url.rstrip('/')}/write"
        params = {"db": self.db, "precision": "ns"}

        auth = None
        if self.username is not None and self.password is not None:
            auth = (self.username, self.password)

        r = self._session.post(
            endpoint,
            params=params,
            data=line.encode("utf-8"),
            headers={"Content-Type": "text/plain; charset=utf-8"},
            auth=auth,
            timeout=self.timeout_sec,
        )
        # InfluxDB 1.x: success is 204 No Content
        if r.status_code != 204:
            raise RuntimeError(
                f"InfluxDB write failed: {r.status_code} {r.text.strip()} (line={line})"
            )
