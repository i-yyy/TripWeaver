"""Structured wrapper around the AMap HTTP APIs with optional MCP fallback."""

from __future__ import annotations

import atexit
import asyncio
import json
import logging
import shutil
import sys
import threading
import urllib.parse
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, TypeVar

import httpx

try:
    from hello_agents.tools import MCPTool
except Exception:  # pragma: no cover - compatibility path
    try:
        from hello_agents.tools.builtin.protocol_tools import MCPTool  # type: ignore
    except Exception:  # pragma: no cover - tool unavailable
        MCPTool = None  # type: ignore

try:
    from fastmcp import Client as FastMCPClient
    from fastmcp.client.transports import StdioTransport
except Exception:  # pragma: no cover - optional dependency
    FastMCPClient = None  # type: ignore
    StdioTransport = None  # type: ignore

from ..config import get_settings
from ..models.schemas import DayRouteInfo, DayRouteStopRequest, Location, POIInfo, RouteMarker, RouteSegment, WeatherInfo

logger = logging.getLogger(__name__)

AMAP_POI_TEXT_URL = "https://restapi.amap.com/v3/place/text"
AMAP_POI_DETAIL_URL = "https://restapi.amap.com/v3/place/detail"
AMAP_WEATHER_URL = "https://restapi.amap.com/v3/weather/weatherInfo"
AMAP_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"
AMAP_WALKING_URL = "https://restapi.amap.com/v3/direction/walking"
AMAP_DRIVING_URL = "https://restapi.amap.com/v3/direction/driving"
AMAP_TRANSIT_URL = "https://restapi.amap.com/v3/direction/transit/integrated"

_amap_mcp_tool: Any = None
_amap_service: Optional["AmapService"] = None
T = TypeVar("T")


class PersistentMCPTool:
    """Thread-backed persistent MCP client with a synchronous run interface."""

    def __init__(self, server_command: List[str], env: Dict[str, str]) -> None:
        if FastMCPClient is None or StdioTransport is None:
            raise RuntimeError("fastmcp client transport is unavailable")

        self.server_command = list(server_command)
        self.env = dict(env)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._client: Any = None
        self._startup_error: BaseException | None = None
        self._ready = threading.Event()
        self._close_lock = threading.Lock()
        self._closing = False
        self._shutdown_event: asyncio.Event | None = None
        self._start()
        atexit.register(self.close)

    def _start(self) -> None:
        self._thread = threading.Thread(target=self._thread_main, name="amap-mcp-client", daemon=True)
        self._thread.start()
        self._ready.wait(timeout=20)
        if self._startup_error is not None:
            raise RuntimeError("Failed to start persistent AMap MCP client") from self._startup_error
        if self._loop is None or self._client is None:
            raise RuntimeError("Persistent AMap MCP client did not initialize")

    def _thread_main(self) -> None:
        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        self._shutdown_event = asyncio.Event()
        loop.create_task(self._run_client())
        try:
            loop.run_forever()
        finally:
            pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()

    async def _run_client(self) -> None:
        client = None
        try:
            transport = StdioTransport(
                command=self.server_command[0],
                args=self.server_command[1:],
                env=self.env or None,
                keep_alive=True,
            )
            client = FastMCPClient(transport, name="amap-persistent")
            await client.__aenter__()
            self._client = client
        except BaseException as exc:
            self._startup_error = exc
        finally:
            self._ready.set()

        if client is None or self._shutdown_event is None:
            if self._loop is not None:
                self._loop.call_soon(self._loop.stop)
            return

        try:
            await self._shutdown_event.wait()
        finally:
            try:
                await client.__aexit__(None, None, None)
            except Exception:
                logger.debug("Persistent AMap MCP client shutdown raised", exc_info=True)
            finally:
                self._client = None
                if self._loop is not None:
                    self._loop.call_soon(self._loop.stop)

    def _submit(self, coro: Any) -> Any:
        if self._loop is None:
            raise RuntimeError("Persistent AMap MCP loop is unavailable")
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def run(self, parameters: Dict[str, Any]) -> Any:
        action = str(parameters.get("action") or "").lower()
        if action == "call_tool":
            tool_name = str(parameters.get("tool_name") or "").strip()
            if not tool_name:
                raise ValueError("tool_name is required for call_tool")
            arguments = parameters.get("arguments", {})
            return self._submit(self._call_tool(tool_name, arguments))
        if action == "list_tools":
            return self._submit(self._list_tools())
        raise ValueError(f"Unsupported MCP action: {action}")

    async def _list_tools(self) -> List[Dict[str, Any]]:
        if self._client is None:
            raise RuntimeError("Persistent AMap MCP client is not connected")
        tools = await self._client.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": getattr(tool, "inputSchema", {}),
            }
            for tool in tools
        ]

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if self._client is None:
            raise RuntimeError("Persistent AMap MCP client is not connected")
        result = await self._client.call_tool(tool_name, arguments or {})
        return self._normalize_result(result)

    @staticmethod
    def _normalize_result(result: Any) -> Any:
        structured = getattr(result, "structured_content", None)
        if structured is not None:
            return structured

        data = getattr(result, "data", None)
        if data is not None:
            if hasattr(data, "model_dump"):
                return data.model_dump()
            return data

        content = getattr(result, "content", None)
        if isinstance(content, list) and content:
            if len(content) == 1:
                item = content[0]
                if hasattr(item, "text"):
                    return item.text
                if hasattr(item, "data"):
                    return item.data
            normalized: List[Any] = []
            for item in content:
                if hasattr(item, "text"):
                    normalized.append(item.text)
                elif hasattr(item, "data"):
                    normalized.append(item.data)
                else:
                    normalized.append(str(item))
            return normalized
        return None

    def close(self) -> None:
        with self._close_lock:
            if self._closing:
                return
            self._closing = True

        try:
            if self._loop is not None and self._shutdown_event is not None:
                self._loop.call_soon_threadsafe(self._shutdown_event.set)
            if self._thread is not None and self._thread.is_alive():
                self._thread.join(timeout=5)
        finally:
            self._closing = False


