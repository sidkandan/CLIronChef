"""Typhur cloud HTTP API client.

Wraps the REST endpoints at api.iot.typhur.com (US) or api.iot.typhur.de (EU).
Handles auth, request signing, device list, cooking commands, status requests, and
MQTT cert provisioning.

See docs/reference/PROTOCOL.md for the wire-format details.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional

import requests

# Protocol constants required by Typhur cloud request signing. These are not user
# secrets and are not derived from user account data.
SIGN_CONSTANT = "7d02d81bd7f4483a9a0ac580f2b6ad44"
APP_ID = "ap206cba3069ed4a11"
APP_VERSION = "4200"

# Per-client identifier (any hex string; not user-secret)
APP_DEVICE_SN = hashlib.md5(b"cliron-chef-cli").hexdigest()

LANG = "en_US"

API_BASES = {
    "US": "https://api.iot.typhur.com",
    "EU": "https://api.iot.typhur.de",
}

START_CLIENT = "android"  # Server validates this enum; "android" or "ios" required


def _config_dir() -> Path:
    """Where to store credentials, tokens, and MQTT certs."""
    override = os.environ.get("CLIRON_CHEF_CONFIG_DIR")
    if override:
        d = Path(override).expanduser()
    else:
        d = Path.home() / ".cliron-chef"
    d.mkdir(mode=0o700, parents=True, exist_ok=True)
    return d


class TyphurAPIError(Exception):
    """Raised when an API call fails or returns a non-success code."""


class TyphurAPI:
    """HTTP API client for the Typhur cloud.

    Usage:
        >>> api = TyphurAPI.login("you@example.com", "password", region="US")
        >>> devices = api.list_devices()
        >>> result, cook_uuid = api.start_cook("AF04", "<deviceId>",
        ...     [{"cookingMode": 3, "setTemperature": 450, "setTime": 2400}])

    Or load from cached credentials:
        >>> api = TyphurAPI.from_cached_credentials()
    """

    def __init__(self, token: str, region: str = "US"):
        if region not in API_BASES:
            raise ValueError(f"Unknown region: {region}. Expected one of {list(API_BASES)}")
        self.token = token
        self.region = region
        self.base = API_BASES[region]

    # -- Auth ----------------------------------------------------------------

    @classmethod
    def login(cls, email: str, password: str, region: str = "US") -> TyphurAPI:
        """Login and return a new TyphurAPI instance with the resulting token."""
        if region not in API_BASES:
            raise ValueError(f"Unknown region: {region}")
        md5_pw = hashlib.md5(password.encode()).hexdigest()
        api = cls(token="none", region=region)  # unauthenticated bootstrap
        data = api.post(
            "/app/account/login",
            {"accountName": email, "accountPassword": md5_pw, "deviceInfo": "cliron-chef"},
        )
        token = data["token"]
        api.token = token
        # Cache locally
        (_config_dir() / "token").write_text(token)
        (_config_dir() / "credentials").write_text(
            json.dumps({"email": email, "password_md5": md5_pw, "region": region})
        )
        os.chmod(_config_dir() / "token", 0o600)
        os.chmod(_config_dir() / "credentials", 0o600)
        return api

    @classmethod
    def from_cached_credentials(cls) -> TyphurAPI:
        """Load token + region from ~/.cliron-chef/. Re-login if no cached creds."""
        cfg = _config_dir()
        token_file = cfg / "token"
        creds_file = cfg / "credentials"
        if token_file.exists() and creds_file.exists():
            creds = json.loads(creds_file.read_text())
            return cls(token=token_file.read_text().strip(), region=creds.get("region", "US"))
        # Fall back to env vars
        email = os.environ.get("TYPHUR_EMAIL")
        password = os.environ.get("TYPHUR_PASSWORD")
        region = os.environ.get("TYPHUR_REGION", "US")
        if email and password:
            return cls.login(email, password, region=region)
        raise TyphurAPIError(
            "No cached credentials and no TYPHUR_EMAIL/TYPHUR_PASSWORD env vars. "
            "Run `cliron-chef login` first."
        )

    # -- Request signing -----------------------------------------------------

    def _sign_headers(self, body: str) -> dict:
        nonce = uuid.uuid4().hex
        ts = str(int(time.time() * 1000))
        headers = [
            ("x-appId", APP_ID),
            ("x-appVersion", APP_VERSION),
            ("x-deviceSn", APP_DEVICE_SN),
            ("x-lang", LANG),
            ("x-nonce", nonce),
            ("x-region", self.region),
            ("x-timestamp", ts),
            ("x-token", self.token),
        ]
        parts = ";".join(f"{k}={v}" for k, v in headers)
        sign_input = f"{SIGN_CONSTANT}|{parts}|{body}"
        sign = hashlib.md5(sign_input.encode()).hexdigest()
        h = dict(headers)
        h["x-sign"] = sign
        h["Content-Type"] = "application/json"
        return h

    def post(self, path: str, body: dict, timeout: int = 20) -> dict:
        """POST a JSON body to the API; return the `data` field of the response."""
        body_str = json.dumps(body, separators=(",", ":"))
        headers = self._sign_headers(body_str)
        r = requests.post(f"{self.base}{path}", headers=headers, data=body_str, timeout=timeout)
        r.raise_for_status()
        out = r.json()
        if str(out.get("code")) not in ("0", "200"):
            raise TyphurAPIError(f"{path} returned: {out}")
        return out.get("data", out)

    # -- Devices --------------------------------------------------------------

    def list_devices(self) -> list:
        """List all bound devices for the authenticated account."""
        return self.post("/app/device/bind/list", {})

    def get_device(self, model: str, device_id: str) -> Optional[dict]:
        """Find a single device by model + ID. Returns None if not bound."""
        for d in self.list_devices():
            if d.get("deviceModel") == model and str(d.get("deviceId")) == str(device_id):
                return d
        return None

    def find_dome(self) -> Optional[dict]:
        """Find the first bound AF04 (Dome 2)."""
        for d in self.list_devices():
            if d.get("deviceModel") == "AF04":
                return d
        return None

    def find_probe(self) -> Optional[dict]:
        """Find the first bound WT01 (Sync ONE)."""
        for d in self.list_devices():
            if d.get("deviceModel") == "WT01":
                return d
        return None

    # -- MQTT cert provisioning ----------------------------------------------

    def get_mqtt_cert(self) -> dict:
        """Get the AWS IoT MQTT client cert.

        Returns: {"p12Url": ..., "p12Password": ..., "clientId": ...}
        """
        return self.post("/app/mqtt/cert/apply", {})

    def get_mqtt_endpoint(self) -> dict:
        """Get the AWS IoT MQTT broker endpoint config."""
        data = self.post("/app/dict/list", {"dictKeys": ["mqtt_conn_param"]})
        for entry in data if isinstance(data, list) else data.get("list", []):
            if entry.get("dictKey") == "mqtt_conn_param":
                val = entry["dictValue"]
                if isinstance(val, str):
                    val = json.loads(val)
                return val
        # Fallback (US default)
        return {
            "endpoint": "a2rac2pr1im2vr-ats.iot.us-west-2.amazonaws.com",
            "port": 8883,
        }

    def fetch_mqtt_files(self) -> tuple:
        """Download the P12 and extract cert + key.

        Returns: (cert_path, key_path, client_id) where paths are str.
        Caches at ~/.cliron-chef/client.{p12,crt,key}.
        """
        cert_info = self.get_mqtt_cert()
        cfg = _config_dir()
        p12_path = cfg / "client.p12"
        cert_path = cfg / "client.crt"
        key_path = cfg / "client.key"

        # Download P12
        response = requests.get(cert_info["p12Url"], timeout=20)
        response.raise_for_status()
        p12_path.write_bytes(response.content)
        os.chmod(p12_path, 0o600)

        # Extract cert + key with openssl (legacy flag for RC2-40 compat)
        with tempfile.NamedTemporaryFile("w", dir=cfg, delete=False) as pass_file:
            pass_file.write(cert_info["p12Password"])
            pass_path = Path(pass_file.name)
        os.chmod(pass_path, 0o600)
        try:
            subprocess.run(
                ["openssl", "pkcs12", "-legacy", "-in", str(p12_path),
                 "-out", str(cert_path), "-clcerts", "-nokeys",
                 "-password", f"file:{pass_path}"],
                check=True, capture_output=True,
            )
            subprocess.run(
                ["openssl", "pkcs12", "-legacy", "-in", str(p12_path),
                 "-out", str(key_path), "-nocerts", "-nodes",
                 "-password", f"file:{pass_path}"],
                check=True, capture_output=True,
            )
        finally:
            try:
                pass_path.unlink()
            except FileNotFoundError:
                pass
        os.chmod(cert_path, 0o600)
        os.chmod(key_path, 0o600)
        return str(cert_path), str(key_path), cert_info["clientId"]

    # -- Cooking commands ----------------------------------------------------

    def send_command(self, device_model: str, device_id: str, cmd_data: dict,
                     cmd_type: Optional[str] = None) -> dict:
        """Send a generic cmdType command. Use start_cook/stop_cook for common cases."""
        if cmd_type is None:
            cmd_type = f"{device_model}:cooking:action"
        body = {
            "cmdType": cmd_type,
            "deviceId": str(device_id),
            "cmdData": cmd_data,
        }
        return self.post("/app/command/send", body)

    def request_status(self, device_model: str, device_id: str) -> dict:
        """Force the device to emit a fresh status:report MQTT message."""
        return self.send_command(
            device_model,
            device_id,
            {"deviceId": str(device_id)},
            cmd_type="device:status:request",
        )

    def start_cook(self, device_model: str, device_id: str, stages: list,
                   cook_uuid: Optional[str] = None) -> tuple:
        """Configure (or hot-modify) a cook.

        stages: list of dicts with keys cookingMode, setTemperature, setTime.
                setTemperature is in WHOLE degrees F (will be *10 for wire format).
                setTime is in seconds.
        cook_uuid: pass an existing cookUuid to hot-modify; omit for a new cook.

        Returns: (response_dict, cook_uuid)
        """
        if cook_uuid is None:
            cook_uuid = uuid.uuid4().hex
        encoded = []
        for s in stages:
            es = dict(s)
            if "setTemperature" in es:
                es["setTemperature"] = int(es["setTemperature"]) * 10
            encoded.append(es)
        cmd_data = {
            "cookingAction": 1,
            "cookUuid": cook_uuid,
            "cookingStageNum": len(encoded),
            "setParams": encoded,
            "startClient": START_CLIENT,
            "cookingData": {
                "dataType": "preset",
                "dataId": str(stages[0].get("cookingMode", 1)),
                "dataName": "cliron-chef",
                "dataImgUrl": "",
            },
        }
        result = self.send_command(device_model, device_id, cmd_data)
        return result, cook_uuid

    def hot_modify(self, device_model: str, device_id: str, cook_uuid: str,
                   mode: int, temp_f: int, time_s: int = 2400) -> dict:
        """Hot-modify the active cook. Always single-stage; reasserts 2400s buffer."""
        result, _ = self.start_cook(
            device_model,
            device_id,
            [{"cookingMode": mode, "setTemperature": temp_f, "setTime": time_s}],
            cook_uuid=cook_uuid,
        )
        return result

    def stop_cook(self, device_model: str, device_id: str,
                  cook_uuid: Optional[str] = None) -> dict:
        """Send STOP (cookingAction=4). cook_uuid is optional — server tolerates any."""
        return self.send_command(
            device_model,
            device_id,
            {
                "cookingAction": 4,
                "cookUuid": cook_uuid or uuid.uuid4().hex,
                "startClient": START_CLIENT,
            },
        )
