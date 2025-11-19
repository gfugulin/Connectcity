Ir para o conteúdo principal 1 Ir para o menu 2 Ir para pesquisa 3 Ir para o rodapé 4
PREFEITURA DE SÃO PAULOAcesso à informação Ícone representando um balão de conversa amarelo com a letra i em verde dentro deleTRANSPARÊNCIA SÃO PAULO
Secretaria Municipal de Transporte e Mobilidade Urbana
Logo da SPTrans e logo comemorativo de 30 anos da empresa
Logo da Prefeitura de São Paulo
Ícone de um ônibus com o texto: Planeje sua viagem
Por trajeto
Por linha
Por local
ACESSO À INFORMAÇÃOPARTICIPAÇÃO SOCIALQUADRO DE SERVIÇOSSPTRANSATENDE+FALE CONOSCOLogotipo do InstagramLogotipo do YoutubeLogotipo do FacebookLogotipo do Twitter
Buscar no site
Buscar no site
Documentacao API
Home Desenvolvedores  API DO OLHO VIVO - GUIA DE REFERÊNCIA  Documentacao API
Atenção: alteração de protocolo
A API do OlhoVivo passa por melhorias constantes e adotou o uso do protocolo HTTPS.
O acesso pelo protocolo HTTP continua disponível até 02/01/2024 quando será desativado, e a partir de então o acesso se dará exclusivamente pelo protocolo HTTPS. Atualize sua aplicação e adote este protocolo seguro o quanto antes.
API DO OLHO VIVO - Guia de Referência
A API de desenvolvimento do Olho Vivo utiliza o protocolo HTTP e seus métodos para trazer as informações necessárias para o desenvolvimento do seu aplicativo.
O formato de retorno dos dados respeita a estrutura RESTFUL e é entregue no formato JSON.
 

Versões disponíveis: 
2.1


conteúdos
Acesso
Autenticação e credenciais
Linhas
Buscar
BuscarLinhaSentido
Paradas
Buscar
BuscarParadasPorLinha
BuscarParadasPorCorredor
Corredores
Empresas
Posição dos veículos
Get
Linha
Garagem
Previsão de chegada
Get
Linha
Parada
Velocidade nas vias
Get
Corredor
OutrasVias
Acesso
O acesso à API do Olho Vivo é possível através da URL http://api.olhovivo.sptrans.com.br/v2.1. v[n] Indica a versão da API a ser utilizada
Autenticação e credenciais
Para autenticar-se no serviço de API do Olho Vivo é necessário efetuar uma chamada prévia utilizando o método http POST informando seu token de acesso. Essa chamada irá retornar true quando a autenticação for realizada com sucesso e false em caso de erros. [string]token Sua chave de acesso que deve ser gerada na área "Meus Aplicativos".
Para mais informações veja como acessar seu perfil Veja um exemplo:
 
POST /Login/Autenticar?token={token}


true
                                                
Linhas
A categoria Linhas possibilita a consulta pelas linhas de ônibus da cidade de São Paulo, bem como suas informações cadastrais como por exemplo: horário de operação da linha, dias de operação (dia útil, sábado ou domingo) e extensão da linha (em metros).
Nesta categoria existem os seguintes métodos de consulta disponíveis:
Buscar
Realiza uma busca das linhas do sistema com base no parâmetro informado. Se a linha não é encontrada então é realizada uma busca fonetizada na denominação das linhas. parâmetro
 

[string]termosBusca descrição
 

Aceita denominação ou número da linha (total ou parcial).
Exemplo: 8000, Lapa ou Ramos Veja um exemplo:
 
GET /Linha/Buscar?termosBusca=8000

