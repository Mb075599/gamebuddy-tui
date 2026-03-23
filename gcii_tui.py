#!/usr/bin/env python3
"""Minimal TUI for controlling an AVerMedia Game Capture HD II over HTTP.

This is based on endpoints recovered from the original GameMate Android app's
native library. The box exposes an `/eos/method/...` and `/eos/query/...`
interface plus SSDP discovery on 239.255.255.250:1900.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import shutil
import socket
import sys
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Iterable


DISCOVERY_ADDRESS = ("239.255.255.250", 1900)
DISCOVERY_REQUEST = (
    "M-SEARCH * HTTP/1.1\r\n"
    "HOST: 239.255.255.250:1900\r\n"
    'MAN: "ssdp:discover"\r\n'
    "MX: 1\r\n"
    "ST: upnp:rootdevice\r\n"
    "\r\n"
).encode("ascii")


def enable_virtual_terminal() -> None:
    if os.name != "nt":
        return
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)
    mode = ctypes.c_uint32()
    if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)


def wrap_block(text: str, width: int) -> list[str]:
    if width <= 1:
        return [text[: max(width, 0)]]
    lines: list[str] = []
    for raw_line in text.splitlines() or [""]:
        line = raw_line.rstrip()
        if not line:
            lines.append("")
            continue
        wrapped = textwrap.wrap(
            line,
            width=width,
            replace_whitespace=False,
            drop_whitespace=False,
        )
        lines.extend(wrapped or [""])
    return lines


def parse_http_headers(payload: bytes) -> dict[str, str]:
    text = payload.decode("utf-8", "ignore")
    headers: dict[str, str] = {}
    for line in text.split("\r\n")[1:]:
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return headers


def is_probably_gcii(headers: dict[str, str]) -> bool:
    haystack = " ".join(headers.values()).lower()
    return any(token in haystack for token in ("avermedia", "gamemate", "capture hd ii"))


def normalize_url_host_port(location: str | None, fallback_host: str) -> tuple[str, int]:
    if location:
        parsed = urllib.parse.urlsplit(location)
        if parsed.hostname:
            port = parsed.port
            if port is None:
                port = 443 if parsed.scheme == "https" else 80
            return parsed.hostname, port
    return fallback_host, 80


def decode_body(body: bytes) -> str:
    if not body:
        return ""
    for encoding in ("utf-8", "utf-16", "latin1"):
        try:
            return body.decode(encoding)
        except UnicodeDecodeError:
            continue
    return body.decode("utf-8", "ignore")


def pretty_payload(body: bytes) -> str:
    text = decode_body(body).strip()
    if not text:
        return "<empty response>"

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    if parsed is not None:
        return json.dumps(parsed, indent=2, sort_keys=True)

    if text.startswith("<"):
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            return text
        ET.indent(root)
        return ET.tostring(root, encoding="unicode")

    return text


@dataclass(slots=True)
class ResponseView:
    endpoint: str
    status: int | None
    body: str
    error: str | None = None


@dataclass(slots=True)
class DeviceTarget:
    host: str
    port: int
    location: str = ""
    server: str = ""
    usn: str = ""
    name: str = ""

    @property
    def label(self) -> str:
        bits = [f"{self.host}:{self.port}"]
        if self.name:
            bits.append(self.name)
        elif self.server:
            bits.append(self.server)
        return " | ".join(bits)


class GCIIClient:
    def __init__(self, host: str, port: int, timeout: float = 2.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def set_target(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def _url(self, category: str, endpoint: str, params: dict[str, str] | None = None) -> str:
        category = category.strip("/")
        endpoint = endpoint.strip("/")
        url = f"{self.base_url()}/eos/{category}/{endpoint}"
        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}?{query}"
        return url

    def request(
        self,
        category: str,
        endpoint: str,
        params: dict[str, str] | None = None,
        data: bytes | None = None,
    ) -> ResponseView:
        url = self._url(category, endpoint, params)
        req = urllib.request.Request(url, method="POST" if data is not None else "GET", data=data)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return ResponseView(
                    endpoint=url,
                    status=response.getcode(),
                    body=pretty_payload(response.read()),
                )
        except urllib.error.HTTPError as exc:
            payload = exc.read()
            return ResponseView(
                endpoint=url,
                status=exc.code,
                body=pretty_payload(payload),
                error=f"HTTP {exc.code}: {exc.reason}",
            )
        except urllib.error.URLError as exc:
            return ResponseView(endpoint=url, status=None, body="", error=str(exc.reason))
        except TimeoutError:
            return ResponseView(endpoint=url, status=None, body="", error="timed out")
        except OSError as exc:
            return ResponseView(endpoint=url, status=None, body="", error=str(exc))

    def method(self, endpoint: str, params: dict[str, str] | None = None) -> ResponseView:
        return self.request("method", endpoint, params=params)

    def query(self, endpoint: str, params: dict[str, str] | None = None) -> ResponseView:
        return self.request("query", endpoint, params=params)

    def probe(self, host: str, port: int) -> tuple[bool, str]:
        original = (self.host, self.port)
        try:
            self.set_target(host, port)
            for category, endpoint in (
                ("query", "status_get"),
                ("method", "get_device_name"),
            ):
                result = self.request(category, endpoint)
                if result.status and 200 <= result.status < 300:
                    return True, result.body[:200].replace("\n", " ")
            return False, ""
        finally:
            self.set_target(*original)

    def discover(self, timeout: float = 2.0) -> list[DeviceTarget]:
        found: dict[tuple[str, int], DeviceTarget] = {}
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            sock.settimeout(timeout)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.sendto(DISCOVERY_REQUEST, DISCOVERY_ADDRESS)
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                try:
                    payload, addr = sock.recvfrom(65535)
                except socket.timeout:
                    break
                headers = parse_http_headers(payload)
                location = headers.get("location", "")
                host, port = normalize_url_host_port(location, addr[0])
                key = (host, port)
                if key not in found:
                    found[key] = DeviceTarget(
                        host=host,
                        port=port,
                        location=location,
                        server=headers.get("server", ""),
                        usn=headers.get("usn", ""),
                    )
        finally:
            sock.close()

        verified: list[DeviceTarget] = []
        for device in found.values():
            good, preview = self.probe(device.host, device.port)
            if good or is_probably_gcii(
                {"server": device.server, "usn": device.usn, "location": device.location}
            ):
                if preview:
                    device.name = preview.splitlines()[0][:80]
                verified.append(device)
        verified.sort(key=lambda item: (item.host, item.port))
        return verified


class KeyReader:
    def __enter__(self) -> "KeyReader":
        if os.name == "nt":
            import msvcrt

            self._msvcrt = msvcrt
            return self

        import termios
        import tty

        self._termios = termios
        self._fd = sys.stdin.fileno()
        self._old = termios.tcgetattr(self._fd)
        tty.setcbreak(self._fd)
        return self

    def __exit__(self, *_: object) -> None:
        if os.name != "nt":
            self._termios.tcsetattr(self._fd, self._termios.TCSADRAIN, self._old)

    def read_key(self) -> str:
        if os.name == "nt":
            first = self._msvcrt.getwch()
            if first in ("\x00", "\xe0"):
                second = self._msvcrt.getwch()
                mapping = {"H": "UP", "P": "DOWN", "K": "LEFT", "M": "RIGHT", "S": "DELETE"}
                return mapping.get(second, second)
            if first == "\r":
                return "ENTER"
            if first == "\x1b":
                return "ESC"
            return first

        first = sys.stdin.read(1)
        if first == "\x1b":
            second = sys.stdin.read(1)
            if second != "[":
                return "ESC"
            third = sys.stdin.read(1)
            mapping = {"A": "UP", "B": "DOWN", "C": "RIGHT", "D": "LEFT"}
            return mapping.get(third, "ESC")
        if first in ("\r", "\n"):
            return "ENTER"
        return first


@dataclass
class AppState:
    client: GCIIClient
    discovered: list[DeviceTarget] = field(default_factory=list)
    last_response: str = "No request sent yet."
    status_line: str = "Ready."
    log_lines: list[str] = field(default_factory=list)
    running: bool = True

    def target_label(self) -> str:
        return f"{self.client.host}:{self.client.port}"

    def push_log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.log_lines.append(f"[{timestamp}] {message}")
        self.log_lines = self.log_lines[-10:]

    def set_response(self, view: ResponseView) -> None:
        lines = [f"Endpoint: {view.endpoint}"]
        if view.status is not None:
            lines.append(f"HTTP: {view.status}")
        if view.error:
            lines.append(f"Error: {view.error}")
        lines.append("")
        lines.append(view.body or "<empty response>")
        self.last_response = "\n".join(lines)


class GCIITUI:
    def __init__(self, host: str, port: int) -> None:
        self.state = AppState(client=GCIIClient(host, port))

    def run(self) -> None:
        enable_virtual_terminal()
        print("\x1b[?25l", end="", flush=True)
        try:
            with KeyReader() as reader:
                while self.state.running:
                    self.render()
                    key = reader.read_key()
                    self.handle_key(key)
        finally:
            print("\x1b[2J\x1b[H\x1b[?25h", end="", flush=True)

    def render(self) -> None:
        columns, rows = shutil.get_terminal_size((100, 34))
        body_width = max(columns - 4, 20)
        response_height = max(rows - 22, 8)

        header = [
            "GCII Control TUI",
            f"Target: {self.state.target_label()}",
            f"Status: {self.state.status_line}",
            "",
            "Keys: d discover | h host | t port | n name | q status | w whole-info | i input-source",
            "      r start-record | p pause-record | x stop-record | s snapshot | k keep-alive",
            "      arrows remote | enter/o ok | m menu | b back | 1 2 3 -> F1/F2/F3",
            "      / custom endpoint | [ ] cycle discovered | esc exit",
            "",
            "Discovered Devices:",
        ]

        discovered = ["  <none>"]
        if self.state.discovered:
            discovered = []
            current = self.state.target_label()
            for device in self.state.discovered[:6]:
                prefix = ">" if f"{device.host}:{device.port}" == current else " "
                discovered.append(f"{prefix} {device.label}")

        response_lines = wrap_block(self.state.last_response, body_width)[:response_height]
        log_lines = self.state.log_lines[-6:] or ["<no log entries>"]

        screen: list[str] = []
        screen.extend(header)
        screen.extend(discovered)
        screen.append("")
        screen.append("Last Response:")
        screen.extend(response_lines)
        screen.append("")
        screen.append("Log:")
        screen.extend(wrap_block("\n".join(log_lines), body_width))

        clipped = screen[:rows]
        print("\x1b[2J\x1b[H" + "\n".join(clipped), end="", flush=True)

    def handle_key(self, key: str) -> None:
        handlers = {
            "d": self.discover,
            "h": self.prompt_host,
            "t": self.prompt_port,
            "n": lambda: self.send_query("method", "get_device_name"),
            "q": lambda: self.send_query("query", "status_get"),
            "w": lambda: self.send_query("query", "get_box_whole_infos"),
            "i": lambda: self.send_query("query", "input_source_type_get"),
            "r": lambda: self.send_query("method", "start_record"),
            "p": lambda: self.send_query("method", "pause_record"),
            "x": lambda: self.send_query("method", "stop_record"),
            "s": lambda: self.send_query("method", "take_image"),
            "k": lambda: self.send_query("method", "keep_alive"),
            "UP": lambda: self.send_query("method", "up"),
            "DOWN": lambda: self.send_query("method", "down"),
            "LEFT": lambda: self.send_query("method", "left"),
            "RIGHT": lambda: self.send_query("method", "right"),
            "ENTER": lambda: self.send_query("method", "ok"),
            "o": lambda: self.send_query("method", "ok"),
            "m": lambda: self.send_query("method", "menu"),
            "b": lambda: self.send_query("method", "back"),
            "1": lambda: self.send_query("method", "f1"),
            "2": lambda: self.send_query("method", "f2"),
            "3": lambda: self.send_query("method", "f3"),
            "/": self.prompt_custom_endpoint,
            "[": self.select_previous_device,
            "]": self.select_next_device,
            "ESC": self.stop,
        }
        action = handlers.get(key)
        if action:
            action()

    def stop(self) -> None:
        self.state.running = False

    def send_query(
        self,
        category: str,
        endpoint: str,
        params: dict[str, str] | None = None,
    ) -> None:
        self.state.status_line = f"Sending {category}/{endpoint}..."
        self.render()
        if category == "query":
            result = self.state.client.query(endpoint, params=params)
        else:
            result = self.state.client.method(endpoint, params=params)
        self.state.set_response(result)
        if result.error:
            self.state.status_line = f"{category}/{endpoint} failed"
            self.state.push_log(f"{category}/{endpoint} -> {result.error}")
        else:
            self.state.status_line = f"{category}/{endpoint} OK"
            self.state.push_log(f"{category}/{endpoint} -> HTTP {result.status}")

    def discover(self) -> None:
        self.state.status_line = "Discovering devices with SSDP..."
        self.render()
        found = self.state.client.discover()
        self.state.discovered = found
        if found:
            self.state.client.set_target(found[0].host, found[0].port)
            self.state.status_line = f"Found {len(found)} device(s); selected {found[0].host}:{found[0].port}"
            self.state.push_log(f"discovery found {len(found)} device(s)")
        else:
            self.state.status_line = "No GCII devices discovered"
            self.state.push_log("discovery found no devices")

    def prompt(self, label: str, default: str = "") -> str | None:
        print("\x1b[2J\x1b[H\x1b[?25h", end="", flush=True)
        try:
            value = input(f"{label} [{default}]: ").strip()
        except EOFError:
            value = ""
        finally:
            print("\x1b[?25l", end="", flush=True)
        if not value:
            return default or None
        return value

    def prompt_host(self) -> None:
        host = self.prompt("Host", self.state.client.host)
        if not host:
            return
        self.state.client.set_target(host, self.state.client.port)
        self.state.status_line = f"Target host set to {host}"
        self.state.push_log(f"host -> {host}")

    def prompt_port(self) -> None:
        raw = self.prompt("Port", str(self.state.client.port))
        if not raw:
            return
        try:
            port = int(raw)
        except ValueError:
            self.state.status_line = f"Invalid port: {raw}"
            self.state.push_log(f"invalid port {raw}")
            return
        self.state.client.set_target(self.state.client.host, port)
        self.state.status_line = f"Target port set to {port}"
        self.state.push_log(f"port -> {port}")

    def prompt_custom_endpoint(self) -> None:
        raw = self.prompt("Endpoint (e.g. query/status_get or method/pincode_gen)", "query/status_get")
        if not raw:
            return
        raw = raw.strip().strip("/")
        parts = raw.split("/", 1)
        if len(parts) != 2 or parts[0] not in {"method", "query"}:
            self.state.status_line = "Custom endpoint must look like method/name or query/name"
            self.state.push_log(f"invalid custom endpoint {raw}")
            return
        params_raw = self.prompt("Query params", "")
        params: dict[str, str] | None = None
        if params_raw:
            parsed = urllib.parse.parse_qs(params_raw, keep_blank_values=True)
            params = {key: values[-1] for key, values in parsed.items()}
        self.send_query(parts[0], parts[1], params=params)

    def select_previous_device(self) -> None:
        self._cycle_device(-1)

    def select_next_device(self) -> None:
        self._cycle_device(1)

    def _cycle_device(self, delta: int) -> None:
        if not self.state.discovered:
            self.state.status_line = "No discovered devices to select"
            return
        current = self.state.target_label()
        labels = [f"{device.host}:{device.port}" for device in self.state.discovered]
        try:
            index = labels.index(current)
        except ValueError:
            index = 0
        new_device = self.state.discovered[(index + delta) % len(self.state.discovered)]
        self.state.client.set_target(new_device.host, new_device.port)
        self.state.status_line = f"Selected {new_device.host}:{new_device.port}"
        self.state.push_log(f"target -> {new_device.host}:{new_device.port}")


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple TUI for the AVerMedia Game Capture HD II")
    parser.add_argument("--host", default="192.168.1.1", help="Target host or IP")
    parser.add_argument("--port", default=80, type=int, help="Target HTTP port")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    try:
        GCIITUI(args.host, args.port).run()
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
