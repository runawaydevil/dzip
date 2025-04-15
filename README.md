# DZip - Compactador e Compartilhador de Arquivos

DZip é uma aplicação web desenvolvida em Python/Flask que permite compactar, extrair e compartilhar arquivos de forma simples e segura.

## Funcionalidades

- **Compartilhamento de Arquivos**
  - Upload de arquivos únicos (até 100MB)
  - Geração de link único para compartilhamento
  - Arquivos disponíveis por 7 dias
  - Contador de downloads

- **Compactação de Arquivos**
  - Upload de múltiplos arquivos (até 10 arquivos, totalizando 500MB)
  - Compactação automática em formato ZIP
  - Interface drag-and-drop

- **Extração de Arquivos**
  - Upload de arquivos ZIP (até 500MB)
  - Extração automática
  - Lista de arquivos extraídos com opções de download
  - Limpeza automática após 1 hora

## Requisitos

- Python 3.8+
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Outras dependências listadas em `requirements.txt`

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/RunawayDevil/dzip.git
cd dzip
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Execute a aplicação:
```bash
python app.py
```

A aplicação estará disponível em `http://localhost:5000`

## Interface

- Design moderno com Tailwind CSS
- Interface responsiva
- Suporte a drag-and-drop
- Feedback visual de progresso
- Mensagens de erro claras

## Segurança

- Validação de tipos de arquivo
- Limites de tamanho
- Nomes de arquivo únicos
- Limpeza automática de arquivos temporários

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Autor

- RunawayDevil - [GitHub](https://github.com/RunawayDevil)

## 🙏 Agradecimentos

- [Flask](https://flask.palletsprojects.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Font Awesome](https://fontawesome.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/) 