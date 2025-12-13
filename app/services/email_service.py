"""
Serviço para envio de emails via SMTP (Gmail) e Microsoft Graph API (Outlook).
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    """
    Serviço para envio de emails.
    Suporta Gmail SMTP e Outlook via Microsoft Graph API.
    """
    
    @staticmethod
    def send_via_smtp(
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        use_tls: bool,
        to: List[str],
        subject: str,
        body: str,
        body_type: str = 'html',
        cc: List[str] = None,
        bcc: List[str] = None,
        attachments: List[Dict[str, Any]] = None
    ) -> bool:
        """
        Envia email via SMTP (Gmail).
        
        Args:
            smtp_host: Host SMTP (ex: smtp.gmail.com)
            smtp_port: Porta SMTP (ex: 587)
            username: Email do remetente
            password: Senha ou App Password
            use_tls: Se True, usa TLS
            to: Lista de destinatários
            subject: Assunto do email
            body: Corpo do email (HTML ou texto)
            body_type: 'html' ou 'text'
            cc: Lista de CC (opcional)
            bcc: Lista de BCC (opcional)
            attachments: Lista de anexos [{'filename': '...', 'content': bytes, 'content_type': '...'}]
        
        Returns:
            True se enviado com sucesso
        """
        try:
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['From'] = username
            msg['To'] = ', '.join(to)
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Adicionar corpo
            if body_type == 'html':
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Adicionar anexos
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Conectar e enviar
            server = smtplib.SMTP(smtp_host, smtp_port)
            if use_tls:
                server.starttls()
            server.login(username, password)
            
            recipients = to.copy()
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            server.sendmail(username, recipients, msg.as_string())
            server.quit()
            
            logger.info(f'Email enviado via SMTP para {to}')
            return True
            
        except Exception as e:
            logger.exception(f'Erro ao enviar email via SMTP: {str(e)}')
            raise
    
    @staticmethod
    def send_via_graph_api(
        access_token: str,
        from_email: str,
        to: List[str],
        subject: str,
        body: str,
        body_type: str = 'html',
        cc: List[str] = None,
        bcc: List[str] = None,
        attachments: List[Dict[str, Any]] = None
    ) -> bool:
        """
        Envia email via Microsoft Graph API (Outlook).
        
        Args:
            access_token: Access token do Microsoft Graph API
            from_email: Email do remetente
            to: Lista de destinatários
            subject: Assunto do email
            body: Corpo do email (HTML ou texto)
            body_type: 'html' ou 'text'
            cc: Lista de CC (opcional)
            bcc: Lista de BCC (opcional)
            attachments: Lista de anexos [{'filename': '...', 'content': bytes, 'content_type': '...'}]
        
        Returns:
            True se enviado com sucesso
        """
        try:
            base_url = 'https://graph.microsoft.com/v1.0'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Construir payload
            message = {
                'message': {
                    'subject': subject,
                    'body': {
                        'contentType': 'html' if body_type == 'html' else 'text',
                        'content': body
                    },
                    'toRecipients': [{'emailAddress': {'address': email}} for email in to]
                },
                'saveToSentItems': True
            }
            
            if cc:
                message['message']['ccRecipients'] = [{'emailAddress': {'address': email}} for email in cc]
            
            if bcc:
                message['message']['bccRecipients'] = [{'emailAddress': {'address': email}} for email in bcc]
            
            # Adicionar anexos se houver
            if attachments:
                attachments_data = []
                for attachment in attachments:
                    import base64
                    attachments_data.append({
                        '@odata.type': '#microsoft.graph.fileAttachment',
                        'name': attachment['filename'],
                        'contentType': attachment.get('content_type', 'application/octet-stream'),
                        'contentBytes': base64.b64encode(attachment['content']).decode('utf-8')
                    })
                message['message']['attachments'] = attachments_data
            
            # Enviar email
            response = requests.post(
                f'{base_url}/users/{from_email}/sendMail',
                headers=headers,
                json=message
            )
            response.raise_for_status()
            
            logger.info(f'Email enviado via Graph API para {to}')
            return True
            
        except Exception as e:
            logger.exception(f'Erro ao enviar email via Graph API: {str(e)}')
            raise

