"""AWS IoT MQTT subscriber wrapper.

Handles the TLS connection to the broker using the cert from TyphurAPI, subscribes to
the device telemetry topics, and dispatches parsed messages to user callbacks.

See docs/reference/PROTOCOL.md for the message format.
"""

from __future__ import annotations

import json
import ssl
import sys
import time
import uuid
from typing import Callable, Optional

import paho.mqtt.client as mqtt

from cliron_chef.api import TyphurAPI


def tenths_to_f(value) -> float:
    """Convert wire-format temperature (tenths of °F) to a regular float.

    Returns nan if the value is None or non-numeric.
    """
    if value is None:
        return float("nan")
    try:
        return float(value) / 10.0
    except (TypeError, ValueError):
        return float("nan")


class TyphurMQTT:
    """MQTT subscriber for Typhur device telemetry.

    Usage:
        >>> api = TyphurAPI.from_cached_credentials()
        >>> mq = TyphurMQTT(api)
        >>> mq.on_probe = lambda data: print(f"probe: {tenths_to_f(data.get('curTemperature'))}°F")
        >>> mq.on_dome  = lambda data: print(f"dome state: {data.get('globalStatus')}")
        >>> mq.subscribe("AF04", "<dome_id>")
        >>> mq.subscribe("WT01", "<probe_id>")
        >>> mq.start()
        >>> time.sleep(60)
        >>> mq.stop()

    Callbacks:
        on_probe(probe_dict): called for each WT01:status:report (single probe data)
        on_dome(cmd_data):   called for each AF04:status:report (cmdData dict)
        on_receipt(receipt): called for each device:cmd:receipt (cmdData dict)
        on_message(payload, topic): generic — called for every message
        on_connect(rc):      called when MQTT connects
        on_disconnect(rc):   called on disconnect
    """

    def __init__(self, api: TyphurAPI, client_id_suffix: Optional[str] = None):
        self.api = api
        cert_path, key_path, base_client_id = api.fetch_mqtt_files()
        endpoint = api.get_mqtt_endpoint()

        self.endpoint = endpoint["endpoint"]
        self.port = int(endpoint.get("port", 8883))
        suffix = client_id_suffix or f"cliron-{uuid.uuid4().hex[:8]}"
        self.client_id = f"{base_client_id}-{suffix}"
        self.cert_path = cert_path
        self.key_path = key_path

        self._client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv311)
        self._client.tls_set(
            certfile=cert_path,
            keyfile=key_path,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1_2,
        )
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        self._subscriptions = []  # list of (topic, qos)
        self._started = False

        # User callbacks (override after construction)
        self.on_probe: Optional[Callable[[dict], None]] = None
        self.on_dome: Optional[Callable[[dict], None]] = None
        self.on_receipt: Optional[Callable[[dict], None]] = None
        self.on_message: Optional[Callable[[dict, str], None]] = None
        self.on_connect: Optional[Callable[[int], None]] = None
        self.on_disconnect: Optional[Callable[[int], None]] = None

    def subscribe(self, device_model: str, device_id: str, qos: int = 0):
        """Subscribe to a device's pub topic."""
        topic = f"device/{device_model}/{device_id}/pub"
        self._subscriptions.append((topic, qos))
        if self._started:
            self._client.subscribe(topic, qos=qos)

    def start(self):
        """Connect to the broker and start the loop in a background thread."""
        if self._started:
            return
        self._client.connect(self.endpoint, self.port, keepalive=60)
        self._client.loop_start()
        self._started = True

    def stop(self):
        """Disconnect and stop the loop."""
        if not self._started:
            return
        self._client.loop_stop()
        self._client.disconnect()
        self._started = False

    # -- Internal callbacks --------------------------------------------------

    def _on_connect(self, client, userdata, flags, rc, props=None):
        for topic, qos in self._subscriptions:
            client.subscribe(topic, qos=qos)
        if self.on_connect:
            self.on_connect(rc)

    def _on_disconnect(self, client, userdata, rc, props=None):
        if self.on_disconnect:
            self.on_disconnect(rc)

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except Exception:
            return

        cmd_data = payload.get("cmdData", {}) or {}
        cmd_type = payload.get("cmdType", "")

        if self.on_message:
            self.on_message(payload, msg.topic)

        if cmd_type.startswith("WT01:status") or cmd_type.startswith("WT13:status"):
            probes = cmd_data.get("probes") or []
            if not probes and "curTemperature" in cmd_data:
                probes = [cmd_data]
            for probe_data in probes:
                if self.on_probe:
                    self.on_probe(probe_data)
        elif cmd_type == "AF04:status:report":
            if self.on_dome:
                self.on_dome(cmd_data)
        elif cmd_type == "device:cmd:receipt":
            if self.on_receipt:
                self.on_receipt(cmd_data)


def tail_telemetry(api: TyphurAPI, dome_id: Optional[str] = None,
                   probe_id: Optional[str] = None, seconds: int = 60):
    """Convenience: print live telemetry for the given duration.

    Suitable for `cliron-chef monitor` and similar.
    """
    mq = TyphurMQTT(api)
    if dome_id:
        mq.subscribe("AF04", dome_id)
    if probe_id:
        mq.subscribe("WT01", probe_id)

    mq.on_probe = lambda p: print(
        f"[probe] internal={tenths_to_f(p.get('curTemperature')):.1f}°F "
        f"ambient={tenths_to_f(p.get('curAmbientTemperature')):.0f}°F "
        f"battery={p.get('batteryValue')}%",
        flush=True,
    )
    mq.on_dome = lambda d: print(
        f"[dome] status={d.get('globalStatus')} cookingState={d.get('cookingState')} "
        f"chamber={tenths_to_f(d.get('curTemperature')):.0f}°F "
        f"remain={d.get('curRemainingTime')}s",
        flush=True,
    )
    mq.on_connect = lambda rc: print(f"[mqtt] connected rc={rc}", file=sys.stderr)

    mq.start()
    try:
        time.sleep(seconds)
    finally:
        mq.stop()
