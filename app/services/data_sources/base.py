from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseDataSource(ABC):
    """
    Interface base para conectores de fontes de dados.
    Cada fonte (HubSpot, Google Forms, etc.) deve implementar esta interface.
    """
    
    def __init__(self, connection):
        """
        Args:
            connection: DataSourceConnection com credenciais e config
        """
        self.connection = connection
    
    @abstractmethod
    def get_object_data(self, object_type: str, object_id: str) -> Dict[str, Any]:
        """
        Busca dados de um objeto específico da fonte.
        
        Args:
            object_type: Tipo do objeto (contact, deal, company, etc.)
            object_id: ID do objeto na fonte
        
        Returns:
            Dict com os dados do objeto
        """
        pass
    
    @abstractmethod
    def list_objects(self, object_type: str, filters: Dict = None) -> list:
        """
        Lista objetos da fonte.
        
        Args:
            object_type: Tipo do objeto
            filters: Filtros opcionais
        
        Returns:
            Lista de objetos
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Testa se a conexão está funcionando.
        
        Returns:
            True se conexão OK, False caso contrário
        """
        pass

