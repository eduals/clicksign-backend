from typing import Dict, Any, Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from .tag_processor import TagProcessor
import logging

logger = logging.getLogger(__name__)

class GoogleDocsService:
    """
    Serviço para manipulação de Google Docs.
    Responsável por copiar templates e substituir tags.
    """
    
    def __init__(self, credentials: Credentials):
        self.docs_service = build('docs', 'v1', credentials=credentials)
        self.drive_service = build('drive', 'v3', credentials=credentials)
    
    def copy_template(self, template_id: str, new_name: str, folder_id: str = None) -> Dict:
        """
        Copia um template do Google Docs.
        
        Args:
            template_id: ID do documento template
            new_name: Nome do novo documento
            folder_id: ID da pasta de destino (opcional)
        
        Returns:
            Dict com id e url do novo documento
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
            'url': f"https://docs.google.com/document/d/{copied_file['id']}/edit"
        }
    
    def get_document_content(self, document_id: str) -> Dict:
        """Retorna o conteúdo completo do documento"""
        return self.docs_service.documents().get(documentId=document_id).execute()
    
    def extract_tags_from_document(self, document_id: str) -> list:
        """
        Extrai todas as tags {{...}} do documento.
        
        Returns:
            Lista de tags encontradas (sem as chaves)
        """
        doc = self.get_document_content(document_id)
        text = self._extract_text_from_content(doc.get('body', {}).get('content', []))
        return TagProcessor.extract_tags(text)
    
    def replace_tags_in_document(
        self, 
        document_id: str, 
        data: Dict[str, Any],
        mappings: Dict[str, str] = None
    ) -> None:
        """
        Substitui todas as tags no documento pelos valores correspondentes.
        
        Args:
            document_id: ID do documento
            data: Dados para substituição
            mappings: Mapeamento de tags para campos
        """
        doc = self.get_document_content(document_id)
        tags = self.extract_tags_from_document(document_id)
        
        requests = []
        
        for tag in tags:
            # Busca o campo mapeado ou usa o próprio tag
            field = mappings.get(tag, tag) if mappings else tag
            value = TagProcessor._get_nested_value(data, field)
            
            # Aplicar transformações se necessário (via mappings)
            # Por enquanto, apenas substitui o valor
            if value is None:
                value = ''
            else:
                value = str(value)
            
            requests.append({
                'replaceAllText': {
                    'containsText': {
                        'text': '{{' + tag + '}}',
                        'matchCase': True
                    },
                    'replaceText': value
                }
            })
        
        if requests:
            self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
    
    def export_as_pdf(self, document_id: str) -> bytes:
        """Exporta o documento como PDF"""
        return self.drive_service.files().export(
            fileId=document_id,
            mimeType='application/pdf'
        ).execute()
    
    def _extract_text_from_content(self, content: list) -> str:
        """Extrai texto puro do conteúdo do documento"""
        text_parts = []
        
        for element in content:
            if 'paragraph' in element:
                for elem in element['paragraph'].get('elements', []):
                    if 'textRun' in elem:
                        text_parts.append(elem['textRun'].get('content', ''))
            elif 'table' in element:
                for row in element['table'].get('tableRows', []):
                    for cell in row.get('tableCells', []):
                        text_parts.append(
                            self._extract_text_from_content(cell.get('content', []))
                        )
        
        return ''.join(text_parts)

