#!/usr/bin/env python
import json
from http.client import HTTPSConnection
from typing import Any

API_HOST = "hardware.api.keil.arm.com"


class JsonGetter:
    _conn: HTTPSConnection

    def __init__(self, host: str) -> None:
        self._conn = HTTPSConnection(host)

    def get(self, path: str) -> dict[str, Any]:
        self._conn.request("GET", path)
        response = self._conn.getresponse()
        assert response.status == 200, f"Query to {path} returned {response.status}"
        return json.loads(response.read())


def make_absolute_link(path: str) -> str:
    return f"https://{API_HOST}{path}"


def get_composed_boards() -> list[dict[str, Any]]:
    hardware_getter = JsonGetter(API_HOST)

    boards: list[dict[str, Any]] = []

    next_page_path = "/boards/?embed"
    while next_page_path is not None:
        page_json = hardware_getter.get(next_page_path)
        for board in page_json["_embedded"]["item"]:
            boards.append(board)
        next_page_path = page_json["_links"].get("next", {}).get("href")

    composed_boards: list[dict[str, Any]] = []

    for board_json in boards:
        if board_json.get("detect_code") is not None:
            devices = []
            for device_link in board_json["_links"].get("device", []):
                device_json = hardware_getter.get(device_link["href"])
                devices.append(
                    {
                        "title": device_json["title"],
                        "source_pack_id": device_json["source_pack_id"],
                        "_links": {
                            "device": {
                                "href": make_absolute_link(
                                    device_json["_links"]["self"]["href"]
                                )
                            }
                        },
                    }
                )

            composed_boards.append(
                {
                    "title": board_json["title"],
                    "detect_code": board_json["detect_code"],
                    "devices": devices,
                    "_links": {
                        "board": {
                            "href": make_absolute_link(
                                board_json["_links"]["self"]["href"]
                            )
                        }
                    },
                }
            )

    return composed_boards


def app(environ, start_response):
    data = json.dumps(get_composed_boards()).encode("UTF-8")
    status = "200 OK"
    response_headers = [
        ("Content-type", "application/json"),
        ("Content-Length", str(len(data))),
    ]
    start_response(status, response_headers)
    return iter([data])


if __name__ == "__main__":
    print(json.dumps(get_composed_boards()))