def _resolve_amap_server_command() -> List[str]:
    """Resolve uvx from the active environment before falling back to PATH."""
    uvx_path = shutil.which("uvx")
    if uvx_path:
        return [uvx_path, "amap-mcp-server"]

    python_dir = Path(sys.executable).resolve().parent
    candidates = [
        python_dir / "Scripts" / "uvx.exe",
        Path(sys.prefix) / "Scripts" / "uvx.exe",
        python_dir / "uvx.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return [str(candidate), "amap-mcp-server"]

    return ["uvx", "amap-mcp-server"]


def get_amap_mcp_tool() -> Any:
    """Return the singleton MCP tool instance."""
    global _amap_mcp_tool

    if _amap_mcp_tool is None:
        settings = get_settings()
        server_command = _resolve_amap_server_command()
        env = {"AMAP_MAPS_API_KEY": settings.amap_api_key}

        if not settings.amap_api_key:
            raise ValueError("AMAP_API_KEY is not configured")

        if FastMCPClient is not None and StdioTransport is not None:
            try:
                _amap_mcp_tool = PersistentMCPTool(server_command=server_command, env=env)
                logger.info("AMap persistent MCP client initialized")
            except Exception:
                logger.exception("Persistent AMap MCP client init failed; falling back to MCPTool")

        if _amap_mcp_tool is None:
            if MCPTool is None:
                raise RuntimeError("Current hello-agents build does not expose MCPTool")
            _amap_mcp_tool = MCPTool(
                name="amap",
                description="AMap service with POI, route and weather capabilities",
                server_command=server_command,
                env=env,
                auto_expand=True,
            )
            logger.info("AMap MCP tool initialized")

    return _amap_mcp_tool


class AmapService:
    """Service layer that standardizes AMap tool outputs."""

    def __init__(self, mcp_tool: Any | None = None) -> None:
        settings = get_settings()
        provider = str(settings.amap_provider or "http").strip().lower()
        if provider not in {"http", "mcp", "hybrid"}:
            logger.warning("Invalid AMAP_PROVIDER=%s; defaulting to http", provider)
            provider = "http"

        self.provider = provider
        self.api_key = settings.amap_api_key.strip()
        self.mcp_tool = mcp_tool
        self.http_enabled = provider in {"http", "hybrid"} and bool(self.api_key)
        self.mcp_enabled = mcp_tool is not None or provider in {"mcp", "hybrid"}
        self._http_client = (
            httpx.Client(timeout=float(settings.amap_http_timeout)) if self.http_enabled else None
        )
        self._mcp_tool_lock = threading.Lock()
        self._poi_detail_cache: Dict[str, Dict[str, Any]] = {}
        self._poi_detail_cache_lock = threading.Lock()
        self._poi_search_cache: Dict[tuple[str, str, bool], List[POIInfo]] = {}
        self._poi_search_cache_lock = threading.Lock()
        self._weather_cache: Dict[str, List[WeatherInfo]] = {}
        self._weather_cache_lock = threading.Lock()

    def list_tools(self) -> List[str]:
        return [
            "maps_text_search",
            "maps_weather",
            "maps_direction_walking_by_address",
            "maps_direction_driving_by_address",
            "maps_direction_transit_integrated_by_address",
            "maps_geo",
            "maps_search_detail",
        ]

    def health_status(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "http_enabled": self.http_enabled,
            "mcp_enabled": self.mcp_enabled,
            "amap_key_configured": bool(self.api_key),
            "mcp_connected": self.mcp_tool is not None,
        }

    def build_static_map_url(
        self,
        locations: Sequence[Location],
        labels: Optional[Sequence[str]] = None,
        zoom: int = 12,
        size: str = "750*420",
    ) -> Optional[str]:
        if not self.api_key or not locations:
            return None

        label_values = list(labels or [])
        marker_specs: List[str] = []
        for index, location in enumerate(locations):
            label = label_values[index] if index < len(label_values) else chr(65 + min(index, 25))
            marker_specs.append(f"mid,0xFF6B35,{label}:{location.longitude},{location.latitude}")

        params = {
            "key": self.api_key,
            "zoom": str(zoom),
            "size": size,
            "scale": "2",
            "markers": "|".join(marker_specs),
        }
        return "https://restapi.amap.com/v3/staticmap?" + urllib.parse.urlencode(params)

    def get_poi_photo_urls(self, poi_id: str) -> List[str]:
        normalized = str(poi_id or "").strip()
        if not normalized:
            return []
        detail = self.get_poi_detail(normalized)
        return self.extract_photo_urls(detail)

    @classmethod
    def extract_photo_urls(cls, detail: Dict[str, Any]) -> List[str]:
        if not isinstance(detail, dict):
            return []

        normalized: List[str] = []
        seen: set[str] = set()

        def _append(url: Any) -> None:
            if not url:
                return
            text = str(url).strip()
            if not text or text in seen:
                return
            seen.add(text)
            normalized.append(text)

        photos = detail.get("photos")
        if isinstance(photos, list):
            for item in photos:
                if isinstance(item, dict):
                    _append(item.get("url") or item.get("image") or item.get("src"))
                else:
                    _append(item)

        photo = detail.get("photo")
        if isinstance(photo, dict):
            _append(photo.get("url") or photo.get("image") or photo.get("src"))
        else:
            _append(photo)

        images = detail.get("images")
        if isinstance(images, list):
            for item in images:
                if isinstance(item, dict):
                    _append(item.get("url") or item.get("image") or item.get("src"))
                else:
                    _append(item)

        return normalized

    def build_day_route(
        self,
        city: str,
        route_type: str,
        hotel: Optional[DayRouteStopRequest],
        attractions: Sequence[DayRouteStopRequest],
    ) -> DayRouteInfo:
        normalized_route_type = str(route_type or "walking").strip().lower() or "walking"
        city_name = str(city or "").strip()

        hotel_marker = self._normalize_day_route_stop(hotel, city_name, label="H", kind="hotel")
        attraction_markers = [
            marker
            for index, stop in enumerate(attractions, start=1)
            if (marker := self._normalize_day_route_stop(stop, city_name, label=str(index), kind="attraction")) is not None
        ]

        markers: List[RouteMarker] = []
        if hotel_marker is not None:
            markers.append(hotel_marker)
        markers.extend(attraction_markers)

        ordered_stops: List[RouteMarker] = []
        if hotel_marker is not None:
            ordered_stops.append(hotel_marker)
        ordered_stops.extend(attraction_markers)
        if hotel_marker is not None and attraction_markers:
            ordered_stops.append(hotel_marker.model_copy())

        segments: List[RouteSegment] = []
        total_distance = 0.0
        total_duration = 0
        for start, end in zip(ordered_stops, ordered_stops[1:]):
            segment = self._build_day_route_segment(start, end, city_name, normalized_route_type)
            segments.append(segment)
            total_distance += float(segment.distance or 0.0)
            total_duration += int(segment.duration or 0)

        fallback_static_map_url = self.build_static_map_url(
            [marker.location for marker in markers],
            labels=[marker.label for marker in markers],
        )

        return DayRouteInfo(
            route_type=normalized_route_type,
            summary=self._build_day_route_summary(ordered_stops, normalized_route_type, total_distance, total_duration),
            distance=total_distance,
            duration=total_duration,
            markers=markers,
            segments=segments,
            fallback_static_map_url=fallback_static_map_url,
        )

    @staticmethod
    def _runtime_trace(message: str) -> None:
        print(f"[AMAP] {message}", flush=True)

    def _trace_poi_results(self, query_label: str, pois: Sequence[POIInfo]) -> None:
        self._runtime_trace(f"POI results -> {query_label} count={len(pois)}")
        for index, poi in enumerate(pois, start=1):
            self._runtime_trace(
                "  "
                + f"{index}. name={poi.name} | type={poi.type or '-'} | "
                + f"address={poi.address or '-'} | "
                + f"location={poi.location.longitude},{poi.location.latitude}"
            )

    def _trace_weather_results(self, city: str, weather_info: Sequence[WeatherInfo]) -> None:
        self._runtime_trace(f"Weather results -> city={city} count={len(weather_info)}")
        for index, item in enumerate(weather_info, start=1):
            self._runtime_trace(
                "  "
                + f"{index}. date={item.date} | day={item.day_weather} {item.day_temp}C | "
                + f"night={item.night_weather} {item.night_temp}C | "
                + f"wind={item.wind_direction} {item.wind_power}"
            )

    def _trace_geocode_result(self, address: str, city: Optional[str], location: Optional[Location]) -> None:
        if location is None:
            self._runtime_trace(f"Geocode result -> address={address} city={city or '-'} result=None")
            return
        self._runtime_trace(
            f"Geocode result -> address={address} city={city or '-'} "
            f"location={location.longitude},{location.latitude}"
        )

    def _trace_route_result(
        self,
        route_type: str,
        origin_address: str,
        destination_address: str,
        route: Dict[str, Any],
    ) -> None:
        self._runtime_trace(
            "Route result -> "
            + f"type={route_type} | origin={origin_address} | destination={destination_address} | "
            + f"distance={route.get('distance')} | duration={route.get('duration')} | "
            + f"description={route.get('description')}"
        )

    def _trace_poi_detail_result(self, poi_id: str, detail: Dict[str, Any]) -> None:
        self._runtime_trace(
            "POI detail -> "
            + f"id={poi_id} | name={detail.get('name', '')} | "
            + f"type={detail.get('type', '')} | address={detail.get('address', '')} | "
            + f"location={detail.get('location', '')}"
        )

    def search_poi(self, keywords: str, city: str, citylimit: bool = True) -> List[POIInfo]:
        cache_key = (keywords.strip(), city.strip(), citylimit)
        with self._poi_search_cache_lock:
            cached = self._poi_search_cache.get(cache_key)
        if cached is not None:
            return [item.model_copy(deep=True) for item in cached]

        result = self._run_with_optional_mcp_fallback(
            operation_name="search_poi",
            http_runner=lambda: self._search_poi_via_http(*cache_key),
            mcp_runner=lambda: self._search_poi_via_mcp(*cache_key),
        )
        with self._poi_search_cache_lock:
            self._poi_search_cache[cache_key] = [item.model_copy(deep=True) for item in result]
        self._trace_poi_results(f"keywords={keywords} city={city}", result)
        logger.info("AMap search_poi keywords=%s city=%s results=%s", keywords, city, len(result))
        return result

    def get_weather(self, city: str) -> List[WeatherInfo]:
        cache_key = city.strip()
        with self._weather_cache_lock:
            cached = self._weather_cache.get(cache_key)
        if cached is not None:
            return [item.model_copy(deep=True) for item in cached]

        result = self._run_with_optional_mcp_fallback(
            operation_name="get_weather",
            http_runner=lambda: self._get_weather_via_http(cache_key),
            mcp_runner=lambda: self._get_weather_via_mcp(cache_key),
        )
        with self._weather_cache_lock:
            self._weather_cache[cache_key] = [item.model_copy(deep=True) for item in result]
        self._trace_weather_results(city, result)
        logger.info("AMap get_weather city=%s forecast_days=%s", city, len(result))
        return result

    def plan_route(
        self,
        origin_address: str,
        destination_address: str,
        origin_city: Optional[str] = None,
        destination_city: Optional[str] = None,
        route_type: str = "walking",
    ) -> Dict[str, Any]:
        normalized_route_type = str(route_type or "walking").strip().lower() or "walking"
        result = self._run_with_optional_mcp_fallback(
            operation_name=f"plan_route[{normalized_route_type}]",
            http_runner=lambda: self._plan_route_via_http(
                origin_address=origin_address,
                destination_address=destination_address,
                origin_city=origin_city,
                destination_city=destination_city,
                route_type=normalized_route_type,
            ),
            mcp_runner=lambda: self._plan_route_via_mcp(
                origin_address=origin_address,
                destination_address=destination_address,
                origin_city=origin_city,
                destination_city=destination_city,
                route_type=normalized_route_type,
            ),
        )
        self._trace_route_result(normalized_route_type, origin_address, destination_address, result)
        return result

    def geocode(self, address: str, city: Optional[str] = None) -> Optional[Location]:
        result = self._run_with_optional_mcp_fallback(
            operation_name="geocode",
            http_runner=lambda: self._geocode_via_http(address, city),
            mcp_runner=lambda: self._geocode_via_mcp(address, city),
        )
        self._trace_geocode_result(address, city, result)
        return result

    def geocode_city_http(self, city: str) -> Optional[Location]:
        normalized_city = city.strip()
        if not normalized_city:
            return None

        candidates = [normalized_city]
        if normalized_city[-1] not in {"市", "区", "县", "州", "盟", "旗"}:
            candidates.append(f"{normalized_city}市")

        last_result: Optional[Location] = None
        last_error: Exception | None = None
        for candidate in candidates:
            try:
                result = self._geocode_via_http(candidate, candidate)
                self._trace_geocode_result(candidate, candidate, result)
                if result is not None:
                    return result
                last_result = result
            except Exception as exc:
                last_error = exc
                logger.warning("AMap city geocode failed for candidate=%s: %s", candidate, exc)
        if last_error is not None:
            raise last_error
        return last_result

    def get_poi_detail(self, poi_id: str) -> Dict[str, Any]:
        cache_key = poi_id.strip()
        with self._poi_detail_cache_lock:
            cached = self._poi_detail_cache.get(cache_key)
        if cached is not None:
            return dict(cached)

        detail = self._run_with_optional_mcp_fallback(
            operation_name="get_poi_detail",
            http_runner=lambda: self._get_poi_detail_via_http(cache_key),
            mcp_runner=lambda: self._get_poi_detail_via_mcp(cache_key),
        )
        with self._poi_detail_cache_lock:
            self._poi_detail_cache[cache_key] = dict(detail)
        self._trace_poi_detail_result(cache_key, detail)
        return detail

    def _run_with_optional_mcp_fallback(
        self,
        operation_name: str,
        http_runner: Callable[[], T],
        mcp_runner: Callable[[], T],
    ) -> T:
        if self.http_enabled:
            try:
                return http_runner()
            except Exception as exc:
                if not self.mcp_enabled:
                    self._runtime_trace(f"{operation_name} failed via HTTP: {exc}")
                    raise RuntimeError(f"AMap {operation_name} failed via HTTP: {exc}") from exc
                self._runtime_trace(f"{operation_name} failed via HTTP, fallback to MCP: {exc}")
                logger.warning("AMap %s failed via HTTP; falling back to MCP: %s", operation_name, exc)

        if self.mcp_enabled:
            return mcp_runner()

        if not self.api_key:
            raise RuntimeError(f"AMap {operation_name} is unavailable because AMAP_API_KEY is missing")
        raise RuntimeError(
            f"AMap {operation_name} is unavailable because provider={self.provider} has no usable client"
        )

    def _normalize_search_poi(self, item: Any) -> Optional[POIInfo]:
        normalized = self._normalize_poi(item)
        if not isinstance(item, dict):
            return normalized

        requires_detail = not item.get("location") or not item.get("type")
        if normalized is not None and not requires_detail:
            return normalized

        poi_id = str(item.get("id") or item.get("poi_id") or "").strip()
        if not poi_id:
            return normalized

        try:
            detail = self.get_poi_detail(poi_id)
        except Exception as exc:  # pragma: no cover - external dependency
            logger.debug("AMap detail hydration failed poi_id=%s error=%s", poi_id, exc)
            return normalized

        if not isinstance(detail, dict):
            return normalized

        merged = dict(item)
        merged.update(detail)
        return self._normalize_poi(merged)

    def _ensure_mcp_tool(self) -> Any:
        if self.mcp_tool is None:
            with self._mcp_tool_lock:
                if self.mcp_tool is None:
                    self.mcp_tool = get_amap_mcp_tool()
        return self.mcp_tool

    def _search_poi_via_http(self, keywords: str, city: str, citylimit: bool) -> List[POIInfo]:
        payload = self._http_get_json(
            AMAP_POI_TEXT_URL,
            {
                "keywords": keywords,
                "city": city,
                "citylimit": "true" if citylimit else "false",
                "offset": 20,
                "page": 1,
                "extensions": "all",
            },
        )
        pois_raw = payload.get("pois", [])
        if not isinstance(pois_raw, list):
            return []
        results = [self._normalize_poi(item) for item in pois_raw]
        return [item for item in results if item is not None]

    def _search_poi_via_mcp(self, keywords: str, city: str, citylimit: bool) -> List[POIInfo]:
        payload = self._call_tool(
            tool_name="maps_text_search",
            arguments={
                "keywords": keywords.strip(),
                "city": city.strip(),
                "citylimit": str(citylimit).lower(),
            },
            preferred_keys=("pois",),
        )
        pois_raw = payload.get("pois", [])
        if not isinstance(pois_raw, list):
            logger.warning("AMap text search returned non-list pois payload")
            return []
        results = [self._normalize_search_poi(item) for item in pois_raw]
        return [item for item in results if item is not None]

    def _get_weather_via_http(self, city: str) -> List[WeatherInfo]:
        payload = self._http_get_json(
            AMAP_WEATHER_URL,
            {
                "city": city,
                "extensions": "all",
            },
        )
        forecasts = payload.get("forecasts", [])
        if isinstance(forecasts, list) and forecasts:
            casts = forecasts[0].get("casts", []) if isinstance(forecasts[0], dict) else []
            if isinstance(casts, list):
                result = [self._normalize_forecast(item) for item in casts]
                return [item for item in result if item is not None]

        lives = payload.get("lives", [])
        if isinstance(lives, list) and lives:
            live = self._normalize_live_weather(lives[0])
            if live is not None:
                return [live]
        return []

    def _get_weather_via_mcp(self, city: str) -> List[WeatherInfo]:
        payload = self._call_tool(
            tool_name="maps_weather",
            arguments={"city": city.strip()},
            preferred_keys=("forecasts", "lives"),
        )

        forecasts = payload.get("forecasts")
        if isinstance(forecasts, list) and forecasts:
            if isinstance(forecasts[0], dict) and isinstance(forecasts[0].get("casts"), list):
                casts = forecasts[0].get("casts", [])
                result = [self._normalize_forecast(item) for item in casts]
                return [item for item in result if item is not None]

            result = [self._normalize_forecast(item) for item in forecasts]
            filtered = [item for item in result if item is not None]
            if filtered:
                return filtered

        lives = payload.get("lives", [])
        if isinstance(lives, list) and lives:
            live = self._normalize_live_weather(lives[0])
            if live is not None:
                return [live]

        logger.warning("AMap get_weather city=%s returned no structured weather", city)
        return []

    def _geocode_via_http(self, address: str, city: Optional[str] = None) -> Optional[Location]:
        params: Dict[str, Any] = {"address": address.strip()}
        if city:
            params["city"] = city.strip()
        payload = self._http_get_json(AMAP_GEOCODE_URL, params)
        geocodes = payload.get("geocodes", [])
        if not isinstance(geocodes, list) or not geocodes:
            logger.warning("AMap geocode returned no results for address=%s", address)
            return None
        return self._parse_location(geocodes[0].get("location"))

    def _geocode_via_mcp(self, address: str, city: Optional[str] = None) -> Optional[Location]:
        arguments: Dict[str, Any] = {"address": address.strip()}
        if city:
            arguments["city"] = city.strip()

        payload = self._call_tool(tool_name="maps_geo", arguments=arguments, preferred_keys=("geocodes",))
        geocodes = payload.get("geocodes", [])
        if not isinstance(geocodes, list) or not geocodes:
            logger.warning("AMap geocode returned no results for address=%s", address)
            return None
        return self._parse_location(geocodes[0].get("location"))

    def _plan_route_via_http(
        self,
        origin_address: str,
        destination_address: str,
        origin_city: Optional[str],
        destination_city: Optional[str],
        route_type: str,
    ) -> Dict[str, Any]:
        origin = self._geocode_via_http(origin_address, origin_city)
        destination = self._geocode_via_http(destination_address, destination_city)
        if origin is None or destination is None:
            raise ValueError("Failed to geocode route endpoints")
        payload = self._route_payload_via_http_from_locations(
            origin=origin,
            destination=destination,
            city=(origin_city or destination_city or "").strip(),
            route_type=route_type,
            detailed=False,
        )
        return self._normalize_route_payload(payload, "walking" if route_type == "walking" else route_type)

    def _plan_route_via_mcp(
        self,
        origin_address: str,
        destination_address: str,
        origin_city: Optional[str],
        destination_city: Optional[str],
        route_type: str,
    ) -> Dict[str, Any]:
        tool_map = {
            "walking": "maps_direction_walking_by_address",
            "driving": "maps_direction_driving_by_address",
            "transit": "maps_direction_transit_integrated_by_address",
        }
        tool_name = tool_map.get(route_type, "maps_direction_walking_by_address")

        arguments: Dict[str, Any] = {
            "origin_address": origin_address.strip(),
            "destination_address": destination_address.strip(),
        }
        if origin_city:
            arguments["origin_city"] = origin_city.strip()
        if destination_city:
            arguments["destination_city"] = destination_city.strip()

        payload = self._call_tool(tool_name=tool_name, arguments=arguments, preferred_keys=("route", "transits"))
        return self._normalize_route_payload(payload, route_type)

    def _normalize_route_payload(self, payload: Dict[str, Any], route_type: str) -> Dict[str, Any]:
        route = payload.get("route", payload)
        distance = 0.0
        duration = 0
        description = ""

        if route_type == "transit":
            transits = route.get("transits", []) if isinstance(route, dict) else []
            if not transits and isinstance(payload.get("transits"), list):
                transits = payload.get("transits", [])
            first = transits[0] if isinstance(transits, list) and transits else {}
            distance = self._to_float(first.get("distance"), 0.0)
            duration = self._to_int(first.get("duration"), 0)
            cost = str(first.get("cost") or "").strip()
            description = f"transit cost {cost}" if cost else "transit route planned"
        else:
            paths = route.get("paths", []) if isinstance(route, dict) else []
            first = paths[0] if isinstance(paths, list) and paths else {}
            distance = self._to_float(first.get("distance"), 0.0)
            duration = self._to_int(first.get("duration"), 0)
            description = str(first.get("strategy") or f"{route_type} route planned")

        return {
            "distance": distance,
            "duration": duration,
            "route_type": route_type,
            "description": description,
        }

    def _route_payload_via_http_from_locations(
        self,
        origin: Location,
        destination: Location,
        city: str,
        route_type: str,
        detailed: bool,
    ) -> Dict[str, Any]:
        origin_text = f"{origin.longitude},{origin.latitude}"
        destination_text = f"{destination.longitude},{destination.latitude}"
        extensions = "all" if detailed else "base"

        if route_type == "transit":
            params: Dict[str, Any] = {
                "origin": origin_text,
                "destination": destination_text,
                "city": city,
                "cityd": city,
                "extensions": extensions,
            }
            params = {key: value for key, value in params.items() if value}
            return self._http_get_json(AMAP_TRANSIT_URL, params)

        if route_type == "driving":
            return self._http_get_json(
                AMAP_DRIVING_URL,
                {
                    "origin": origin_text,
                    "destination": destination_text,
                    "extensions": extensions,
                },
            )

        params: Dict[str, Any] = {
            "origin": origin_text,
            "destination": destination_text,
        }
        if detailed:
            params["extensions"] = "all"
        return self._http_get_json(AMAP_WALKING_URL, params)

    def _normalize_day_route_stop(
        self,
        stop: Any,
        city: str,
        label: str,
        kind: str,
    ) -> Optional[RouteMarker]:
        if stop is None:
            return None

        if hasattr(stop, "model_dump"):
            data = stop.model_dump()
        elif isinstance(stop, dict):
            data = dict(stop)
        else:
            return None

        title = str(data.get("name") or "").strip()
        if not title:
            return None

        address = str(data.get("address") or "").strip()
        location = self._parse_location(data.get("location"))
        if location is None:
            for candidate in [address, f"{city}{title}" if city and title else "", title]:
                compact = str(candidate or "").strip()
                if not compact:
                    continue
                try:
                    location = self.geocode(compact, city or None)
                except Exception as exc:
                    logger.debug("AMap geocode failed for day route stop=%s candidate=%s error=%s", title, compact, exc)
                    location = None
                if location is not None:
                    break
        if location is None:
            return None

        return RouteMarker(
            label=label,
            title=title,
            kind=kind,
            address=address,
            location=location,
            image_url=str(data.get("image_url") or "").strip() or None,
        )

    def _build_day_route_segment(
        self,
        start: RouteMarker,
        end: RouteMarker,
        city: str,
        route_type: str,
    ) -> RouteSegment:
        route: Dict[str, Any] | None = None
        payload: Dict[str, Any] | None = None

        if self.http_enabled:
            try:
                payload = self._route_payload_via_http_from_locations(
                    origin=start.location,
                    destination=end.location,
                    city=city,
                    route_type=route_type,
                    detailed=True,
                )
                route = self._normalize_route_payload(payload, route_type)
            except Exception as exc:
                logger.warning(
                    "AMap day route segment failed via HTTP route_type=%s start=%s end=%s error=%s",
                    route_type,
                    start.title,
                    end.title,
                    exc,
                )

        if route is None and self.mcp_enabled:
            try:
                route = self._plan_route_via_mcp(
                    origin_address=start.address or start.title,
                    destination_address=end.address or end.title,
                    origin_city=city or None,
                    destination_city=city or None,
                    route_type=route_type,
                )
            except Exception as exc:
                logger.warning(
                    "AMap day route segment failed via MCP route_type=%s start=%s end=%s error=%s",
                    route_type,
                    start.title,
                    end.title,
                    exc,
                )

        if route is None:
            route = {
                "distance": 0.0,
                "duration": 0,
                "route_type": route_type,
                "description": "Route detail unavailable",
            }

        polyline = self._extract_route_polyline(payload, route_type, start.location, end.location)
        if len(polyline) < 2:
            polyline = [start.location, end.location]

        return RouteSegment(
            start_label=start.label,
            end_label=end.label,
            route_type=route_type,
            distance=float(route.get("distance") or 0.0),
            duration=int(route.get("duration") or 0),
            description=str(route.get("description") or ""),
            polyline=polyline,
        )

    def _extract_route_polyline(
        self,
        payload: Optional[Dict[str, Any]],
        route_type: str,
        origin: Location,
        destination: Location,
    ) -> List[Location]:
        if not isinstance(payload, dict):
            return [origin, destination]

        route = payload.get("route", payload)
        chunks: List[List[Location]] = []
        if route_type == "transit":
            transits = route.get("transits", []) if isinstance(route, dict) else []
            if not transits and isinstance(payload.get("transits"), list):
                transits = payload.get("transits", [])
            first = transits[0] if isinstance(transits, list) and transits else {}
            chunks = self._collect_polyline_chunks(first)
        else:
            paths = route.get("paths", []) if isinstance(route, dict) else []
            first = paths[0] if isinstance(paths, list) and paths else {}
            steps = first.get("steps", []) if isinstance(first, dict) else []
            if isinstance(steps, list):
                for step in steps:
                    if isinstance(step, dict):
                        chunks.append(self._parse_polyline_text(step.get("polyline")))
            if not chunks and isinstance(first, dict):
                chunks.append(self._parse_polyline_text(first.get("polyline")))

        merged = self._merge_polyline_chunks(chunks)
        return merged or [origin, destination]

    @classmethod
    def _collect_polyline_chunks(cls, value: Any) -> List[List[Location]]:
        chunks: List[List[Location]] = []
        if isinstance(value, dict):
            polyline = value.get("polyline")
            if polyline:
                chunks.append(cls._parse_polyline_text(polyline))
            for child in value.values():
                chunks.extend(cls._collect_polyline_chunks(child))
            return chunks
        if isinstance(value, list):
            for item in value:
                chunks.extend(cls._collect_polyline_chunks(item))
        return chunks

    @classmethod
    def _parse_polyline_text(cls, raw_polyline: Any) -> List[Location]:
        if not isinstance(raw_polyline, str):
            return []

        points: List[Location] = []
        for pair in raw_polyline.split(";"):
            compact = pair.strip()
            if not compact or "," not in compact:
                continue
            lng_text, lat_text = [part.strip() for part in compact.split(",", 1)]
            points.append(
                Location(
                    longitude=cls._to_float(lng_text, 0.0),
                    latitude=cls._to_float(lat_text, 0.0),
                )
            )
        return points

    @classmethod
    def _merge_polyline_chunks(cls, chunks: Sequence[Sequence[Location]]) -> List[Location]:
        merged: List[Location] = []
        for chunk in chunks:
            for point in chunk:
                if not merged or not cls._same_location(merged[-1], point):
                    merged.append(point)
        return merged

    @staticmethod
    def _same_location(left: Location, right: Location) -> bool:
        return round(float(left.longitude), 6) == round(float(right.longitude), 6) and round(
            float(left.latitude), 6
        ) == round(float(right.latitude), 6)

    def _build_day_route_summary(
        self,
        ordered_stops: Sequence[RouteMarker],
        route_type: str,
        total_distance: float,
        total_duration: int,
    ) -> str:
        if not ordered_stops:
            return ""

        sequence = " → ".join(stop.title for stop in ordered_stops)
        route_type_label = {
            "walking": "步行",
            "driving": "驾车",
            "transit": "公共交通",
        }.get(route_type, route_type)
        duration_text = self._format_duration(total_duration)
        distance_text = self._format_distance(total_distance)
        return f"建议按 {sequence} 的顺序出行，以{route_type_label}衔接，预计总里程 {distance_text}，总耗时 {duration_text}。"

    @staticmethod
    def _format_duration(duration_seconds: int) -> str:
        if duration_seconds <= 0:
            return "待确认"
        total_minutes = max(1, int(round(duration_seconds / 60)))
        hours, minutes = divmod(total_minutes, 60)
        if hours and minutes:
            return f"{hours}小时{minutes}分钟"
        if hours:
            return f"{hours}小时"
        return f"{minutes}分钟"

    @staticmethod
    def _format_distance(distance_meters: float) -> str:
        if distance_meters <= 0:
            return "待确认"
        if distance_meters >= 1000:
            return f"{distance_meters / 1000:.1f} 公里"
        return f"{int(round(distance_meters))} 米"

    def _get_poi_detail_via_http(self, poi_id: str) -> Dict[str, Any]:
        payload = self._http_get_json(
            AMAP_POI_DETAIL_URL,
            {
                "id": poi_id,
                "extensions": "all",
            },
        )
        pois = payload.get("pois")
        if isinstance(pois, list) and pois:
            return dict(pois[0])
        return payload

    def _get_poi_detail_via_mcp(self, poi_id: str) -> Dict[str, Any]:
        payload = self._call_tool(
            tool_name="maps_search_detail",
            arguments={"id": poi_id},
            preferred_keys=("pois", "poi"),
        )
        pois = payload.get("pois")
        if isinstance(pois, list) and pois:
            return dict(pois[0])
        poi = payload.get("poi")
        if isinstance(poi, dict):
            return dict(poi)
        return dict(payload)

    def _http_get_json(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key or self._http_client is None:
            raise RuntimeError("AMap HTTP client is not configured")

        endpoint_name = url.rsplit("/", 1)[-1]
        sanitized_params = {key: value for key, value in params.items() if key != "key"}
        self._runtime_trace(f"HTTP request -> {endpoint_name} params={sanitized_params}")
        response = self._http_client.get(url, params={"key": self.api_key, **params})
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            self._runtime_trace(f"HTTP response <- {endpoint_name} invalid JSON payload")
            raise ValueError("AMap HTTP response must be a JSON object")
        status = str(payload.get("status") or "")
        if status and status != "1":
            info = str(payload.get("info") or payload.get("infocode") or "AMap API request failed")
            self._runtime_trace(f"HTTP response <- {endpoint_name} failed info={info}")
            raise ValueError(f"{endpoint_name}: {info}")
        self._runtime_trace(
            f"HTTP response <- {endpoint_name} ok status={status or 'n/a'} keys={list(payload.keys())}"
        )
        return payload

    def _call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        preferred_keys: Sequence[str] = (),
    ) -> Dict[str, Any]:
        mcp_tool = self._ensure_mcp_tool()
        self._runtime_trace(f"MCP request -> {tool_name} arguments={arguments}")
        logger.debug("AMap call tool=%s arguments=%s", tool_name, arguments)
        raw_result = mcp_tool.run(
            {
                "action": "call_tool",
                "tool_name": tool_name,
                "arguments": arguments,
            }
        )
        payload = self._parse_tool_payload(raw_result, preferred_keys=preferred_keys)
        if not isinstance(payload, dict):
            self._runtime_trace(f"MCP response <- {tool_name} invalid payload type={type(payload).__name__}")
            raise ValueError(f"Unexpected AMap payload type for {tool_name}: {type(payload).__name__}")
        self._runtime_trace(f"MCP response <- {tool_name} ok keys={list(payload.keys())}")
        return payload

    @classmethod
    def _parse_tool_payload(
        cls,
        raw_result: Any,
        preferred_keys: Sequence[str] = (),
    ) -> Dict[str, Any]:
        if isinstance(raw_result, dict):
            return cls._normalize_payload_container(raw_result, preferred_keys)
        if isinstance(raw_result, list):
            return cls._normalize_payload_container(raw_result, preferred_keys)

        text = str(raw_result or "").strip()
        if not text:
            return {}

        direct = cls._safe_json_loads(text)
        if isinstance(direct, dict):
            return cls._normalize_payload_container(direct, preferred_keys)
        if isinstance(direct, list):
            return cls._normalize_payload_container(direct, preferred_keys)

        wrapped = cls._extract_tool_wrapped_payload(text)
        if wrapped is not None:
            wrapped_payload = cls._safe_json_loads(wrapped)
            if isinstance(wrapped_payload, dict):
                return cls._normalize_payload_container(wrapped_payload, preferred_keys)
            if isinstance(wrapped_payload, list):
                return cls._normalize_payload_container(wrapped_payload, preferred_keys)

        candidates: List[Any] = []
        for fragment in cls._extract_json_fragments(text):
            parsed = cls._safe_json_loads(fragment)
            if parsed is None:
                continue
            candidates.append(parsed)

        preferred = cls._pick_preferred_payload(candidates, preferred_keys)
        if isinstance(preferred, dict):
            return cls._normalize_payload_container(preferred, preferred_keys)
        if isinstance(preferred, list):
            return cls._normalize_payload_container(preferred, preferred_keys)

        return {"raw": text}

    @classmethod
    def _normalize_payload_container(cls, payload: Any, preferred_keys: Sequence[str]) -> Dict[str, Any]:
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, list):
            if len(payload) == 1 and isinstance(payload[0], dict):
                first = payload[0]
                if not preferred_keys or cls._contains_preferred_keys(first, preferred_keys):
                    return first
            return {"items": payload}
        return {"raw": str(payload)}

    @staticmethod
    def _safe_json_loads(text: str) -> Any:
        try:
            return json.loads(text)
        except Exception:
            return None

    @classmethod
    def _extract_tool_wrapped_payload(cls, text: str) -> Optional[str]:
        prefixes = ("[TOOL_RESPONSE:", "[TOOL_CALL_RESPONSE:", "[TOOL_CALL_RESULT:")
        for prefix in prefixes:
            start = text.find(prefix)
            if start < 0:
                continue

            if prefix == "[TOOL_CALL_RESULT:":
                marker_end = text.find("]\n", start)
                if marker_end < 0:
                    marker_end = text.find("]", start)
                remainder = text[marker_end + 1 :] if marker_end >= 0 else ""
            else:
                remainder = text[start + len(prefix) :]

            fragments = cls._extract_json_fragments(remainder)
            if fragments:
                return fragments[0]
        return None

    @classmethod
    def _pick_preferred_payload(cls, candidates: Iterable[Any], preferred_keys: Sequence[str]) -> Any:
        candidate_list = list(candidates)
        if not candidate_list:
            return None

        if preferred_keys:
            for candidate in candidate_list:
                if cls._contains_preferred_keys(candidate, preferred_keys):
                    return cls._unwrap_candidate(candidate)

        return cls._unwrap_candidate(candidate_list[0])

    @classmethod
    def _contains_preferred_keys(cls, candidate: Any, preferred_keys: Sequence[str]) -> bool:
        if isinstance(candidate, dict):
            if any(key in candidate for key in preferred_keys):
                return True
            data = candidate.get("data")
            if isinstance(data, dict) and any(key in data for key in preferred_keys):
                return True
        return False

    @staticmethod
    def _unwrap_candidate(candidate: Any) -> Any:
        if isinstance(candidate, dict):
            data = candidate.get("data")
            if isinstance(data, dict):
                return data
        return candidate

    @staticmethod
    def _extract_json_fragments(text: str) -> List[str]:
        openings = {"{": "}", "[": "]"}
        fragments: List[str] = []
        start: Optional[int] = None
        stack: List[str] = []
        in_string = False
        escape = False

        for index, char in enumerate(text):
            if start is None:
                if char in openings:
                    start = index
                    stack = [openings[char]]
                    in_string = False
                    escape = False
                continue

            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
                continue

            if char in openings:
                stack.append(openings[char])
                continue

            if char in ("}", "]"):
                if not stack or char != stack[-1]:
                    start = None
                    stack = []
                    continue
                stack.pop()
                if not stack and start is not None:
                    fragments.append(text[start : index + 1])
                    start = None

        return fragments

    @classmethod
    def _normalize_poi(cls, item: Any) -> Optional[POIInfo]:
        if not isinstance(item, dict):
            return None

        location = cls._parse_location(item.get("location"))
        if location is None:
            return None

        tel = item.get("tel")
        tel_value: Optional[str]
        if isinstance(tel, list):
            tel_value = "; ".join(str(entry) for entry in tel if entry)
        elif tel:
            tel_value = str(tel)
        else:
            tel_value = None

        address = str(item.get("address") or "").strip()
        if not address:
            parts = [
                item.get("pname"),
                item.get("province"),
                item.get("cityname"),
                item.get("city"),
                item.get("adname"),
                item.get("business_area"),
            ]
            address = " ".join(str(part).strip() for part in parts if part)

        return POIInfo(
            id=str(item.get("id") or item.get("poi_id") or ""),
            name=str(item.get("name") or ""),
            type=str(item.get("type") or item.get("typecode") or ""),
            address=address,
            location=location,
            tel=tel_value,
        )

    @classmethod
    def _normalize_forecast(cls, item: Any) -> Optional[WeatherInfo]:
        if not isinstance(item, dict):
            return None
        return WeatherInfo(
            date=str(item.get("date") or ""),
            day_weather=str(item.get("dayweather") or item.get("day_weather") or ""),
            night_weather=str(item.get("nightweather") or item.get("night_weather") or ""),
            day_temp=cls._to_int(item.get("daytemp"), 0),
            night_temp=cls._to_int(item.get("nighttemp"), 0),
            wind_direction=str(item.get("daywind") or item.get("winddirection") or ""),
            wind_power=str(item.get("daypower") or item.get("windpower") or ""),
        )

    @classmethod
    def _normalize_live_weather(cls, item: Any) -> Optional[WeatherInfo]:
        if not isinstance(item, dict):
            return None
        reporttime = str(item.get("reporttime") or "")
        date = reporttime.split(" ", 1)[0] if reporttime else ""
        weather = str(item.get("weather") or "")
        temp = cls._to_int(item.get("temperature"), 0)
        return WeatherInfo(
            date=date,
            day_weather=weather,
            night_weather=weather,
            day_temp=temp,
            night_temp=temp,
            wind_direction=str(item.get("winddirection") or ""),
            wind_power=str(item.get("windpower") or ""),
        )

    @classmethod
    def _parse_location(cls, raw_location: Any) -> Optional[Location]:
        if isinstance(raw_location, dict):
            lng = raw_location.get("longitude", raw_location.get("lng", raw_location.get("lon")))
            lat = raw_location.get("latitude", raw_location.get("lat"))
            if lng is None or lat is None:
                return None
            return Location(
                longitude=cls._to_float(lng, 0.0),
                latitude=cls._to_float(lat, 0.0),
            )

        if isinstance(raw_location, str) and "," in raw_location:
            lng_text, lat_text = [part.strip() for part in raw_location.split(",", 1)]
            return Location(
                longitude=cls._to_float(lng_text, 0.0),
                latitude=cls._to_float(lat_text, 0.0),
            )

        return None

    @staticmethod
    def _to_int(value: Any, default: int) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            compact = value.strip()
            if compact:
                try:
                    return int(float(compact))
                except ValueError:
                    return default
        return default

    @staticmethod
    def _to_float(value: Any, default: float) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            compact = value.strip()
            if compact:
                try:
                    return float(compact)
                except ValueError:
                    return default
        return default


def get_amap_service() -> AmapService:
    """Return singleton AMap service."""
    global _amap_service

    if _amap_service is None:
        _amap_service = AmapService()

    return _amap_service
