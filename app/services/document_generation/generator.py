from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.database import db
from app.models import (
    Workflow, GeneratedDocument, Template, 
    WorkflowFieldMapping, Organization, WorkflowExecution
)
from .google_docs import GoogleDocsService
from .tag_processor import TagProcessor

logger = logging.getLogger(__name__)

class DocumentGenerator:
    """
    Orquestrador principal de geração de documentos.
    Coordena a busca de dados, processamento de template e geração do documento.
    """
    
    def __init__(self, google_credentials):
        self.google_docs = GoogleDocsService(google_credentials)
    
    def generate_from_workflow(
        self,
        workflow: Workflow,
        source_data: Dict[str, Any],
        source_object_id: str,
        user_id: str = None
    ) -> GeneratedDocument:
        """
        Gera um documento a partir de um workflow configurado.
        
        Args:
            workflow: Workflow com configurações
            source_data: Dados da fonte (já buscados)
            source_object_id: ID do objeto na fonte
            user_id: ID do usuário que está gerando
        
        Returns:
            GeneratedDocument criado
        """
        execution = None
        
        try:
            # Criar registro de execução
            execution = WorkflowExecution(
                workflow_id=workflow.id,
                trigger_type='manual',
                trigger_data={'source_object_id': source_object_id},
                status='running'
            )
            db.session.add(execution)
            db.session.commit()
            
            start_time = datetime.utcnow()
            
            # Verificar quota da organização
            org = workflow.organization
            if not org.can_generate_document():
                raise Exception('Limite de documentos atingido para este período')
            
            # Buscar template
            template = workflow.template
            if not template:
                raise Exception('Template não configurado no workflow')
            
            # Buscar mapeamentos
            mappings = {
                m.template_tag: m.source_field 
                for m in workflow.field_mappings
            }
            
            # Gerar nome do documento
            doc_name = self._generate_document_name(
                workflow.output_name_template,
                source_data,
                workflow.source_object_type
            )
            
            # Copiar template
            new_doc = self.google_docs.copy_template(
                template_id=template.google_file_id,
                new_name=doc_name,
                folder_id=workflow.output_folder_id
            )
            
            # Substituir tags
            self.google_docs.replace_tags_in_document(
                document_id=new_doc['id'],
                data=source_data,
                mappings=mappings
            )
            
            # Criar registro do documento gerado
            generated_doc = GeneratedDocument(
                organization_id=workflow.organization_id,
                workflow_id=workflow.id,
                source_connection_id=workflow.source_connection_id,
                source_object_type=workflow.source_object_type,
                source_object_id=source_object_id,
                template_id=template.id,
                template_version=template.version,
                name=doc_name,
                google_doc_id=new_doc['id'],
                google_doc_url=new_doc['url'],
                status='generated',
                generated_data=source_data,
                generated_by=user_id,
                generated_at=datetime.utcnow()
            )
            
            # Gerar PDF se configurado
            if workflow.create_pdf:
                pdf_bytes = self.google_docs.export_as_pdf(new_doc['id'])
                pdf_result = self._upload_pdf(
                    pdf_bytes, 
                    f"{doc_name}.pdf",
                    workflow.output_folder_id
                )
                generated_doc.pdf_file_id = pdf_result['id']
                generated_doc.pdf_url = pdf_result['url']
            
            db.session.add(generated_doc)
            
            # Incrementar contador da organização
            org.increment_document_count()
            
            # Atualizar execução
            end_time = datetime.utcnow()
            execution.status = 'completed'
            execution.completed_at = end_time
            execution.execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            execution.generated_document_id = generated_doc.id
            
            db.session.commit()
            
            logger.info(f"Documento gerado com sucesso: {generated_doc.id}")
            return generated_doc
            
        except Exception as e:
            logger.error(f"Erro ao gerar documento: {str(e)}")
            
            if execution:
                execution.status = 'failed'
                execution.error_message = str(e)
                execution.completed_at = datetime.utcnow()
                db.session.commit()
            
            raise
    
    def _generate_document_name(
        self, 
        template: str, 
        data: Dict, 
        object_type: str
    ) -> str:
        """
        Gera o nome do documento baseado no template de nomeação.
        
        Template suporta tags como:
        - {{company_name}}
        - {{date}} - data atual
        - {{timestamp}} - timestamp atual
        - {{object_type}} - tipo do objeto
        """
        if not template:
            template = "{{object_type}} - {{timestamp}}"
        
        # Adiciona campos especiais
        data_with_meta = {
            **data,
            'date': datetime.utcnow().strftime('%Y-%m-%d'),
            'timestamp': datetime.utcnow().strftime('%Y%m%d_%H%M%S'),
            'object_type': object_type
        }
        
        return TagProcessor.replace_tags(template, data_with_meta)
    
    def _upload_pdf(self, pdf_bytes: bytes, name: str, folder_id: str) -> Dict:
        """Upload do PDF para o Google Drive"""
        from googleapiclient.http import MediaInMemoryUpload
        
        media = MediaInMemoryUpload(pdf_bytes, mimetype='application/pdf')
        
        file_metadata = {
            'name': name,
            'mimeType': 'application/pdf'
        }
        
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        file = self.google_docs.drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        return {
            'id': file['id'],
            'url': file.get('webViewLink', f"https://drive.google.com/file/d/{file['id']}/view")
        }

