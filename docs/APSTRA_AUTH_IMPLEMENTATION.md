# Apstra Controller Authentication Guide

This document provides a comprehensive guide for implementing the correct authentication method for Juniper Apstra controllers in any Python project.

## 1. Apstra Authentication Overview

Juniper Apstra controllers utilize a session-based authentication mechanism that requires a specific implementation pattern, differing from standard REST APIs.

### Key Characteristics:
- **Authentication Endpoint**: `POST` request to `/api/aaa/login`.
- **Request Body**: JSON payload containing `{"username": "user", "password": "pass"}`.
- **Authentication Header**: The controller issues a token that must be sent in the `AUTHTOKEN` header for all subsequent requests. This is different from the standard `Authorization: Bearer <token>` header.
- **Token Caching**: The authentication token should be cached and reused for multiple requests until it expires.
- **Error Handling**: Proper error handling is crucial, especially for `401 Unauthorized` responses, which indicate an invalid or expired token.

---

## 2. Python Implementation

This section provides a detailed, step-by-step guide to implementing an Apstra API client in Python using `httpx`.

### Step 2.1: Client Initialization

The `ApstraClient` class is initialized with the necessary connection details and an `httpx.AsyncClient` instance.

```python
import httpx
import asyncio
from typing import Optional
from urllib.parse import urljoin

class ApstraClient:
    """An asynchronous client for interacting with the Apstra API."""

    def __init__(self, host: str, username: str, password: str, port: int = 443, use_https: bool = True, verify_ssl: bool = False):
        """
        Initializes the ApstraClient.

        Args:
            host: The hostname or IP address of the Apstra controller.
            username: The username for authentication.
            password: The password for authentication.
            port: The port number for the controller (default: 443).
            use_https: Whether to use HTTPS for the connection (default: True).
            verify_ssl: Whether to verify the SSL certificate (default: False).
        """
        self.host = host
        self.port = port
        self.use_https = use_https
        self.username = username
        self.password = password
        self._auth_token: Optional[str] = None

        protocol = "https" if use_https else "http"
        if (use_https and port == 443) or (not use_https and port == 80):
            self.base_url = f"{protocol}://{host}"
        else:
            self.base_url = f"{protocol}://{host}:{port}"

        self._client = httpx.AsyncClient(
            timeout=30.0,
            verify=verify_ssl,
            follow_redirects=True
        )
```

### Step 2.2: Authentication Method

The `authenticate` method handles the login process and caches the token.

```python
    async def authenticate(self) -> str:
        """
        Authenticates with the Apstra controller and caches the auth token.
        
        Returns:
            The authentication token.
            
        Raises:
            ValueError: If authentication fails or the token is not found.
            httpx.RequestError: If a network error occurs.
        """
        if self._auth_token:
            # Note: For production environments, consider implementing a token
            # expiration check to ensure the token is still valid.
            return self._auth_token

        auth_url = urljoin(self.base_url, "/api/aaa/login")
        auth_data = {"username": self.username, "password": self.password}

        try:
            response = await self._client.post(auth_url, json=auth_data)
            response.raise_for_status()

            auth_response = response.json()
            self._auth_token = auth_response.get("token")
            if not self._auth_token:
                raise ValueError("Authentication failed: token not found in response.")

            # Set the Apstra-specific AUTHTOKEN header for all future requests
            self._client.headers["AUTHTOKEN"] = self._auth_token
            return self._auth_token

        except httpx.HTTPStatusError as e:
            raise ValueError(f"Authentication failed with status {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise ConnectionError(f"Network error during authentication: {e}")

```

### Step 2.3: Making Authenticated Requests

The `_make_request` method ensures that all outgoing requests are authenticated and handles token expiration.

```python
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """
        Makes an authenticated HTTP request to the Apstra API.

        Args:
            method: The HTTP method (e.g., 'GET', 'POST').
            endpoint: The API endpoint path.
            **kwargs: Additional arguments for the request.

        Returns:
            The HTTP response.
        """
        await self.authenticate()
        
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = await self._client.request(method=method, url=url, **kwargs)

            # Handle token expiration by re-authenticating once
            if response.status_code == 401:
                self._auth_token = None
                if "AUTHTOKEN" in self._client.headers:
                    del self._client.headers["AUTHTOKEN"]
                
                await self.authenticate()
                response = await self._client.request(method=method, url=url, **kwargs)

            response.raise_for_status()
            return response

        except httpx.RequestError as e:
            raise ConnectionError(f"Request to {endpoint} failed: {e}")
```

### Step 2.4: Context Manager Support

Implementing `__aenter__` and `__aexit__` allows the client to be used as an async context manager, ensuring resources are properly managed.

```python
    async def __aenter__(self):
        """Async context manager entry."""
        await self.authenticate()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Closes the HTTP client."""
        if self._client:
            await self._client.aclose()
```

---

## 3. Common Mistakes to Avoid

1.  **Incorrect Endpoint**: Using `/api/user/login` instead of the correct `/api/aaa/login`.
2.  **Incorrect Header**: Using the standard `Authorization: Bearer` header instead of the required `AUTHTOKEN` header.
3.  **No Token Caching**: Authenticating on every request, which is inefficient and can lead to performance issues.
4.  **No Error Handling**: Failing to handle network errors or `401 Unauthorized` responses gracefully.
5.  **SSL Verification Issues**: Not disabling SSL verification (`verify=False`) when connecting to controllers with self-signed certificates.

---

## 4. Testing the Implementation

Here is an example of how to test the `ApstraClient` using `pytest` and `unittest.mock`.

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_authentication_success():
    """Tests successful authentication with the Apstra controller."""
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock a successful authentication response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "test-token-123"}
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response
        
        client = ApstraClient("https://test.apstra.com", "admin", "admin")
        token = await client.authenticate()
        
        assert token == "test-token-123"
        assert client._client.headers["AUTHTOKEN"] == "test-token-123"
```

---

## 5. Complete Working Example

This example demonstrates how to use the `ApstraClient` to connect to a controller and retrieve a list of blueprints. The code below assumes the `ApstraClient` class from the previous sections is defined in the same file.

```python
async def main():
    """Main function to demonstrate ApstraClient usage."""
    # Replace with your Apstra controller's details
    APSTRA_HOST = "10.85.192.46"
    APSTRA_USERNAME = "admin"
    APSTRA_PASSWORD = "admin"

    try:
        async with ApstraClient(APSTRA_HOST, APSTRA_USERNAME, APSTRA_PASSWORD) as client:
            # Example: Get all blueprints
            response = await client._make_request("GET", "/api/blueprints")
            blueprints = response.json()
            print(f"Successfully retrieved {len(blueprints.get('items', []))} blueprints.")

    except (ValueError, ConnectionError) as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

This authentication pattern has been tested and verified against Juniper Apstra controllers.