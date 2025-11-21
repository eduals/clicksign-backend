from flask import Blueprint, request, jsonify
from app.database import db
from app.models import FieldMapping
from app.auth import require_auth
import uuid

bp = Blueprint('field_mappings', __name__, url_prefix='/api/v1/field-mappings')

@bp.route('', methods=['GET'])
@require_auth
def list_field_mappings():
    """Listar mapeamentos de um portal"""
    try:
        portal_id = request.args.get('portal_id')
        object_type = request.args.get('object_type')  # Opcional
        
        if not portal_id:
            return jsonify({
                'error': 'portal_id is required'
            }), 400
        
        query = FieldMapping.query.filter_by(portal_id=portal_id)
        
        if object_type:
            query = query.filter_by(object_type=object_type)
        
        mappings = query.order_by(FieldMapping.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [mapping.to_dict() for mapping in mappings]
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@bp.route('', methods=['POST'])
@require_auth
def create_field_mapping():
    """Criar novo mapeamento"""
    try:
        data = request.get_json()
        
        required_fields = ['portal_id', 'object_type', 'clicksign_field_name', 
                          'clicksign_field_type', 'hubspot_property_name', 'hubspot_property_type']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'{field} is required'
                }), 400
        
        # Verificar se já existe mapeamento com mesmo campo ClickSign para o objeto
        existing = FieldMapping.query.filter_by(
            portal_id=data['portal_id'],
            object_type=data['object_type'],
            clicksign_field_name=data['clicksign_field_name']
        ).first()
        
        if existing:
            return jsonify({
                'error': 'Mapping already exists for this ClickSign field'
            }), 409
        
        mapping = FieldMapping(
            portal_id=data['portal_id'],
            object_type=data['object_type'],
            clicksign_field_name=data['clicksign_field_name'],
            clicksign_field_type=data['clicksign_field_type'],
            hubspot_property_name=data['hubspot_property_name'],
            hubspot_property_type=data['hubspot_property_type'],
            description=data.get('description'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(mapping)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': mapping.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@bp.route('/<mapping_id>', methods=['PATCH'])
@require_auth
def update_field_mapping(mapping_id):
    """Atualizar mapeamento"""
    try:
        mapping = FieldMapping.query.get(mapping_id)
        
        if not mapping:
            return jsonify({
                'error': 'Mapping not found'
            }), 404
        
        data = request.get_json()
        
        # Campos que podem ser atualizados
        updatable_fields = [
            'clicksign_field_name', 'clicksign_field_type',
            'hubspot_property_name', 'hubspot_property_type',
            'description', 'is_active'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(mapping, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': mapping.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@bp.route('/<mapping_id>', methods=['DELETE'])
@require_auth
def delete_field_mapping(mapping_id):
    """Deletar mapeamento"""
    try:
        mapping = FieldMapping.query.get(mapping_id)
        
        if not mapping:
            return jsonify({
                'error': 'Mapping not found'
            }), 404
        
        db.session.delete(mapping)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Mapping deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@bp.route('/<mapping_id>/toggle', methods=['PUT'])
@require_auth
def toggle_field_mapping(mapping_id):
    """Ativar/desativar mapeamento"""
    try:
        mapping = FieldMapping.query.get(mapping_id)
        
        if not mapping:
            return jsonify({
                'error': 'Mapping not found'
            }), 404
        
        mapping.is_active = not mapping.is_active
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': mapping.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

