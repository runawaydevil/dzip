# DZip - Compacte e Compartilhe Arquivos

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Flask](https://img.shields.io/badge/flask-2.3.3-blue)](https://flask.palletsprojects.com/)
[![Status](https://img.shields.io/badge/status-active-success)]()
[![Hack the Planet](https://img.shields.io/badge/Hack-The%20Planet-red)](https://github.com/RunawayDevil)
[![1337](https://img.shields.io/badge/1337-H4X0R-orange)](https://github.com/RunawayDevil)
[![Matrix](https://img.shields.io/badge/Matrix-Neo-green)](https://github.com/RunawayDevil)
[![Terminal](https://img.shields.io/badge/Terminal-%3E_%20-green)](https://github.com/RunawayDevil)

DZip é uma aplicação web que permite compactar e compartilhar arquivos de forma simples e segura. Com suporte para arquivos ZIP e RAR, você pode compactar até 100 arquivos de uma vez, com tamanho total máximo de 500MB.

## Características

- Compactação de múltiplos arquivos (até 100)
- Suporte para formatos ZIP e RAR
- Limite de 500MB por upload
- Links de compartilhamento com validade de 7 dias
- Interface moderna e responsiva
- Upload por drag-and-drop
- Compartilhamento de links para download

## Requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)
- SQLite (padrão) ou PostgreSQL (opcional)

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/RunawayDevil/dzip.git
cd dzip
```

2. Crie um ambiente virtual (recomendado):
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
   - Copie o arquivo `.env.sample` para `.env`:
   ```bash
   cp .env.sample .env
   ```
   - Edite o arquivo `.env` com suas configurações:
   ```
   SECRET_KEY=sua_chave_secreta_aqui
   DATABASE_URL=sqlite:///dzip.db
   LINK_EXPIRATION_DAYS=7
   MAX_UPLOAD_SIZE=524288000
   MAX_FILES_PER_UPLOAD=100
   ```

5. Inicialize o banco de dados:
```bash
flask db init
flask db migrate
flask db upgrade
```

## Executando a Aplicação

1. Inicie o servidor Flask:
```bash
python app.py
```

2. Acesse a aplicação em seu navegador:
```
http://localhost:5000
```

Para produção, recomenda-se usar o Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Uso

1. Arraste e solte seus arquivos na área indicada ou clique em "Selecione Arquivos"
2. Verifique a lista de arquivos selecionados
3. Clique em "Compactar e Gerar Link"
4. Copie o link gerado e compartilhe com quem desejar

## Limitações

- Máximo de 100 arquivos por upload
- Tamanho total máximo de 500MB
- Links expiram após 7 dias
- Arquivos são automaticamente removidos após a expiração do link

## Changelog

### v1.0.0 (2025-01-01)
- Lançamento inicial do DZip
- Implementação do sistema de upload de arquivos
- Suporte para compactação e descompactação de arquivos
- Interface moderna e responsiva
- Sistema de links temporários
- Limite de 100 arquivos e 500MB por upload
- Configuração via variáveis de ambiente
- Suporte a SQLite e PostgreSQL
- Sistema de migração de banco de dados
- Documentação completa
- Licença MIT

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Autor

- **RunawayDevil** - [GitHub](https://github.com/RunawayDevil)

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes. 