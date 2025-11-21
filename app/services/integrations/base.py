from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.models import GeneratedDocument, SignatureRequest

class BaseIntegration(ABC):
    """
    Interface base para integrações opcionais (ClickSign, DocuSign, etc.).
    """
    
    def __init__(self, organization_id: str):
        """
        Args:
            organization_id: ID da organização
        """
        self.organization_id = organization_id
    
    @abstractmethod
    def send_document_for_signature(
        self,
        document: GeneratedDocument,
        signers: List[Dict],
        message: str = None
    ) -> SignatureRequest:
        """
        Envia documento gerado para assinatura.
        
        Args:
            document: Documento gerado
            signers: Lista de signatários [{"email": "...", "name": "..."}]
            message: Mensagem opcional para os signatários
        
        Returns:
            SignatureRequest criado
        """
        pass
    
    @abstractmethod
    def get_signature_status(self, signature_request_id: str) -> Dict:
        """
        Consulta status de uma solicitação de assinatura.
        
        Args:
            signature_request_id: ID da solicitação
        
        Returns:
            Dict com status e informações
        """
        pass
    
    @abstractmethod
    def handle_webhook(self, payload: Dict) -> None:
        """
        Processa webhook do provider.
        
        Args:
            payload: Dados do webhook
        """
        pass

