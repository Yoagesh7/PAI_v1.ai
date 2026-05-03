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
        self.model = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")
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


rag_system = RAGSystem()import requests
import json
import os
import time

_OFFLINE_MSG = (
    " **AI mentor is offline.**\n\n"
    "The local LLM server isn't running. "
    "Please start **start_llama.bat** and try again."
)

class RAGSystem:
    def __init__(self, base_url="http://127.0.0.1:8080"):
        self.base_url = base_url
        self.max_retries = 2
        self.retry_delay = 1.5          # seconds between retries
        print(f"rag_system initialized with {base_url}")

    def _is_server_up(self):
        """Quick ping to /health before spending time on a full request."""
        try:
            r = requests.get(f"{self.base_url}/health", timeout=3)
            return r.status_code == 200
        except Exception as e:
            print(f"DEBUG: LLM Health check failed: {e}")
            return False

    def generate_response(self, messages, temperature=0.7):
        url = f"{self.base_url}/v1/chat/completions"
        valid_messages = [m for m in messages if 'role' in m and 'content' in m]
        # Truncate if too many messages
        if len(valid_messages) > 15:
            valid_messages = [valid_messages[0]] + valid_messages[-14:]

        payload = {
            "messages": valid_messages,
            "temperature": temperature,
            "max_tokens": 2048,
            "stream": False
        }

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(url, json=payload, timeout=120)
                if response.status_code != 200:
                    print(f"LLM Error Status: {response.status_code} - {response.text}")
                    return {'message': {'content': f"Error: {response.text}"}}
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    return {'message': {'content': data['choices'][0]['message']['content']}}
                return {'message': {'content': "Error: No response from model."}}
            except requests.exceptions.ConnectionError as e:
                if attempt < self.max_retries:
                    print(f"LLM connection failed (attempt {attempt+1}), retrying in {self.retry_delay}s")
                    time.sleep(self.retry_delay)
                else:
                    print(f"LLM Connection Error (all retries exhausted): {e}")
                    return {'message': {'content': _OFFLINE_MSG}}
            except Exception as e:
                print(f"LLM Error: {e}")
                return {'message': {'content': f"I'm having trouble thinking right now. ({e})"}}

    def generate_response_stream(self, messages, temperature=0.7):
        """Stream tokens one by one from llama.cpp SSE endpoint."""
        url = f"{self.base_url}/v1/chat/completions"
        
        # Fast pre-flight check so the caller gets an immediate friendly message
        if not self._is_server_up():
            yield _OFFLINE_MSG
            return

        valid_messages = [m for m in messages if 'role' in m and 'content' in m]
        # Truncate messages if they have too many items to stay safe
        if len(valid_messages) > 15:
            valid_messages = [valid_messages[0]] + valid_messages[-14:]

        payload = {
            "messages": valid_messages,
            "temperature": temperature,
            "max_tokens": 2048,
            "stream": True
        }

        try:
            response = requests.post(url, json=payload, timeout=120, stream=True)
            if response.status_code != 200:
                error_detail = response.text[:100]
                yield f"(Error {response.status_code}: {error_detail})"
                return
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                yield content
                        except Exception:
                            pass
        except requests.exceptions.ConnectionError as e:
            print(f"LLM Stream Connection Error: {e}")
            yield _OFFLINE_MSG
        except Exception as e:
            print(f"LLM Stream Error: {e}")
            yield f"(Connection Error: {e})"

    def generate_json(self, prompt):
        messages = [{"role": "user", "content": prompt}]
        return self.generate_response(messages, temperature=0.3)

# Global Instance
rag_system = RAGSystem()
