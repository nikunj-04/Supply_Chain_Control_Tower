"""Seed initial authentication data: roles, permissions, and default users."""
from models.auth_models import User, Role, Permission, get_auth_session
from datetime import datetime

def seed_auth_data():
    """Create initial roles, permissions, and users."""
    session = get_auth_session()
    
    try:
        # Check if already seeded
        if session.query(Role).count() > 0:
            print("Auth data already seeded.")
            return
        
        print("Seeding authentication data...")
        
        # Define permissions
        permissions_data = [
            # Dashboard
            {"name": "dashboard.view", "display_name": "View Dashboard", "module": "dashboard", "action": "view", "description": "View main dashboard"},
            
            # WMS Permissions
            {"name": "wms.view", "display_name": "View WMS", "module": "wms", "action": "view", "description": "View warehouse data"},
            {"name": "wms.edit", "display_name": "Edit WMS", "module": "wms", "action": "edit", "description": "Edit warehouse data"},
            {"name": "wms.inventory.manage", "display_name": "Manage Inventory", "module": "wms", "action": "manage", "description": "Manage inventory levels"},
            {"name": "wms.receiving", "display_name": "Receive Items", "module": "wms", "action": "receive", "description": "Process receiving operations"},
            {"name": "wms.picking", "display_name": "Pick Orders", "module": "wms", "action": "pick", "description": "Process picking operations"},
            
            # TMS Permissions
            {"name": "tms.view", "display_name": "View TMS", "module": "tms", "action": "view", "description": "View transportation data"},
            {"name": "tms.edit", "display_name": "Edit TMS", "module": "tms", "action": "edit", "description": "Edit shipment data"},
            {"name": "tms.create", "display_name": "Create Shipments", "module": "tms", "action": "create", "description": "Create new shipments"},
            {"name": "tms.carrier.manage", "display_name": "Manage Carriers", "module": "tms", "action": "manage", "description": "Manage carrier relationships"},
            
            # OMS Permissions
            {"name": "oms.view", "display_name": "View Orders", "module": "oms", "action": "view", "description": "View order data"},
            {"name": "oms.edit", "display_name": "Edit Orders", "module": "oms", "action": "edit", "description": "Edit order data"},
            {"name": "oms.create", "display_name": "Create Orders", "module": "oms", "action": "create", "description": "Create new orders"},
            {"name": "oms.cancel", "display_name": "Cancel Orders", "module": "oms", "action": "cancel", "description": "Cancel orders"},
            
            # Billing Permissions
            {"name": "billing.view", "display_name": "View Billing", "module": "billing", "action": "view", "description": "View billing data"},
            {"name": "billing.edit", "display_name": "Edit Billing", "module": "billing", "action": "edit", "description": "Edit billing data"},
            {"name": "billing.approve", "display_name": "Approve Invoices", "module": "billing", "action": "approve", "description": "Approve invoices for payment"},
            {"name": "billing.export", "display_name": "Export Billing", "module": "billing", "action": "export", "description": "Export billing data"},
            
            # Returns Permissions
            {"name": "returns.view", "display_name": "View Returns", "module": "returns", "action": "view", "description": "View return data"},
            {"name": "returns.process", "display_name": "Process Returns", "module": "returns", "action": "process", "description": "Process return requests"},
            {"name": "returns.approve", "display_name": "Approve Returns", "module": "returns", "action": "approve", "description": "Approve return refunds"},
            
            # Yard Permissions
            {"name": "yard.view", "display_name": "View Yard", "module": "yard", "action": "view", "description": "View yard operations"},
            {"name": "yard.manage", "display_name": "Manage Yard", "module": "yard", "action": "manage", "description": "Manage dock schedules and yard"},
            
            # Exception Permissions
            {"name": "exceptions.view", "display_name": "View Exceptions", "module": "exceptions", "action": "view", "description": "View exceptions"},
            {"name": "exceptions.assign", "display_name": "Assign Exceptions", "module": "exceptions", "action": "assign", "description": "Assign exceptions to users"},
            {"name": "exceptions.resolve", "display_name": "Resolve Exceptions", "module": "exceptions", "action": "resolve", "description": "Resolve exceptions"},
            {"name": "exceptions.escalate", "display_name": "Escalate Exceptions", "module": "exceptions", "action": "escalate", "description": "Escalate exceptions"},
            
            # Reports Permissions
            {"name": "reports.view", "display_name": "View Reports", "module": "reports", "action": "view", "description": "View reports"},
            {"name": "reports.generate", "display_name": "Generate Reports", "module": "reports", "action": "generate", "description": "Generate custom reports"},
            {"name": "reports.schedule", "display_name": "Schedule Reports", "module": "reports", "action": "schedule", "description": "Schedule automated reports"},
            {"name": "reports.export", "display_name": "Export Reports", "module": "reports", "action": "export", "description": "Export report data"},
            
            # Analytics Permissions
            {"name": "analytics.view", "display_name": "View Analytics", "module": "analytics", "action": "view", "description": "View analytics dashboards"},
            {"name": "analytics.advanced", "display_name": "Advanced Analytics", "module": "analytics", "action": "advanced", "description": "Access advanced analytics"},
            
            # Admin Permissions
            {"name": "admin.users", "display_name": "Manage Users", "module": "admin", "action": "manage", "description": "Manage user accounts"},
            {"name": "admin.roles", "display_name": "Manage Roles", "module": "admin", "action": "manage", "description": "Manage roles and permissions"},
            {"name": "admin.system", "display_name": "System Admin", "module": "admin", "action": "manage", "description": "Full system administration"},
        ]
        
        # Create permissions
        permissions = {}
        for perm_data in permissions_data:
            perm = Permission(**perm_data)
            session.add(perm)
            permissions[perm.name] = perm
        
        session.flush()
        
        # Define roles with their permissions
        roles_data = [
            {
                "name": "system_admin",
                "display_name": "System Administrator",
                "description": "Full system access and administration",
                "permissions": list(permissions.values())  # All permissions
            },
            {
                "name": "operations_manager",
                "display_name": "Operations Manager",
                "description": "Manage all operational aspects across WMS, TMS, OMS",
                "permissions": [
                    permissions["dashboard.view"],
                    permissions["wms.view"], permissions["wms.edit"], permissions["wms.inventory.manage"],
                    permissions["tms.view"], permissions["tms.edit"], permissions["tms.create"],
                    permissions["oms.view"], permissions["oms.edit"], permissions["oms.create"],
                    permissions["yard.view"], permissions["yard.manage"],
                    permissions["exceptions.view"], permissions["exceptions.assign"], permissions["exceptions.resolve"], permissions["exceptions.escalate"],
                    permissions["reports.view"], permissions["reports.generate"], permissions["reports.export"],
                    permissions["analytics.view"], permissions["analytics.advanced"],
                ]
            },
            {
                "name": "warehouse_manager",
                "display_name": "Warehouse Manager",
                "description": "Manage warehouse operations, inventory, and yard",
                "permissions": [
                    permissions["dashboard.view"],
                    permissions["wms.view"], permissions["wms.edit"], permissions["wms.inventory.manage"],
                    permissions["wms.receiving"], permissions["wms.picking"],
                    permissions["yard.view"], permissions["yard.manage"],
                    permissions["oms.view"],
                    permissions["exceptions.view"], permissions["exceptions.resolve"],
                    permissions["reports.view"], permissions["reports.generate"],
                    permissions["analytics.view"],
                ]
            },
            {
                "name": "transportation_manager",
                "display_name": "Transportation Manager",
                "description": "Manage transportation, shipments, and carriers",
                "permissions": [
                    permissions["dashboard.view"],
                    permissions["tms.view"], permissions["tms.edit"], permissions["tms.create"],
                    permissions["tms.carrier.manage"],
                    permissions["oms.view"],
                    permissions["exceptions.view"], permissions["exceptions.resolve"],
                    permissions["reports.view"], permissions["reports.generate"],
                    permissions["analytics.view"],
                ]
            },
            {
                "name": "billing_manager",
                "display_name": "Billing Manager",
                "description": "Manage billing, invoices, and financial reports",
                "permissions": [
                    permissions["dashboard.view"],
                    permissions["billing.view"], permissions["billing.edit"], permissions["billing.approve"],
                    permissions["billing.export"],
                    permissions["oms.view"],
                    permissions["tms.view"],
                    permissions["reports.view"], permissions["reports.generate"], permissions["reports.export"],
                    permissions["analytics.view"],
                ]
            },
            {
                "name": "customer_service",
                "display_name": "Customer Service Representative",
                "description": "Handle customer inquiries, view orders and shipments",
                "permissions": [
                    permissions["dashboard.view"],
                    permissions["oms.view"],
                    permissions["tms.view"],
                    permissions["wms.view"],
                    permissions["returns.view"], permissions["returns.process"],
                    permissions["exceptions.view"], permissions["exceptions.assign"],
                    permissions["reports.view"],
                ]
            },
            {
                "name": "dock_supervisor",
                "display_name": "Dock Supervisor",
                "description": "Manage dock operations, receiving and shipping",
                "permissions": [
                    permissions["dashboard.view"],
                    permissions["yard.view"], permissions["yard.manage"],
                    permissions["wms.view"], permissions["wms.receiving"], permissions["wms.picking"],
                    permissions["tms.view"],
                    permissions["exceptions.view"],
                ]
            },
            {
                "name": "returns_manager",
                "display_name": "Returns Manager",
                "description": "Manage return processing and approvals",
                "permissions": [
                    permissions["dashboard.view"],
                    permissions["returns.view"], permissions["returns.process"], permissions["returns.approve"],
                    permissions["oms.view"],
                    permissions["wms.view"],
                    permissions["exceptions.view"], permissions["exceptions.resolve"],
                    permissions["reports.view"],
                ]
            },
            {
                "name": "analyst",
                "display_name": "Business Analyst",
                "description": "View-only access to analytics and reporting",
                "permissions": [
                    permissions["dashboard.view"],
                    permissions["wms.view"],
                    permissions["tms.view"],
                    permissions["oms.view"],
                    permissions["billing.view"],
                    permissions["returns.view"],
                    permissions["yard.view"],
                    permissions["exceptions.view"],
                    permissions["reports.view"], permissions["reports.generate"], permissions["reports.export"],
                    permissions["analytics.view"], permissions["analytics.advanced"],
                ]
            },
            {
                "name": "client_user",
                "display_name": "Client User",
                "description": "Limited access to own company's data",
                "permissions": [
                    permissions["dashboard.view"],
                    permissions["oms.view"],
                    permissions["tms.view"],
                    permissions["wms.view"],
                    permissions["billing.view"],
                    permissions["returns.view"],
                    permissions["reports.view"],
                ]
            },
        ]
        
        # Create roles
        for role_data in roles_data:
            role = Role(
                name=role_data["name"],
                display_name=role_data["display_name"],
                description=role_data["description"]
            )
            role.permissions = role_data["permissions"]
            session.add(role)
        
        session.flush()
        
        # Create default users
        admin_role = session.query(Role).filter(Role.name == "system_admin").first()
        ops_mgr_role = session.query(Role).filter(Role.name == "operations_manager").first()
        cs_role = session.query(Role).filter(Role.name == "customer_service").first()
        
        default_users = [
            {
                "username": "admin",
                "email": "admin@3pl-company.com",
                "full_name": "System Administrator",
                "password": "admin123",  # Change in production!
                "is_superuser": True,
                "roles": [admin_role]
            },
            {
                "username": "ops_manager",
                "email": "ops@3pl-company.com",
                "full_name": "Operations Manager",
                "password": "ops123",
                "department": "operations",
                "roles": [ops_mgr_role]
            },
            {
                "username": "cs_rep",
                "email": "cs@3pl-company.com",
                "full_name": "Customer Service Rep",
                "password": "cs123",
                "department": "customer_service",
                "roles": [cs_role]
            },
        ]
        
        for user_data in default_users:
            roles = user_data.pop("roles")
            password = user_data.pop("password")
            user = User(**user_data)
            user.hashed_password = User.hash_password(password)
            user.roles = roles
            session.add(user)
        
        session.commit()
        
        print("✓ Created", len(permissions_data), "permissions")
        print("✓ Created", len(roles_data), "roles")
        print("✓ Created", len(default_users), "default users")
        print("\nDefault users:")
        print("  - admin / admin123 (System Administrator)")
        print("  - ops_manager / ops123 (Operations Manager)")
        print("  - cs_rep / cs123 (Customer Service)")
        print("\n⚠ Remember to change default passwords in production!")
        
    except Exception as e:
        session.rollback()
        print(f"Error seeding auth data: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_auth_data()
