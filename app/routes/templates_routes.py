from flask import Blueprint, request, jsonify
from app.auth import require_auth
from app.routes.google_drive_routes import get_google_credentials, list_templates as list_gdrive_templates
from googleapiclient.discovery import build
import requests

bp = Blueprint('templates', __name__, url_prefix='/api/v1/templates')

@bp.route('', methods=['GET'])
@require_auth
def list_all_templates():
    """Listar todos os templates disponíveis (ClickSign + Google Drive)"""
    try:
        portal_id = request.args.get('portal_id')
        
        if not portal_id:
            return jsonify({
                'error': 'portal_id is required'
            }), 400
        
        # Buscar templates do ClickSign
        clicksign_templates = []
        try:
            # TODO: Integrar com API do ClickSign para buscar templates
            # Por enquanto, retornar array vazio
            # clicksign_templates = await get_clicksign_templates(portal_id)
            pass
        except Exception as e:
            print(f"Error fetching ClickSign templates: {e}")
        
        # Buscar templates do Google Drive
        google_drive_templates = []
        try:
            creds = get_google_credentials(portal_id)
            if creds:
                service = build('drive', 'v3', credentials=creds)
                # Usar mesma lógica de list_templates
                from app.models import GoogleDriveConfig
                from app.database import db
                config = GoogleDriveConfig.query.filter_by(portal_id=portal_id).first()
                folder_id = config.templates_folder_id if config else None
                
                query = "trashed=false and (mimeType='application/pdf' or mimeType='application/vnd.google-apps.document')"
                if folder_id:
                    query += f" and '{folder_id}' in parents"
                
                results = service.files().list(
                    q=query,
                    fields="files(id, name, mimeType, modifiedTime)",
                    pageSize=100
                ).execute()
                
                google_drive_templates = results.get('files', [])
        except Exception as e:
            print(f"Error fetching Google Drive templates: {e}")
        
        return jsonify({
            'success': True,
            'data': {
                'clicksign_templates': clicksign_templates,
                'google_drive_templates': google_drive_templates
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

