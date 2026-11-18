import sys
sys.path.insert(0, 'c:/RN/Demo')
from mcp_monitor.web_interface import create_web_interface
from mcp_monitor import MCPMonitor
m = MCPMonitor()
app = create_web_interface(m)
c = app.test_client()
r = c.get('/')
print('Status:', r.status_code)
print('Body:', r.get_data(as_text=True)[:200])