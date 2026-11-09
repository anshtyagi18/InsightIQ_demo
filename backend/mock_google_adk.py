"""
Mock google.adk module to prevent import errors.
Registers mock classes into sys.modules.
"""
import sys
from types import ModuleType

class MockAgent:
    def __init__(self, *args, **kwargs):
        pass

class MockFunctionTool:
    def __init__(self, *args, **kwargs):
        pass

class MockADK:
    def __init__(self):
        pass
    def authenticate(self, *args, **kwargs):
        return True
    def get_client(self, *args, **kwargs):
        return MockClient()

class MockClient:
    def __init__(self):
        pass
    def query(self, *args, **kwargs):
        return {}
    def upload(self, *args, **kwargs):
        return {"status": "success"}

adk = MockADK()

# Ensure google and google.adk are proper package modules in sys.modules
google_mod = ModuleType("google")
google_mod.__path__ = []
adk_mod = ModuleType("google.adk")
adk_mod.__path__ = []
agents_mod = ModuleType("google.adk.agents")
tools_mod = ModuleType("google.adk.tools")

setattr(adk_mod, "adk", adk)
setattr(adk_mod, "MockADK", MockADK)
setattr(adk_mod, "MockClient", MockClient)
setattr(agents_mod, "Agent", MockAgent)
setattr(tools_mod, "FunctionTool", MockFunctionTool)

setattr(google_mod, "adk", adk_mod)
setattr(adk_mod, "agents", agents_mod)
setattr(adk_mod, "tools", tools_mod)

sys.modules["google"] = google_mod
sys.modules["google.adk"] = adk_mod
sys.modules["google.adk.agents"] = agents_mod
sys.modules["google.adk.tools"] = tools_mod

__all__ = ['adk', 'MockADK', 'MockClient', 'MockAgent', 'MockFunctionTool']
