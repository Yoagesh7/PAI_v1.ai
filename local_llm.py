import json
import os
import time

import requests


class AIConnectionError(RuntimeError):
    """Raised when the NVIDIA API cannot be reached or returns an error."""


# Backwards-compatible alias used by the existing app code.
OllamaConnectionError = AIConnectionError


_OFFLINE_MSG = (
    " **AI service unavailable.**\n\n"
    "Set the NVIDIA API key in your environment and try again."
)


class RAGSystem:
    def __init__(self):
        self.base_url = os.getenv("NVIDIA_API_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip("/")
        self.api_key = (
            os.getenv("NVIDIA_API_KEY")
            or os.getenv("NVAPI_API_KEY")
            or os.getenv("NVIDIA_API_TOKEN")
            or ""
        )
        self.model = os.getenv("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")
        self.max_retries = 2
        self.retry_delay = 1.5
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
        if len(valid_messages) > 15:
            valid_messages = [valid_messages[0]] + valid_messages[-14:]
        return valid_messages

    def _request(self, payload, stream=False):
        url = f"{self.base_url}/chat/completions"
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(url, headers=self._headers(), json=payload, timeout=120, stream=stream)
                if response.status_code != 200:
                    detail = response.text[:500]
                    raise AIConnectionError(f"NVIDIA API error {response.status_code}: {detail}")
                return response
            except requests.exceptions.RequestException as exc:
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                raise AIConnectionError(str(exc)) from exc

    def generate_response(self, messages, temperature=0.7):
        valid_messages = self._clean_messages(messages)
        payload = {
            "model": self.model,
            "messages": valid_messages,
            "temperature": temperature,
            "max_tokens": 2048,
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
            return {"message": {"content": _OFFLINE_MSG}}
        except Exception as exc:
            print(f"AI Error: {exc}", flush=True)
            return {"message": {"content": f"I'm having trouble thinking right now. ({exc})"}}

    def generate_response_stream(self, messages, temperature=0.7):
        valid_messages = self._clean_messages(messages)
        payload = {
            "model": self.model,
            "messages": valid_messages,
            "temperature": temperature,
            "max_tokens": 2048,
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
            yield _OFFLINE_MSG
        except Exception as exc:
            print(f"AI Stream Error: {exc}", flush=True)
            yield f"(Connection Error: {exc})"

    def generate_json(self, prompt):
        messages = [{"role": "user", "content": prompt}]
        return self.generate_response(messages, temperature=0.3)


# Global Instance
rag_system = RAGSystem()
