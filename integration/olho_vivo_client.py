"""
Cliente para API Olho Vivo da SPTrans
Fornece dados em tempo real de transporte público de São Paulo
"""
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class OlhoVivoClient:
    """Cliente para API Olho Vivo da SPTrans"""
    
    BASE_URL = "https://api.olhovivo.sptrans.com.br/v2.1"
    
    def __init__(self, token: str):
        """
        Inicializa o cliente com token de autenticação
        
        Args:
            token: Token de acesso da API Olho Vivo
        """
        # Limpar token (remover espaços e caracteres invisíveis)
        self.token = token.strip() if token else ""
        
        # Validar token
        if not self.token:
            raise ValueError("Token não pode ser vazio")
        
        self.session = requests.Session()
        
        # Configurar headers padrão para a API Olho Vivo
        # Nota: Não incluir Content-Type para POST com query string, pode causar problemas
        # Algumas APIs validam User-Agent e outros headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Origin': 'https://www.sptrans.com.br',
            'Referer': 'https://www.sptrans.com.br/desenvolvedores/'
        })
        
        self.authenticated = False
    
    def authenticate(self) -> bool:
        """
        Autentica na API Olho Vivo
        
        Conforme documentação: POST /Login/Autenticar?token={token}
        Retorna true se sucesso, false se erro
        
        Returns:
            True se autenticação bem-sucedida, False caso contrário
        """
        try:
            url = f"{self.BASE_URL}/Login/Autenticar"
            
            # Log detalhado para debug
            logger.info(f"🔐 Tentando autenticar na API Olho Vivo")
            logger.info(f"   URL: {url}")
            logger.info(f"   Token (primeiros 20 chars): {self.token[:20]}...")
            logger.info(f"   Token completo (últimos 10 chars): ...{self.token[-10:]}")
            logger.info(f"   Token length: {len(self.token)}")
            logger.info(f"   Token repr: {repr(self.token)}")  # Mostra caracteres invisíveis
            
            # Limpar token novamente (garantir que não há espaços)
            clean_token = self.token.strip()
            if clean_token != self.token:
                logger.warning(f"   ⚠️ Token tinha espaços! Limpando...")
                self.token = clean_token
            
            # Tentar diferentes métodos de envio do token
            # Método 1: Token na query string (conforme documentação)
            params = {"token": self.token}
            url_with_token = f"{url}?token={self.token}"
            
            logger.info(f"   Tentando método 1: POST com token na query string")
            logger.info(f"   URL completa: {url_with_token}")
            logger.info(f"   Headers enviados: {dict(self.session.headers)}")
            
            # Fazer requisição POST
            # Nota: Algumas APIs podem ter problemas com params no POST, então vamos tentar direto na URL também
            try:
                response = self.session.post(url_with_token, timeout=10, allow_redirects=True)
            except Exception as e1:
                logger.warning(f"   Erro com URL direta, tentando com params: {e1}")
                response = self.session.post(url, params=params, timeout=10, allow_redirects=True)
            
            # Log detalhado da resposta
            logger.info(f"   Status code: {response.status_code}")
            logger.info(f"   Response text: {response.text}")
            logger.info(f"   Response headers: {dict(response.headers)}")
            logger.info(f"   Request URL final: {response.url}")
            logger.info(f"   Request headers enviados: {dict(response.request.headers)}")
            
            # Verificar se houve redirecionamento
            if response.history:
                logger.info(f"   ⚠️ Houve redirecionamento: {len(response.history)} redirect(s)")
                for i, hist in enumerate(response.history):
                    logger.info(f"      Redirect {i+1}: {hist.status_code} -> {hist.url}")
            
            response.raise_for_status()
            
            # A API retorna um boolean (true/false) como JSON
            # Mas pode retornar como string "true"/"false" ou boolean
            try:
                result = response.json()
                logger.info(f"   Response JSON: {result} (tipo: {type(result).__name__})")
            except ValueError:
                # Se não for JSON, verificar texto puro
                text = response.text.strip()
                logger.warning(f"   Resposta não é JSON válido: '{text}'")
                self.authenticated = text.lower() == "true"
            else:
                # Verificar se é boolean True ou string "true"
                if isinstance(result, bool):
                    self.authenticated = result
                elif isinstance(result, str):
                    self.authenticated = result.lower() == "true"
                else:
                    # Tentar converter para boolean
                    self.authenticated = bool(result)
            
            if self.authenticated:
                logger.info("✅ Autenticação na API Olho Vivo bem-sucedida")
            else:
                logger.error(f"❌ Falha na autenticação da API Olho Vivo")
                logger.error(f"   Resposta recebida: {response.text}")
                logger.error(f"   Status: {response.status_code}")
                logger.error(f"   URL completa: {url}?token={self.token[:20]}...")
                logger.error(f"   ⚠️ Verifique se o token está correto e ativo em: https://www.sptrans.com.br/desenvolvedores/")
            
            return self.authenticated
            
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout ao autenticar na API Olho Vivo (servidor não respondeu)")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Erro de conexão com API Olho Vivo: {str(e)}")
            return False
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Erro HTTP ao autenticar: {e.response.status_code} - {e.response.text[:200]}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao autenticar na API Olho Vivo: {str(e)}")
            logger.error(f"   Tipo do erro: {type(e).__name__}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    def buscar_linhas(self, termos_busca: str) -> List[Dict]:
        """
        Busca linhas de ônibus
        
        Args:
            termos_busca: Número ou nome da linha (total ou parcial)
            
        Returns:
            Lista de linhas encontradas
        """
        if not self.authenticated:
            if not self.authenticate():
                return []
        
        try:
            url = f"{self.BASE_URL}/Linha/Buscar"
            params = {"termosBusca": termos_busca}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Erro ao buscar linhas: {str(e)}")
            return []
    
    def buscar_paradas(self, termos_busca: str) -> List[Dict]:
        """
        Busca paradas de ônibus
        
        Args:
            termos_busca: Nome ou código da parada
            
        Returns:
            Lista de paradas encontradas
        """
        if not self.authenticated:
            if not self.authenticate():
                return []
        
        try:
            url = f"{self.BASE_URL}/Parada/Buscar"
            params = {"termosBusca": termos_busca}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Erro ao buscar paradas: {str(e)}")
            return []
    
    def buscar_paradas_por_linha(self, codigo_linha: int) -> List[Dict]:
        """
        Busca paradas atendidas por uma linha
        
        Args:
            codigo_linha: Código identificador da linha
            
        Returns:
            Lista de paradas
        """
        if not self.authenticated:
            if not self.authenticate():
                return []
        
        try:
            url = f"{self.BASE_URL}/Parada/BuscarParadasPorLinha"
            params = {"codigoLinha": codigo_linha}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Erro ao buscar paradas por linha: {str(e)}")
            return []
    
    def obter_posicao_veiculos(self, codigo_linha: Optional[int] = None) -> Dict:
        """
        Obtém posição dos veículos em tempo real
        
        Args:
            codigo_linha: Código da linha (opcional, se não informado retorna todas)
            
        Returns:
            Dicionário com posições dos veículos
        """
        if not self.authenticated:
            if not self.authenticate():
                return {}
        
        try:
            if codigo_linha:
                url = f"{self.BASE_URL}/Posicao/Linha"
                params = {"codigoLinha": codigo_linha}
            else:
                url = f"{self.BASE_URL}/Posicao"
                params = {}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # A API às vezes retorna texto vazio ou HTML em vez de JSON.
            # Tentar parsear como JSON; se falhar, logar e devolver estrutura vazia estável.
            try:
                data = response.json()
                return data if isinstance(data, dict) else {}
            except ValueError:
                text = (response.text or '').strip()
                logger.error(f"Erro ao obter posição dos veículos: resposta não-JSON: '{text[:200]}'")
                # Retornar formato compatível com o frontend: sem veículos.
                return {}
            
        except Exception as e:
            logger.error(f"Erro ao obter posição dos veículos: {str(e)}")
            return {}
    
    def obter_previsao_chegada(self, codigo_parada: int, codigo_linha: Optional[int] = None) -> Dict:
        """
        Obtém previsão de chegada dos veículos
        
        Args:
            codigo_parada: Código da parada
            codigo_linha: Código da linha (opcional)
            
        Returns:
            Dicionário com previsões de chegada
        """
        if not self.authenticated:
            if not self.authenticate():
                return {}
        
        try:
            if codigo_linha:
                url = f"{self.BASE_URL}/Previsao"
                params = {
                    "codigoParada": codigo_parada,
                    "codigoLinha": codigo_linha
                }
            else:
                url = f"{self.BASE_URL}/Previsao/Parada"
                params = {"codigoParada": codigo_parada}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Erro ao obter previsão de chegada: {str(e)}")
            return {}
    
    def obter_corredores(self) -> List[Dict]:
        """
        Obtém lista de corredores
        
        Returns:
            Lista de corredores
        """
        if not self.authenticated:
            if not self.authenticate():
                return []
        
        try:
            url = f"{self.BASE_URL}/Corredor"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Erro ao obter corredores: {str(e)}")
            return []
    
    def obter_empresas(self) -> List[Dict]:
        """
        Obtém lista de empresas operadoras
        
        Returns:
            Lista de empresas
        """
        if not self.authenticated:
            if not self.authenticate():
                return []
        
        try:
            url = f"{self.BASE_URL}/Empresa"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Erro ao obter empresas: {str(e)}")
            return []