[
    {
        "cl": 1273,
        "lc": false,
        "lt": "8000",
        "sl": 1,
        "tl": 10,
        "tp": "PCA.RAMOS DE AZEVEDO",
        "ts": "TERMINAL LAPA"
    },
    {
        "cl": 34041,
        "lc": false,
        "lt": "8000",
        "sl": 2,
        "tl": 10,
        "tp": "PCA.RAMOS DE AZEVEDO",
        "ts": "TERMINAL LAPA"
    }
]
                                                
 
Objetos de retorno
[int]cl Código identificador da linha. Este é um código identificador único de cada linha do sistema (por sentido de operação) [bool]lc Indica se uma linha opera no modo circular (sem um terminal secundário) [string]lt Informa a primeira parte do letreiro numérico da linha [int]tl Informa a segunda parte do letreiro numérico da linha, que indica se a linha opera nos modos:
BASE (10), ATENDIMENTO (21, 23, 32, 41) [int]sl Informa o sentido ao qual a linha atende, onde 1 significa Terminal Principal para Terminal Secundário e 2 para Terminal Secundário para Terminal Principal [str]tp Informa o letreiro descritivo da linha no sentido Terminal Principal para Terminal Secundário [str]ts Informa o letreiro descritivo da linha no sentido Terminal Secundário para Terminal Principal
BuscarLinhaSentido
Realiza uma busca das linhas do sistema com base no parâmetro informado. Se a linha não é encontrada então é realizada uma busca fonetizada na denominação das linhas. A linha retornada será unicamente aquela cujo sentido de operação seja o informado no parâmetro sentido. parâmetro
 

[string]termosBusca descrição
 

Aceita denominação ou número da linha (total ou parcial).
Exemplo: 8000, Lapa ou Ramos [byte]sentido Código identificador do sentido de operação da linha, onde:
1: Terminal Principal para Terminal Secundário
2: para Terminal Secundário para Terminal Principal Veja um exemplo:
 
GET /Linha/BuscarLinhaSentido?termosBusca={codigoLinha}&sentido={sentido}


[
    {
        "cl": 1273,
        "lc": false,
        "lt": "8000",
        "sl": 1,
        "tl": 10,
        "tp": "PCA.RAMOS DE AZEVEDO",
        "ts": "TERMINAL LAPA"
    }
]
                                                
 
Objetos de retorno
[int]cl Código identificador da linha. Este é um código identificador único de cada linha do sistema (por sentido de operação) [bool]lc Indica se uma linha opera no modo circular (sem um terminal secundário) [string]lt Informa a primeira parte do letreiro numérico da linha [int]tl Informa a segunda parte do letreiro numérico da linha, que indica se a linha opera nos modos:
BASE (10), ATENDIMENTO (21, 23, 32, 41) [int]sl Informa o sentido ao qual a linha atende, onde 1 significa Terminal Principal para Terminal Secundário e 2 para Terminal Secundário para Terminal Principal [str]tp Informa o letreiro descritivo da linha no sentido Terminal Principal para Terminal Secundário [str]ts Informa o letreiro descritivo da linha no sentido Terminal Secundário para Terminal Principal
 
Paradas
A categoria Paradas possibilita a consulta pelos pontos de parada da cidade de São Paulo. Atualmente esta categoria contempla apenas as paradas de corredores.
Nesta categoria existem os seguintes métodos de consulta disponíveis:
Buscar
Realiza uma busca fonética das paradas de ônibus do sistema com base no parâmetro informado. A consulta é realizada no nome da parada e também no seu endereço de localização.
parâmetro
 

[string]termosBusca descrição
 

Aceita nome da parada ou endereço de localização (total ou parcial).
Exemplo: Afonso, ou Balthazar da Veiga Veja um exemplo:
 
GET /Parada/Buscar?termosBusca={termosBusca}


[
  {
    "cp": 340015329,
    "np": "AFONSO BRAZ B/C1",
    "ed": "R ARMINDA/ R BALTHAZAR DA VEIGA",
    "py": -23.592938,
    "px": -46.672727
  }
]
                                                
 
Objetos de retorno
[int]cp Código identificador da parada [string]np Nome da parada [string]ed Endereço de localização da parada [double]py Informação de latitude da localização da parada [double]px Informação de longitude da localização da parada
 
BuscarParadasPorLinha
Realiza uma busca por todos os pontos de parada atendidos por uma determinada linha. parâmetro
 

[int]codigoLinha descrição
 

Código identificador da linha. Este é um código identificador único de cada linha do sistema (por sentido) e pode ser obtido através do método BUSCAR da categoria Linhas Veja um exemplo:
 
GET /Parada/BuscarParadasPorLinha?codigoLinha={codigoLinha}


