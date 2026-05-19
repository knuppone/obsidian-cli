from __future__ import annotations

import urllib.parse
import warnings
from typing import Any, Callable, Dict, Optional, TypeVar

import requests
from urllib3.exceptions import InsecureRequestWarning

from obsidian_cli.api_key import load_api_key_from_vault
from obsidian_cli.config import AppConfig
from obsidian_cli.models import DEFAULT_TEXT_CONTENT_TYPE, JSONLOGIC_CONTENT_TYPE, NOTE_JSON_ACCEPT

T = TypeVar("T")


class RestHttpClient:
    def __init__(self, config: AppConfig) -> None:
        if not config.api_key:
            raise ValueError("API key is required for REST backend.")
        self._vault_root = config.vault_root
        self._api_key: str = config.api_key
        self._api_key_source: str = config.api_key_source
        self._protocol: str = config.protocol
        self._host: str = config.host
        self._port: int = config.port
        self._verify_ssl: bool = config.verify_ssl
        self._timeout: tuple[int, int] = (3, 30)
        self._retried_auth: bool = False
        if not self._verify_ssl:
            warnings.filterwarnings("ignore", category=InsecureRequestWarning)

    @property
    def base_url(self) -> str:
        return f"{self._protocol}://{self._host}:{self._port}"

    def headers(
        self,
        *,
        accept: Optional[str] = "application/json",
        content_type: Optional[str] = None,
        extra: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        result: Dict[str, str] = {"Authorization": f"Bearer {self._api_key}"}
        if accept:
            result["Accept"] = accept
        if content_type:
            result["Content-Type"] = content_type
        if extra:
            result.update(extra)
        return result

    def _try_vault_plugin_key_on_auth_failure(self, error_code: Any) -> bool:
        if error_code != 40101 or self._retried_auth:
            return False
        vault_key: Optional[str] = load_api_key_from_vault(self._vault_root)
        if not vault_key or vault_key == self._api_key:
            return False
        self._api_key = vault_key
        self._retried_auth = True
        return True

    def safe_call(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except requests.HTTPError as exc:
            error_data: Dict[str, Any] = dict()
            if exc.response is not None and exc.response.content:
                try:
                    parsed = exc.response.json()
                    if isinstance(parsed, dict):
                        error_data = parsed
                except ValueError:
                    pass
            code: Any = error_data.get("errorCode", -1)
            message: str = str(error_data.get("message", " "))
            if self._try_vault_plugin_key_on_auth_failure(code):
                return fn()
            hint: str = (
                f" (key source: {self._api_key_source}, length {len(self._api_key)}). "
                "Re-copy the key from Obsidian → Settings → Local REST API, or unset "
                "OBSIDIAN_API_KEY to use the vault plugin file automatically."
            )
            if code == 40101:
                raise RuntimeError(f"Error {code}: {message}{hint}") from exc
            raise RuntimeError(f"Error {code}: {message}") from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"Request failed: {exc}") from exc

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[bytes] = None,
        json_body: Optional[Any] = None,
        accept: Optional[str] = "application/json",
        content_type: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        url: str = f"{self.base_url}{path}"

        def call_fn() -> requests.Response:
            response = requests.request(
                method,
                url,
                headers=self.headers(
                    accept=accept,
                    content_type=content_type,
                    extra=extra_headers,
                ),
                params=params,
                data=data,
                json=json_body,
                verify=self._verify_ssl,
                timeout=self._timeout,
            )
            response.raise_for_status()
            return response

        return self.safe_call(call_fn)

    def patch_with_target(
        self,
        path: str,
        patch_content: str,
        operation: str,
        target_type: str,
        target: str,
        *,
        target_scope: Optional[str] = None,
    ) -> requests.Response:
        extra: Dict[str, str] = {
            "Operation": operation,
            "Target-Type": target_type,
            "Target": urllib.parse.quote(target),
        }
        if target_scope:
            extra["Target-Scope"] = target_scope
        return self.request(
            "PATCH",
            path,
            data=patch_content.encode("utf-8"),
            content_type="text/markdown",
            accept="application/json",
            extra_headers=extra,
        )

    @staticmethod
    def text_content_type() -> str:
        return DEFAULT_TEXT_CONTENT_TYPE

    @staticmethod
    def note_json_accept() -> str:
        return NOTE_JSON_ACCEPT

    @staticmethod
    def jsonlogic_content_type() -> str:
        return JSONLOGIC_CONTENT_TYPE
