
from app.dependencies import require_role

admin_check = require_role("Admin")
agent_check = require_role("Admin", "Support Agent")

print("RBAC functions created successfully.")