[
  {
    "cp": 340015329,
    "np": "AFONSO BRAZ B/C1",
    "ed": "R ARMINDA/ R BALTHAZAR DA VEIGA",
    "py": -23.592938,
    "px": -46.672727
  }
]
                                                
 
Objetos de retorno
[int]cp Código identificador da parada [string]np Nome da parada [string]ed Endereço de localização da parada [double]py Informação de latitude da localização da parada [double]px Informação de longitude da localização da parada
 
BuscarParadasPorCorredor
Retorna a lista detalhada de todas as paradas que compõem um determinado corredor. parâmetro
 

[int]codigoCorredor descrição
 

Código identificador do corredor. Este é um código identificador único de cada corredor do sistema e pode ser obtido através do método GET da categoria Corredores Veja um exemplo:
 
GET /Parada/BuscarParadasPorCorredor?codigoCorredor={codigoCorredor}


[
  {
    "cp": 340015329,
    "np": "AFONSO BRAZ B/C1",
    "ed": "R ARMINDA/ R BALTHAZAR DA VEIGA",
    "py": -23.592938,
    "px": -46.672727
  }
]
                                                
 
Objetos de retorno
[int]cp Código identificador da parada [string]np Nome da parada [string]ed Endereço de localização da parada [double]py Informação de latitude da localização da parada [double]px Informação de longitude da localização da parada
 
Corredores
A categoria Corredores possibilita uma consulta que retorna todos os corredores inteligentes da cidade de São Paulo.
Nesta categoria existem os seguintes métodos de consulta disponíveis:
GET
Retorna uma lista com todos os corredores inteligentes
Veja um exemplo:
 
GET /Corredor


[
  {
    "cc":8,
    "nc":"Campo Limpo"
  }
]
                                                
 
Objetos de retorno
[int]cc Código identificador da corredor. Este é um código identificador único de cada corredor inteligente do sistema [string]nc Nome do corredor
Empresas
A categoria Empresas possibilita uma consulta que retorna a relação das empresas operadoras do transporte público na cidade de São Paulo.
Nesta categoria existem os seguintes métodos de consulta disponíveis:
GET
Retorna uma lista com todos as empresas operadoras relacionadas por área de operação
Veja um exemplo:
 
GET /Empresa


[
  {
    "hr":"11:20",
    "e": [
      {
        "a": 1,
        "e": [
          {
            "a": 1,
            "c": 999,
            "n": "NOME"
          }
        ]
      }
    ]
  }
]
                                                
 
Objetos de retorno
[string]hr Horário de referência da geração das informações [{}]e Relação de empresas por área de operação [int]a Código da área de operação [{}]e Relação de empresas [int]a Código da área de operação [int]c Código de referência da empresa [string]n Nome da empresa
Posição dos veículos
A categoria Posição Dos Veículos é a responsável por retornar a posição exata de cada veículo de qualquer linha de ônibus da SPTrans
Nesta categoria existem os seguintes métodos de consulta disponíveis:
GET
Retorna uma lista completa com a última localização de todos os veículos mapeados com suas devidas posições lat / long Veja um exemplo:
 
GET /Posicao


{
  "hr": "11:30",
  "l": [
    {
      "c": "5015-10",
      "cl": 33887,
      "sl": 2,
      "lt0": "METRÔ JABAQUARA",
      "lt1": "JD. SÃO JORGE",
      "qv": 1,
      "vs": [
        {
          "p":68021,
          "a":true,
          "ta":"2017-05-12T14:30:37Z",
          "py":-23.678712500000003,
          "px":-46.65674
        }
      ]
    }
  ]
}
 
Objetos de retorno
[string]hr Horário de referência da geração das informações [{}]l Relação de linhas localizadas onde: [string]c Letreiro completo [int]cl Código identificador da linha [int]sl Sentido de operação onde 1 significa de Terminal Principal para Terminal Secundário e 2 de Terminal Secundário para Terminal Principal [string]lt0 Letreiro de destino da linha [string]lt1 Letreiro de origem da linha [int]qv Quantidade de veículos localizados [{}]vs Relação de veículos localizados, onde: [int]p Prefixo do veículo [bool]a Indica se o veículo é (true) ou não (false) acessível para pessoas com deficiência [string]ta Indica o horário universal (UTC) em que a localização foi capturada. Essa informação está no padrão ISO 8601 [double]py Informação de latitude da localização do veículo [double]px Informação de longitude da localização do veículo
Linha
Retorna uma lista com todos os veículos de uma determinada linha com suas devidas posições lat / long parâmetro
 

