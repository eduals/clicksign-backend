import re
from typing import Dict, List, Any, Optional

class TagProcessor:
    """
    Processa tags no formato {{tag_name}} em templates.
    
    Formatos suportados:
    - {{property_name}} - propriedade simples
    - {{object.property}} - propriedade de objeto relacionado
    - {{line_items}} - marcador para tabela de line items
    - {{=SUM(...)}} - fórmulas (para Sheets)
    """
    
    TAG_PATTERN = r'\{\{([^}]+)\}\}'
    
    @classmethod
    def extract_tags(cls, text: str) -> List[str]:
        """Extrai todas as tags de um texto"""
        matches = re.findall(cls.TAG_PATTERN, text)
        return list(set(matches))
    
    @classmethod
    def replace_tags(cls, text: str, data: Dict[str, Any], mappings: Dict[str, str] = None) -> str:
        """
        Substitui tags no texto pelos valores correspondentes.
        
        Args:
            text: Texto com tags {{...}}
            data: Dicionário com os dados
            mappings: Mapeamento opcional de tag -> campo no data
        
        Returns:
            Texto com tags substituídas
        """
        def replace_match(match):
            tag = match.group(1).strip()
            
            # Se tem mapeamento, usa o campo mapeado
            field = mappings.get(tag, tag) if mappings else tag
            
            # Busca o valor (suporta dot notation: "contact.firstname")
            value = cls._get_nested_value(data, field)
            
            if value is None:
                return ''  # ou match.group(0) para manter a tag
            
            return str(value)
        
        return re.sub(cls.TAG_PATTERN, replace_match, text)
    
    @classmethod
    def _get_nested_value(cls, data: Dict, path: str) -> Any:
        """
        Busca valor em dicionário usando dot notation.
        Ex: "contact.firstname" -> data['contact']['firstname']
        """
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
            
            if value is None:
                return None
        
        return value
    
    @classmethod
    def apply_transform(cls, value: Any, transform_type: str, config: Dict = None) -> str:
        """
        Aplica transformação ao valor.
        
        Transform types:
        - date_format: Formata data
        - number_format: Formata número
        - currency: Formata como moeda
        - uppercase: Converte para maiúsculas
        - lowercase: Converte para minúsculas
        - capitalize: Primeira letra maiúscula
        """
        if value is None:
            return ''
        
        config = config or {}
        
        if transform_type == 'uppercase':
            return str(value).upper()
        
        elif transform_type == 'lowercase':
            return str(value).lower()
        
        elif transform_type == 'capitalize':
            return str(value).capitalize()
        
        elif transform_type == 'date_format':
            from datetime import datetime
            fmt = config.get('format', '%d/%m/%Y')
            if isinstance(value, str):
                # Tenta parsear ISO format
                try:
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return dt.strftime(fmt)
                except:
                    return value
            elif isinstance(value, datetime):
                return value.strftime(fmt)
            return str(value)
        
        elif transform_type == 'number_format':
            try:
                num = float(value)
                decimals = config.get('decimals', 2)
                return f"{num:,.{decimals}f}"
            except:
                return str(value)
        
        elif transform_type == 'currency':
            try:
                num = float(value)
                symbol = config.get('symbol', 'R$')
                decimals = config.get('decimals', 2)
                return f"{symbol} {num:,.{decimals}f}"
            except:
                return str(value)
        
        return str(value)

