"""
Serviço para manipulação de Google Slides.
Similar ao GoogleDocsService, mas para apresentações.
"""
from typing import Dict, Any, Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from .tag_processor import TagProcessor
import logging

logger = logging.getLogger(__name__)


class GoogleSlidesService:
    """
    Serviço para manipulação de Google Slides.
    """
    
    def __init__(self, credentials: Credentials):
        self.slides_service = build('slides', 'v1', credentials=credentials)
        self.drive_service = build('drive', 'v3', credentials=credentials)
    
    def copy_template(self, template_id: str, new_name: str, folder_id: str = None) -> Dict:
        """
        Copia um template do Google Slides.
        
        Args:
            template_id: ID da apresentação template
            new_name: Nome da nova apresentação
            folder_id: ID da pasta de destino (opcional)
        
        Returns:
            Dict com id e url da nova apresentação
        """
        body = {'name': new_name}
        
        if folder_id:
            body['parents'] = [folder_id]
        
        copied_file = self.drive_service.files().copy(
            fileId=template_id,
            body=body,
            supportsAllDrives=True
        ).execute()
        
        return {
            'id': copied_file['id'],
            'url': f"https://docs.google.com/presentation/d/{copied_file['id']}/edit"
        }
    
    def get_presentation_content(self, presentation_id: str) -> Dict:
        """Retorna o conteúdo completo da apresentação"""
        return self.slides_service.presentations().get(presentationId=presentation_id).execute()
    
    def extract_tags_from_presentation(self, presentation_id: str) -> list:
        """
        Extrai todas as tags {{...}} da apresentação.
        
        Returns:
            Lista de tags encontradas (sem as chaves)
        """
        presentation = self.get_presentation_content(presentation_id)
        text = self._extract_text_from_presentation(presentation)
        return TagProcessor.extract_tags(text)
    
    def replace_tags_in_presentation(
        self,
        presentation_id: str,
        data: Dict[str, Any],
        mappings: Dict[str, str] = None
    ) -> None:
        """
        Substitui todas as tags na apresentação pelos valores correspondentes.
        
        Args:
            presentation_id: ID da apresentação
            data: Dados para substituição
            mappings: Mapeamento de tags para campos
        """
        presentation = self.get_presentation_content(presentation_id)
        requests = []
        
        # Processar cada slide
        for slide in presentation.get('slides', []):
            slide_id = slide.get('objectId')
            
            # Processar shapes (textos, imagens, etc.)
            for page_element in slide.get('pageElements', []):
                shape = page_element.get('shape', {})
                if not shape:
                    continue
                
                # Processar textos no shape
                text_elements = shape.get('text', {}).get('textElements', [])
                for text_element in text_elements:
                    text_run = text_element.get('textRun', {})
                    if not text_run:
                        continue
                    
                    text_content = text_run.get('content', '')
                    tags = TagProcessor.extract_tags(text_content)
                    
                    for tag in tags:
                        field = mappings.get(tag, tag) if mappings else tag
                        value = TagProcessor._get_nested_value(data, field)
                        
                        if value is not None:
                            new_text = text_content.replace(f'{{{{{tag}}}}}', str(value))
                            
                            # Criar request para substituir texto
                            # Nota: Google Slides API requer substituição por índice
                            # Por simplicidade, substituiremos todo o texto do elemento
                            requests.append({
                                'deleteText': {
                                    'objectId': page_element.get('objectId'),
                                    'textRange': {
                                        'startIndex': 0,
                                        'endIndex': len(text_content)
                                    }
                                }
                            })
                            
                            requests.append({
                                'insertText': {
                                    'objectId': page_element.get('objectId'),
                                    'text': new_text,
                                    'insertionIndex': 0
                                }
                            })
        
        # Processar tags AI
        ai_tags = TagProcessor.extract_ai_tags(self._extract_text_from_presentation(presentation))
        for ai_tag in ai_tags:
            tag_key = f'ai:{ai_tag}'
            value = data.get(tag_key) or data.get(ai_tag, '')
            value = str(value) if value is not None else ''
            
            # Substituir em toda a apresentação
            requests.append({
                'replaceAllText': {
                    'containsText': {
                        'text': f'{{{{ai:{ai_tag}}}}}',
                        'matchCase': True
                    },
                    'replaceText': value
                }
            })
        
        if requests:
            self.slides_service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={'requests': requests}
            ).execute()
    
    def export_as_pdf(self, presentation_id: str) -> bytes:
        """Exporta a apresentação como PDF"""
        return self.drive_service.files().export(
            fileId=presentation_id,
            mimeType='application/pdf'
        ).execute()
    
    def _extract_text_from_presentation(self, presentation: Dict) -> str:
        """Extrai texto puro da apresentação"""
        text_parts = []
        
        for slide in presentation.get('slides', []):
            for page_element in slide.get('pageElements', []):
                shape = page_element.get('shape', {})
                if shape:
                    text_elements = shape.get('text', {}).get('textElements', [])
                    for text_element in text_elements:
                        text_run = text_element.get('textRun', {})
                        if text_run:
                            text_parts.append(text_run.get('content', ''))
        
        return ''.join(text_parts)

