"""Create a test client user for testing client-specific data filtering."""
import sys
import os

# Change to backend directory so relative paths work
os.chdir(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, '.')

from services.auth_service import auth_service

# Create a client user for Lowe-Parker (CUST-2234)
result = auth_service.create_user(
    username="lowe_client",
    email="client@loweparker.com",
    full_name="Lowe Parker Client",
    password="Test123!",
    role_names=["client_user"],
    client_id="CUST-2234"
)

print(f"Client user created: {result}")
print("Username: lowe_client")
print("Password: Test123!")
print("Client ID: CUST-2234")
print("This user will only see data for Lowe-Parker")
