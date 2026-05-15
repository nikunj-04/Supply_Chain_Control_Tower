"""Authentication and Authorization Service."""
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from models.auth_models import User, Role, Permission, UserSession, AuditLog, get_auth_session
from logger import setup_logger

logger = setup_logger(__name__)


class AuthService:
    """Service for handling authentication and authorization."""
    
    def __init__(self):
        self.session = get_auth_session()
        self.token_expiry_hours = 8  # 8 hours for access token
        self.refresh_expiry_days = 30  # 30 days for refresh token
    
    def authenticate(self, username: str, password: str, ip_address: str = None, user_agent: str = None) -> Optional[Dict]:
        """Authenticate user and create session."""
        try:
            user = self.session.query(User).filter(User.username == username, User.is_active == True).first()
            
            if not user or not user.verify_password(password):
                self.log_audit(
                    username=username,
                    action="login_failed",
                    ip_address=ip_address,
                    success=False,
                    error_message="Invalid credentials"
                )
                return None
            
            # Create session
            session = UserSession(
                user_id=user.id,
                token=UserSession.generate_token(),
                refresh_token=UserSession.generate_token(),
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=datetime.utcnow() + timedelta(hours=self.token_expiry_hours)
            )
            
            self.session.add(session)
            user.last_login = datetime.utcnow()
            self.session.commit()
            
            self.log_audit(
                user_id=user.id,
                username=user.username,
                action="login",
                ip_address=ip_address,
                success=True
            )
            
            return {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_superuser": user.is_superuser,
                    "client_id": user.client_id,
                    "department": user.department,
                    "roles": [{"id": r.id, "name": r.name, "display_name": r.display_name} for r in user.roles],
                    "permissions": self.get_user_permissions(user)
                },
                "token": session.token,
                "refresh_token": session.refresh_token,
                "expires_at": session.expires_at.isoformat()
            }
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"Authentication error: {e}")
            return None
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate token and return user info."""
        try:
            session = self.session.query(UserSession).filter(
                UserSession.token == token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            ).first()
            
            if not session:
                return None
            
            # Update last activity
            session.last_activity = datetime.utcnow()
            self.session.commit()
            
            user = session.user
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_superuser": user.is_superuser,
                "client_id": user.client_id,
                "department": user.department,
                "roles": [r.name for r in user.roles],
                "permissions": self.get_user_permissions(user)
            }
        
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None
    
    def refresh_session(self, refresh_token: str) -> Optional[Dict]:
        """Refresh an expired session using refresh token."""
        try:
            session = self.session.query(UserSession).filter(
                UserSession.refresh_token == refresh_token,
                UserSession.is_active == True
            ).first()
            
            if not session:
                return None
            
            # Generate new tokens
            session.token = UserSession.generate_token()
            session.refresh_token = UserSession.generate_token()
            session.expires_at = datetime.utcnow() + timedelta(hours=self.token_expiry_hours)
            session.last_activity = datetime.utcnow()
            
            self.session.commit()
            
            user = session.user
            return {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name
                },
                "token": session.token,
                "refresh_token": session.refresh_token,
                "expires_at": session.expires_at.isoformat()
            }
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"Session refresh error: {e}")
            return None
    
    def logout(self, token: str, ip_address: str = None) -> bool:
        """Logout user and invalidate session."""
        try:
            session = self.session.query(UserSession).filter(UserSession.token == token).first()
            
            if session:
                username = session.user.username
                session.is_active = False
                self.session.commit()
                
                self.log_audit(
                    user_id=session.user_id,
                    username=username,
                    action="logout",
                    ip_address=ip_address,
                    success=True
                )
                
                return True
            
            return False
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"Logout error: {e}")
            return False
    
    def get_user_permissions(self, user: User) -> List[str]:
        """Get all permissions for a user."""
        if user.is_superuser:
            return ["*"]  # Superuser has all permissions
        
        permissions = set()
        for role in user.roles:
            for perm in role.permissions:
                permissions.add(perm.name)
        
        return sorted(list(permissions))
    
    def check_permission(self, user_id: int, permission: str) -> bool:
        """Check if user has a specific permission."""
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            return user.has_permission(permission) if user else False
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return False
    
    def log_audit(self, username: str, action: str, user_id: int = None, resource_type: str = None,
                  resource_id: str = None, details: str = None, ip_address: str = None,
                  success: bool = True, error_message: str = None):
        """Log user action to audit log."""
        try:
            audit = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                success=success,
                error_message=error_message
            )
            self.session.add(audit)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f"Audit log error: {e}")
    
    def get_audit_logs(self, username: str = None, action: str = None, 
                       resource_type: str = None, success: bool = None,
                       limit: int = 100, offset: int = 0):
        """Get audit logs with optional filtering."""
        try:
            query = self.session.query(AuditLog)
            
            if username:
                query = query.filter(AuditLog.username.like(f"%{username}%"))
            if action:
                query = query.filter(AuditLog.action == action)
            if resource_type:
                query = query.filter(AuditLog.resource_type == resource_type)
            if success is not None:
                query = query.filter(AuditLog.success == success)
            
            total = query.count()
            logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset).all()
            
            return {
                "total": total,
                "logs": [{
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat(),
                    "user_id": log.user_id,
                    "username": log.username,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "details": log.details,
                    "ip_address": log.ip_address,
                    "success": log.success,
                    "error_message": log.error_message
                } for log in logs]
            }
        except Exception as e:
            logger.error(f"Error fetching audit logs: {e}")
            return {"total": 0, "logs": []}
    
    def create_user(self, username: str, email: str, full_name: str, password: str,
                   role_names: List[str], client_id: str = None, department: str = None) -> Optional[User]:
        """Create a new user."""
        try:
            # Check if username or email already exists
            existing = self.session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing:
                return None
            
            # Get roles
            roles = self.session.query(Role).filter(Role.name.in_(role_names)).all()
            
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                hashed_password=User.hash_password(password),
                client_id=client_id,
                department=department,
                roles=roles
            )
            
            self.session.add(user)
            self.session.commit()
            
            logger.info(f"User created: {username}")
            return user
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"User creation error: {e}")
            return None
    
    def get_all_roles(self) -> List[Dict]:
        """Get all roles with their permissions."""
        roles = self.session.query(Role).filter(Role.is_active == True).all()
        return [{
            "id": r.id,
            "name": r.name,
            "display_name": r.display_name,
            "description": r.description,
            "permissions": [{"id": p.id, "name": p.name, "display_name": p.display_name} for p in r.permissions]
        } for r in roles]
    
    def get_all_permissions(self) -> List[Dict]:
        """Get all permissions grouped by module."""
        permissions = self.session.query(Permission).all()
        return [{
            "id": p.id,
            "name": p.name,
            "display_name": p.display_name,
            "description": p.description,
            "module": p.module,
            "action": p.action
        } for p in permissions]
    
    def get_all_users(self) -> List[Dict]:
        """Get all users with their roles (admin only)."""
        users = self.session.query(User).all()
        return [{
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name,
            "email": u.email,
            "is_active": u.is_active,
            "is_superuser": u.is_superuser,
            "client_id": u.client_id,
            "department": u.department,
            "last_login": u.last_login.isoformat() if u.last_login else None,
            "created_at": u.created_at.isoformat(),
            "roles": [{"id": r.id, "name": r.name, "display_name": r.display_name} for r in u.roles]
        } for u in users]
    
    def update_user(self, user_id: int, full_name: str = None, email: str = None, 
                   password: str = None, role_id: int = None, is_active: bool = None) -> Optional[Dict]:
        """Update user details (admin only)."""
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User with id {user_id} not found")
            
            if full_name:
                user.full_name = full_name
            if email:
                user.email = email
            if password:
                user.password_hash = User.hash_password(password)
            if is_active is not None:
                user.is_active = is_active
            if role_id:
                role = self.session.query(Role).filter(Role.id == role_id).first()
                if not role:
                    raise ValueError(f"Role with id {role_id} not found")
                user.roles = [role]
            
            self.session.commit()
            logger.info(f"User updated: {user.username}")
            
            return {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email,
                "is_active": user.is_active,
                "roles": [{"id": r.id, "name": r.name, "display_name": r.display_name} for r in user.roles]
            }
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"User update error: {e}")
            raise
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user (admin only)."""
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User with id {user_id} not found")
            
            # Deactivate sessions
            self.session.query(UserSession).filter(UserSession.user_id == user_id).update({"is_active": False})
            
            # Delete user
            self.session.delete(user)
            self.session.commit()
            
            logger.info(f"User deleted: {user.username}")
            return True
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"User deletion error: {e}")
            raise


# Singleton instance
auth_service = AuthService()