[int]codigoLinha descrição
 

Código identificador da linha. Este é um código identificador único de cada linha do sistema (por sentido) e pode ser obtido através do método BUSCAR da categoria Linhas Veja um exemplo:
 
GET /Posicao/Linha?codigoLinha={codigoLinha}


{
  "hr": "19:57",
  "vs": [
    {
      "p": "11433",
      "a": false,
      "ta": "2017-05-07T22:57:02Z",
      "py": -23.540150375000003,
      "px": -46.64414075
    }
  ]
}
                                                
 
Objetos de retorno
[string]hr Horário de referência da geração das informações [{}]vs Relação de veículos localizados, onde: [int]p Prefixo do veículo [bool]a Indica se o veículo é (true) ou não (false) acessível para pessoas com deficiência [string]ta Indica o horário universal (UTC) em que a localização foi capturada. Essa informação está no padrão ISO 8601 [double]py Informação de latitude da localização do veículo [double]px Informação de longitude da localização do veículo
Garagem
Retorna uma lista completa todos os veículos mapeados que estejam transmitindo em uma garagem da empresa informada. parâmetro
 

[int]codigoEmpresa  descrição
 

Código identificador da empresa. Este é um código identificador único que pode ser obtido através do método GET da categoria Empresas [int]codigoLinha opcional Código identificador da linha. Este é um código identificador único de cada linha do sistema (por sentido) e pode ser obtido através do método BUSCAR da categoria Linhas Veja um exemplo:
 
GET /Posicao/Garagem?codigoEmpresa=0[&codigoLinha=0]


{
  "hr": "11:30",
  "l": [
    {
      "c": "5015-10",
      "cl": 33887,
      "sl": 2,
      "lt0": "METRÔ JABAQUARA",
      "lt1": "JD. SÃO JORGE",
      "qv": 1,
      "vs": [
        {
          "p":68021,
          "a":true,
          "ta":"2017-05-12T14:30:37Z",
          "py":-23.678712500000003,
          "px":-46.65674
        }
      ]
    }
  ]
}
 
Objetos de retorno
[string]hr Horário de referência da geração das informações [{}]l Relação de linhas localizadas onde: [string]c Letreiro completo [int]cl Código identificador da linha [int]sl Sentido de operação onde 1 significa de Terminal Principal para Terminal Secundário e 2 de Terminal Secundário para Terminal Principal [string]lt0 Letreiro de destino da linha [string]lt1 Letreiro de origem da linha [int]qv Quantidade de veículos localizados [{}]vs Relação de veículos localizados, onde: [int]p Prefixo do veículo [bool]a Indica se o veículo é (true) ou não (false) acessível para pessoas com deficiência [string]ta Indica o horário universal (UTC) em que a localização foi capturada. Essa informação está no padrão ISO 8601 [double]py Informação de latitude da localização do veículo [double]px Informação de longitude da localização do veículo
Previsão de chegada
A categoria Previsão de chegada é a responsável por retornar a previsão de chegada de cada veículo de uma determinada linha e de um determinado ponto de parada, além da localização exata de cada veículo que constar na cadeia de previsões.
Obs.: As previsões são baseadas no horário também informado no retorno dos métodos.

Nesta categoria existem os seguintes métodos de consulta disponíveis:
GET
Retorna uma lista com a previsão de chegada dos veículos da linha informada que atende ao ponto de parada informado. parâmetro
 

[int]codigoParada descrição
 

Código identificador da parada. Este é um código identificador único de cada ponto de parada do sistema (por sentido) e pode ser obtido através do método BUSCAR da categoria Paradas [int]codigoLinha Código identificador da linha. Este é um código identificador único de cada linha do sistema (por sentido) e pode ser obtido através do método BUSCAR da categoria Linhas Veja um exemplo:
 
GET /Previsao?codigoParada={codigoParada}&codigoLinha={codigoLinha}


