# FlowSheet

FlowSheet é uma aplicação backend construída com Django para automatizar fluxos baseados em planilhas Excel. O sistema importa dados estruturados de uma planilha, persiste esses dados no banco e executa automações web com Playwright usando cada linha como entrada.

## Problema que o projeto resolve

Muitas operações administrativas ainda dependem de copiar dados de planilhas e preencher formulários manualmente em sistemas web. O FlowSheet reduz esse trabalho repetitivo, permitindo:

- importar uma planilha com dados
- revisar e editar registros dentro da aplicação
- disparar automações web baseadas nesses registros
- acompanhar o progresso da execução em tempo real

## Principais funcionalidades

- upload de planilhas Excel
- parsing e persistência dos dados importados
- histórico de importações
- edição manual de cada linha importada
- execução de automação com Playwright
- atualização em tempo real do status linha por linha
- histórico de execuções
- histórico de resultados por registro executado
- reprocessamento apenas dos registros com erro

## Arquitetura

O projeto segue uma separação simples e didática por responsabilidade:

- `models`: representam o domínio e a persistência
- `views`: recebem as requisições HTTP e retornam respostas
- `services`: concentram a lógica de negócio
- `templates`: renderizam a interface com Django Templates

### Apps principais

#### `registros`

Responsável por:

- upload da planilha
- criação do lote de importação
- persistência dos registros
- listagem dos dados importados
- edição dos registros

Models principais:

- `ImportacaoPlanilha`
- `Registro`

#### `automations`

Responsável por:

- disparo da automação
- controle das execuções
- atualização de status dos registros
- histórico por execução
- endpoint de status para atualização em tempo real
- reprocessamento de erros

Models principais:

- `Execution`
- `ResultadoExecucaoRegistro`

## Fluxo do sistema

1. o usuário envia uma planilha pela rota `/upload/`
2. o backend cria uma `ImportacaoPlanilha`
3. cada linha da planilha vira um `Registro`
4. o usuário revisa ou edita os dados em `/registros/`
5. o usuário inicia a automação
6. o sistema cria uma `Execution`
7. o Playwright processa os registros em background
8. o status de cada linha é atualizado em tempo real
9. os resultados ficam salvos para consulta posterior

## Modelagem principal

### `ImportacaoPlanilha`

Representa um lote importado de uma planilha.

Campos principais:

- `nome_arquivo`
- `status`
- `total_registros`
- `criado_em`

### `Registro`

Representa uma linha da planilha.

Campos principais:

- `nome`
- `empresa`
- `email`
- `telefone`
- `status`
- `mensagem_erro`
- `executado_em`
- `importacao`

### `Execution`

Representa uma execução de automação.

Campos principais:

- `importacao`
- `status`
- `total_linhas`
- `linhas_processadas`
- `sucesso_count`
- `erro_count`
- `mensagem_erro`
- `criado_em`
- `finalizado_em`

### `ResultadoExecucaoRegistro`

Representa o resultado de um registro dentro de uma execução específica.

Campos principais:

- `execution`
- `registro`
- `status`
- `mensagem_erro`
- `executado_em`

## Stack utilizada

### Backend

- Python
- Django

### Processamento de planilhas

- openpyxl

### Automação

- Playwright

### Banco de dados

- SQLite no ambiente de desenvolvimento
- PostgreSQL pode ser adotado em produção

### Interface

- Django Templates

## Requisitos

- Python 3.14+
- ambiente virtual recomendado
- Chromium do Playwright instalado

## Instalação

```bash
git clone <url-do-repositorio>
cd flow-sheet
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
python manage.py migrate
```

## Como executar o projeto

```bash
python manage.py runserver
```

Depois acesse:

- `http://127.0.0.1:8000/upload/`

## Como usar

1. acesse a tela de upload
2. envie uma planilha `.xlsx`
3. vá para a listagem de registros
4. revise ou edite as linhas importadas
5. clique em `Iniciar automação`
6. acompanhe a execução em tempo real
7. consulte o detalhe da execução
8. se houver falhas, use o reprocessamento de erros

## Formato esperado da planilha

A planilha deve conter, no mínimo, as seguintes colunas:

- `nome`
- `empresa`
- `email`
- `telefone`

O sistema atualmente lê a planilha ativa e começa a processar a partir da segunda linha, assumindo que a primeira contém cabeçalhos.

## Testes

Para executar os testes:

```bash
python manage.py test
```

## Decisões técnicas do projeto

- separação entre os apps `registros` e `automations`
- uso de `services.py` para manter lógica de negócio fora das views
- modelagem de importações como lote (`ImportacaoPlanilha`)
- modelagem de histórico de execução por registro (`ResultadoExecucaoRegistro`)
- atualização em tempo real via polling HTTP
- execução em background para não bloquear a resposta da interface

## Limitações atuais

Como MVP e projeto de portfólio, o sistema ainda possui algumas simplificações:

- a automação roda em background com thread local, não com fila de jobs profissional
- não há autenticação aplicada ao fluxo principal
- a validação da planilha ainda é simples
- o destino da automação está centrado em um formulário de teste interno
- não há logging estruturado nem observabilidade avançada

## Melhorias futuras

- Celery + Redis para processamento assíncrono real
- autenticação e permissões por usuário
- API REST
- validação avançada de planilhas
- logging estruturado
- dashboard de monitoramento
- exportação de erros
- deploy com Docker
- PostgreSQL em produção

## Objetivo do projeto

Este projeto foi construído como peça de portfólio para demonstrar:

- conhecimento de Django
- modelagem de domínio
- organização de backend por camadas
- automação web com Playwright
- manipulação de arquivos e dados estruturados
- testes automatizados

## Contribuição

Contribuições são bem-vindas. Para mudanças maiores, o ideal é abrir uma issue antes para discutir a proposta.
