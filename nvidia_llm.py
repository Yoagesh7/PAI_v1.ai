import json
import os
import time

import requests


def _load_config_value(name, default=""):
    try:
        import config
        return getattr(config, name, default)
    except Exception:
        return default


class AIConnectionError(RuntimeError):
    """Raised when the NVIDIA API cannot be reached or returns an error."""


_OFFLINE_MSG = (
    " **AI service unavailable.**\n\n"
    "Set the NVIDIA API key in your environment and try again."
)


class RAGSystem:
    def __init__(self):
        self.base_url = (
            os.getenv("NVIDIA_API_BASE_URL")
            or _load_config_value("NVIDIA_API_BASE_URL", "https://integrate.api.nvidia.com/v1")
        ).rstrip("/")
        self.api_key = (
            os.getenv("NVIDIA_API_KEY")
            or os.getenv("NVAPI_API_KEY")
            or os.getenv("NVIDIA_API_TOKEN")
            or _load_config_value("NVIDIA_API_KEY", "")
            or ""
        )
        self.model = os.getenv("NVIDIA_MODEL") or _load_config_value("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")
        # Tunable retry/backoff settings
        self.max_retries = int(os.getenv('NVIDIA_MAX_RETRIES', '3'))
        self.retry_delay = float(os.getenv('NVIDIA_RETRY_DELAY', '0.8'))
        # Circuit breaker: if many consecutive failures, pause calls for cooldown seconds
        self._consecutive_failures = 0
        self._failure_threshold = int(os.getenv('NVIDIA_FAILURE_THRESHOLD', '4'))
        self._cooldown_seconds = int(os.getenv('NVIDIA_COOLDOWN_SECONDS', '60'))
        self._last_failure_time = 0
        print(f"rag_system initialized with NVIDIA API model={self.model}", flush=True)

    def _headers(self):
        if not self.api_key:
            raise AIConnectionError("NVIDIA API key is missing. Set NVIDIA_API_KEY or NVAPI_API_KEY.")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _clean_messages(messages):
        valid_messages = [m for m in messages if isinstance(m, dict) and m.get("role") and m.get("content")]
        cleaned = []
        for idx, msg in enumerate(valid_messages):
            content = str(msg.get("content", ""))
            if len(content) > 2000:
                content = content[:2000] + "\n...[truncated]"
            cleaned.append({"role": msg["role"], "content": content})
        if len(cleaned) > 9:
            cleaned = [cleaned[0]] + cleaned[-8:]
        return cleaned

    def _request(self, payload, stream=False):
        url = f"{self.base_url}/chat/completions"
        # Check circuit breaker
        if self._consecutive_failures >= self._failure_threshold:
            elapsed = time.time() - self._last_failure_time
            if elapsed < self._cooldown_seconds:
                raise AIConnectionError("NVIDIA service temporarily disabled due to repeated errors.")
            else:
                # reset after cooldown
                self._consecutive_failures = 0
        for attempt in range(self.max_retries + 1):
            try:
                timeout = int(os.getenv('NVIDIA_TIMEOUT', '30'))
                response = requests.post(url, headers=self._headers(), json=payload, timeout=timeout, stream=stream)
                if response.status_code != 200:
                    detail = response.text[:500]
                    # record failure
                    self._consecutive_failures += 1
                    self._last_failure_time = time.time()
                    raise AIConnectionError(f"NVIDIA API error {response.status_code}: {detail}")
                return response
            except requests.exceptions.RequestException as exc:
                # record failure
                self._consecutive_failures += 1
                self._last_failure_time = time.time()
                if attempt < self.max_retries:
                    # exponential backoff
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise AIConnectionError(str(exc)) from exc

    def generate_response(self, messages, temperature=0.7):
        valid_messages = self._clean_messages(messages)
        payload = {
            "model": self.model,
            "messages": valid_messages,
            "temperature": temperature,
            "max_tokens": 768,
            "stream": False,
        }

        try:
            response = self._request(payload, stream=False)
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                return {"message": {"content": content}}
            return {"message": {"content": "Error: No response from model."}}
        except AIConnectionError as exc:
            print(f"AI Error: {exc}", flush=True)
            return {"message": {"content": f"{_OFFLINE_MSG}\n\nDebug: {exc}"}}
        except Exception as exc:
            print(f"AI Error: {exc}", flush=True)
            return {"message": {"content": f"I'm having trouble thinking right now. ({exc})"}}

    def generate_response_stream(self, messages, temperature=0.7):
        valid_messages = self._clean_messages(messages)
        payload = {
            "model": self.model,
            "messages": valid_messages,
            "temperature": temperature,
            "max_tokens": 768,
            "stream": True,
        }

        try:
            response = self._request(payload, stream=True)
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except Exception:
                        continue
        except AIConnectionError as exc:
            print(f"AI Stream Error: {exc}", flush=True)
            yield f"{_OFFLINE_MSG}\n\nDebug: {exc}"
        except Exception as exc:
            print(f"AI Stream Error: {exc}", flush=True)
            yield f"(Connection Error: {exc})"

    def generate_json(self, prompt):
        messages = [{"role": "user", "content": prompt}]
        return self.generate_response(messages, temperature=0.3)


rag_system = RAGSystem()