{
  "hr": "20:09",
  "p": {
    "cp": 4200953,
    "np": "PARADA ROBERTO SELMI DEI B/C",
    "py": -23.675901,
    "px": -46.752812,
    "l": [
      {
        "c": "7021-10",
        "cl": 1989,
        "sl": 1,
        "lt0": "TERM. JOÃO DIAS",
        "lt1": "JD. MARACÁ",
        "qv": 1,
        "vs": [
          {
            "p": "74558",
            "t": "23:11",
            "a": true,
            "ta": "2017-05-07T23:09:05Z",
            "py": -23.67603,
            "px": -46.75891166666667
          }
        ]
      }
    ]
  }
}
                                                
 
Objetos de retorno
[string]hr Horário de referência da geração das informações {}p Representa um ponto de parada onde: [int]cp código identificador da parada [string]np Nome da parada [double]py Informação de latitude da localização do veículo [double]px Informação de longitude da localização do veículo [{}]l Relação de linhas localizadas onde: [string]c Letreiro completo [int]cl Código identificador da linha [int]sl Sentido de operação onde 1 significa de Terminal Principal para Terminal Secundário e 2 de Terminal Secundário para Terminal Principal [string]lt0 Letreiro de destino da linha [string]lt1 Letreiro de origem da linha [int]qv Quantidade de veículos localizados [{}]vs Relação de veículos localizados onde: [int]p Prefixo do veículo [string]t Horário previsto para chegada do veículo no ponto de parada relacionado [bool]a Indica se o veículo é (true) ou não (false) acessível para pessoas com deficiência [string]ta Indica o horário universal (UTC) em que a localização foi capturada. Essa informação está no padrão ISO 8601 [double]py Informação de latitude da localização do veículo [double]px Informação de longitude da localização do veículo
 
Linha
Retorna uma lista com a previsão de chegada de cada um dos veículos da linha informada em todos os pontos de parada aos quais que ela atende. parâmetro
 

[int]codigoLinha descrição
 

Código identificador da linha. Este é um código identificador único de cada linha do sistema (por sentido) e pode ser obtido através do método BUSCAR da categoria Linhas Veja um exemplo:
 
GET /Previsao/Linha?codigoLinha={codigoLinha}


{
  "hr": "20:18",
  "ps": [
    {
      "cp": 700016623,
      "np": "ANA CINTRA B/C",
      "py": -23.538763,
      "px": -46.646925,
      "vs": [
        {
          "p": "11436",
          "t": "23:26",
          "a": false,
          "ta": "2017-05-07T23:18:02Z",
          "py": -23.528119999999998,
          "px": -46.670674999999996
        }
      ]
    }
  ]
}
                                                
 
Objetos de retorno
[string]hr Horário de referência da geração das informações [{}]ps Representa uma relação de pontos de parada onde: [int]cp código identificador da parada [string]np Nome da parada [double]py Informação de latitude da localização do veículo [double]px Informação de longitude da localização do veículo [{}]vs Relação de veículos localizados onde: [int]p Prefixo do veículo [string]t Horário previsto para chegada do veículo no ponto de parada relacionado [bool]a Indica se o veículo é (true) ou não (false) acessível para pessoas com deficiência [string]ta Indica o horário universal (UTC) em que a localização foi capturada. Essa informação está no padrão ISO 8601 [double]py Informação de latitude da localização do veículo [double]px Informação de longitude da localização do veículo
 
Parada
Retorna uma lista com a previsão de chegada dos veículos de cada uma das linhas que atendem ao ponto de parada informado. parâmetro
 

[int]codigoParada descrição
 

Código identificador da parada. Este é um código identificador único de cada ponto de parada do sistema (por sentido) e pode ser obtido através do método BUSCAR da categoria Paradas Veja um exemplo:
 
GET /Previsao/Parada?codigoParada={codigoParada}


