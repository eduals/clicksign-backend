from flask import Blueprint, request, jsonify, g
from app.database import db
from app.models import Workflow, WorkflowFieldMapping, Template
from app.utils.auth import require_auth, require_org, require_admin
import logging

logger = logging.getLogger(__name__)
workflows_bp = Blueprint('workflows', __name__, url_prefix='/api/v1/workflows')


@workflows_bp.route('', methods=['GET'])
@require_auth
@require_org
def list_workflows():
    """Lista workflows da organização"""
    org_id = g.organization_id
    status = request.args.get('status')
    
    query = Workflow.query.filter_by(organization_id=org_id)
    
    if status:
        query = query.filter_by(status=status)
    
    workflows = query.order_by(Workflow.updated_at.desc()).all()
    
    return jsonify({
        'workflows': [workflow_to_dict(w) for w in workflows]
    })


@workflows_bp.route('/<workflow_id>', methods=['GET'])
@require_auth
@require_org
def get_workflow(workflow_id):
    """Retorna detalhes de um workflow"""
    workflow = Workflow.query.filter_by(
        id=workflow_id,
        organization_id=g.organization_id
    ).first_or_404()
    
    return jsonify(workflow_to_dict(workflow, include_mappings=True))


@workflows_bp.route('', methods=['POST'])
@require_auth
@require_org
@require_admin
def create_workflow():
    """
    Cria um novo workflow.
    
    Body:
    {
        "name": "Quote Generator",
        "description": "...",
        "source_connection_id": "uuid",
        "source_object_type": "deal",
        "template_id": "uuid",
        "output_folder_id": "google_drive_folder_id",
        "output_name_template": "{{company_name}} - Quote - {{date}}",
        "create_pdf": true,
        "trigger_type": "manual",
        "field_mappings": [
            {"template_tag": "company_name", "source_field": "associations.company.name"},
            {"template_tag": "deal_amount", "source_field": "amount", "transform_type": "currency"}
        ]
    }
    """
    data = request.get_json()
    
    # Validações
    required = ['name', 'template_id']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} é obrigatório'}), 400
    
    # Criar workflow
    workflow = Workflow(
        organization_id=g.organization_id,
        name=data['name'],
        description=data.get('description'),
        source_connection_id=data.get('source_connection_id'),
        source_object_type=data.get('source_object_type'),
        source_config=data.get('source_config'),
        template_id=data['template_id'],
        output_folder_id=data.get('output_folder_id'),
        output_name_template=data.get('output_name_template', '{{object_type}} - {{timestamp}}'),
        create_pdf=data.get('create_pdf', True),
        trigger_type=data.get('trigger_type', 'manual'),
        trigger_config=data.get('trigger_config'),
        post_actions=data.get('post_actions'),
        status='draft',
        created_by=data.get('user_id')
    )
    
    db.session.add(workflow)
    db.session.flush()  # Para obter o ID
    
    # Criar field mappings
    for mapping_data in data.get('field_mappings', []):
        mapping = WorkflowFieldMapping(
            workflow_id=workflow.id,
            template_tag=mapping_data['template_tag'],
            source_field=mapping_data['source_field'],
            transform_type=mapping_data.get('transform_type'),
            transform_config=mapping_data.get('transform_config'),
            default_value=mapping_data.get('default_value')
        )
        db.session.add(mapping)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'workflow': workflow_to_dict(workflow, include_mappings=True)
    }), 201


@workflows_bp.route('/<workflow_id>', methods=['PUT'])
@require_auth
@require_org
@require_admin
def update_workflow(workflow_id):
    """Atualiza um workflow"""
    workflow = Workflow.query.filter_by(
        id=workflow_id,
        organization_id=g.organization_id
    ).first_or_404()
    
    data = request.get_json()
    
    # Atualizar campos permitidos
    allowed_fields = [
        'name', 'description', 'source_connection_id', 'source_object_type',
        'source_config', 'template_id', 'output_folder_id', 'output_name_template',
        'create_pdf', 'trigger_type', 'trigger_config', 'post_actions', 'status'
    ]
    
    for field in allowed_fields:
        if field in data:
            setattr(workflow, field, data[field])
    
    # Atualizar field mappings se fornecidos
    if 'field_mappings' in data:
        # Remove mapeamentos existentes
        WorkflowFieldMapping.query.filter_by(workflow_id=workflow.id).delete()
        
        # Cria novos
        for mapping_data in data['field_mappings']:
            mapping = WorkflowFieldMapping(
                workflow_id=workflow.id,
                template_tag=mapping_data['template_tag'],
                source_field=mapping_data['source_field'],
                transform_type=mapping_data.get('transform_type'),
                transform_config=mapping_data.get('transform_config'),
                default_value=mapping_data.get('default_value')
            )
            db.session.add(mapping)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'workflow': workflow_to_dict(workflow, include_mappings=True)
    })


@workflows_bp.route('/<workflow_id>', methods=['DELETE'])
@require_auth
@require_org
@require_admin
def delete_workflow(workflow_id):
    """Deleta um workflow"""
    workflow = Workflow.query.filter_by(
        id=workflow_id,
        organization_id=g.organization_id
    ).first_or_404()
    
    db.session.delete(workflow)
    db.session.commit()
    
    return jsonify({'success': True})


@workflows_bp.route('/<workflow_id>/activate', methods=['POST'])
@require_auth
@require_org
@require_admin
def activate_workflow(workflow_id):
    """Ativa um workflow"""
    workflow = Workflow.query.filter_by(
        id=workflow_id,
        organization_id=g.organization_id
    ).first_or_404()
    
    # Validar que workflow está completo
    if not workflow.template_id:
        return jsonify({'error': 'Template não configurado'}), 400
    
    workflow.status = 'active'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'workflow': workflow_to_dict(workflow)
    })


def workflow_to_dict(workflow: Workflow, include_mappings: bool = False) -> dict:
    """Converte workflow para dicionário"""
    result = {
        'id': str(workflow.id),
        'name': workflow.name,
        'description': workflow.description,
        'status': workflow.status,
        'source_connection_id': str(workflow.source_connection_id) if workflow.source_connection_id else None,
        'source_object_type': workflow.source_object_type,
        'template_id': str(workflow.template_id) if workflow.template_id else None,
        'output_folder_id': workflow.output_folder_id,
        'output_name_template': workflow.output_name_template,
        'create_pdf': workflow.create_pdf,
        'trigger_type': workflow.trigger_type,
        'post_actions': workflow.post_actions,
        'created_at': workflow.created_at.isoformat(),
        'updated_at': workflow.updated_at.isoformat()
    }
    
    if include_mappings:
        result['field_mappings'] = [
            {
                'id': str(m.id),
                'template_tag': m.template_tag,
                'source_field': m.source_field,
                'transform_type': m.transform_type,
                'transform_config': m.transform_config,
                'default_value': m.default_value
            }
            for m in workflow.field_mappings
        ]
    
    # Incluir info do template se disponível
    if workflow.template:
        result['template'] = {
            'id': str(workflow.template.id),
            'name': workflow.template.name,
            'google_file_type': workflow.template.google_file_type,
            'thumbnail_url': workflow.template.thumbnail_url
        }
    
    return result

