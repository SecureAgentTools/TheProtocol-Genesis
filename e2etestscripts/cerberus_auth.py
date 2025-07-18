"""
Shared authentication utilities for Cerberus tests.
Provides commander login and token management.
"""
import aiohttp
import asyncio
from typing import Optional, Dict, Any

# Commander credentials
COMMANDER_EMAIL = "commander@agentvault.com"
COMMANDER_PASSWORD = "SovereignKey!2025"

# Base configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"


class AuthManager:
    """Manages authentication for test scripts"""
    
    def __init__(self):
        self.access_token: Optional[str] = None
        self.token_type: str = "Bearer"
        
    async def login(self, session: aiohttp.ClientSession) -> bool:
        """Login with commander credentials"""
        try:
            # OAuth2 requires form data, not JSON
            form_data = aiohttp.FormData()
            form_data.add_field('username', COMMANDER_EMAIL)
            form_data.add_field('password', COMMANDER_PASSWORD)
            
            async with session.post(
                f"{BASE_URL}{API_PREFIX}/auth/login",
                data=form_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data.get('access_token')
                    self.token_type = data.get('token_type', 'Bearer')
                    return True
                else:
                    print(f"[AUTH] Login failed with status {response.status}")
                    return False
        except Exception as e:
            print(f"[AUTH] Login error: {str(e)}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        if self.access_token:
            return {"Authorization": f"{self.token_type} {self.access_token}"}
        return {}
    
    async def ensure_authenticated(self, session: aiohttp.ClientSession) -> bool:
        """Ensure we have a valid token"""
        if not self.access_token:
            return await self.login(session)
        return True


# Global auth manager instance
auth_manager = AuthManager()


async def get_authenticated_session() -> aiohttp.ClientSession:
    """Get an authenticated aiohttp session"""
    session = aiohttp.ClientSession()
    await auth_manager.ensure_authenticated(session)
    return session


def get_auth_headers() -> Dict[str, str]:
    """Get current auth headers"""
    return auth_manager.get_headers()