{
  "hr": "20:20",
  "p": {
    "cp": 4200953,
    "np": "PARADA ROBERTO SELMI DEI B/C",
    "py": -23.675901,
    "px": -46.752812,
    "l": [
      {
        "c": "675K-10",
        "cl": 198,
        "sl": 1,
        "lt0": "METRO STA CRUZ",
        "lt1": "TERM. JD. ANGELA",
        "qv": 1,
        "vs": [
          {
            "p": "73651",
            "t": "23:22",
            "a": true,
            "ta": "2017-05-07T23:20:06Z",
            "py": -23.676623333333335,
            "px": -46.757641666666665
          }
        ]
      }
    ]
  }
}
                                                
 
Objetos de retorno
[string]hr Horário de referência da geração das informações {}p Representa um ponto de parada onde: [int]cp código identificador da parada [string]np Nome da parada [double]py Informação de latitude da localização do veículo [double]px Informação de longitude da localização do veículo [{}]l Relação de linhas localizadas onde: [string]c Letreiro completo [int]cl Código identificador da linha [int]sl Sentido de operação onde 1 significa de Terminal Principal para Terminal Secundário e 2 de Terminal Secundário para Terminal Principal [string]lt0 Letreiro de destino da linha [string]lt1 Letreiro de origem da linha [int]qv Quantidade de veículos localizados [{}]vs Relação de veículos localizados onde: [int]p Prefixo do veículo [string]t Horário previsto para chegada do veículo no ponto de parada relacionado [bool]a Indica se o veículo é (true) ou não (false) acessível para pessoas com deficiência [string]ta Indica o horário universal (UTC) em que a localização foi capturada. Essa informação está no padrão ISO 8601 [double]py Informação de latitude da localização do veículo [double]px Informação de longitude da localização do veículo
Velocidade nas vias
A categoria Velocidade nas Vias é a responsável por retornar um arquivo KMZ contendo um mapa de fluidez da cidade com a velocidade média e tempo de percurso de cada trecho envolvido.
Nesta categoria existem os seguintes métodos de consulta disponíveis:
GET
Retorna o mapa completo da cidade.
parâmetro
 

[string]sentido descrição
 

Se desejar a informação separada de um único sentido será preciso indicar aqui. Os valores possíveis são:
BC - veículos saindo do bairro em direção ao centro
CB - veículos saindo do centro em direção ao bairro

Veja um exemplo:
 
GET /KMZ



GET /KMZ/BC


 
Corredor
Retorna o mapa completo de todos os corredores da cidade.
parâmetro
 

[string]sentido descrição
 

Se desejar a informação separada de um único sentido será preciso indicar aqui. Os valores possíveis são:
BC - veículos saindo do bairro em direção ao centro
CB - veículos saindo do centro em direção ao bairro

Veja um exemplo:
 
GET /KMZ/Corredor



GET /KMZ/Corredor/BC


 
OutrasVias
Retorna o mapa completo com as vias importantes da cidade (exceto corredores).
parâmetro
 

[string]sentido descrição
 

Se desejar a informação separada de um único sentido será preciso indicar aqui. Os valores possíveis são:
BC - veículos saindo do bairro em direção ao centro
CB - veículos saindo do centro em direção ao bairro

Veja um exemplo:
 
GET /KMZ/OutrasVias



GET /KMZ/OutrasVias/BC


 
Acesso à Informação - SPTrans
Aquático SP
Audiências públicas - Faixas exclusivas
Bilhete QR Digital
Bilhete Único
Campanhas
Canal do Estudante
Compra de Créditos e Serviços
Desenvolvedores
Governança Corporativa
Informativos
Licitações
Manuais Técnicos e Resoluções
Mídia e Negócios
Museu SPTrans dos Transportes
Notícias
Noturno - Rede de Ônibus da Madrugada
Ouvidoria
Participação Social
Passageiros Transportados
Perguntas e Respostas
PlanFrota
Postos de Atendimento
Programa de Estágio
Seleção Pública
Tarifas
SPTrans Brasão da Prefeitura de São Paulo. À direita, os textos: Prefeitura de São Paulo - Mobilidade Urbana e Transporte
São Paulo Transporte S/A
Rua Boa Vista, 236 - Centro - São Paulo/SP
CEP: 01014-000
Telefone: 156
Política de PrivacidadeLogotipo do Instagram Logotipo do Youtube Logotipo do Facebook Logotipo do TwitterParticipante do Programa Nacional de Prevenção à Corrupção Este sitio possui um selo de acessibilidade digital.


Plugin de acessibilidade da Hand Talk.


