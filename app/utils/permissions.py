from app.models import User, Organization
from app.database import db

def check_permission(user: User, permission: str) -> bool:
    """
    Verifica se usuário tem permissão específica.
    
    Args:
        user: Usuário
        permission: Nome da permissão (create_workflow, create_template, etc.)
    
    Returns:
        True se tem permissão, False caso contrário
    """
    if not user:
        return False
    
    # Admins têm todas as permissões
    if user.is_admin():
        return True
    
    # Permissões específicas por role
    permission_map = {
        'create_workflow': ['admin'],
        'create_template': ['admin'],
        'edit_workflow': ['admin'],
        'delete_workflow': ['admin'],
        'execute_workflow': ['admin', 'user'],
        'view_documents': ['admin', 'user']
    }
    
    allowed_roles = permission_map.get(permission, [])
    return user.role in allowed_roles


def get_user_organization(user_id: str) -> Organization:
    """
    Obtém organização do usuário.
    
    Args:
        user_id: ID do usuário
    
    Returns:
        Organization do usuário
    """
    user = User.query.filter_by(id=user_id).first_or_404()
    return user.organization

