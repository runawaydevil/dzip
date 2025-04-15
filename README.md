# DZip - Compactador e Extrator de Arquivos

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Stable-brightgreen)](https://github.com/RunawayDevil/dzip)

DZip é uma aplicação web moderna para compactação e extração de arquivos, desenvolvida com Flask e Python. Oferece uma interface intuitiva e recursos avançados para gerenciamento de arquivos.

## ✨ Funcionalidades

- **Compactação de Arquivos**
  - Upload de múltiplos arquivos (até 10)
  - Compressão nível 9 (máxima)
  - Limite de tamanho total de 100MB
  - Links de download temporários
  - Interface drag-and-drop

- **Extração de Arquivos**
  - Upload de arquivos ZIP
  - Visualização de arquivos extraídos
  - Download individual ou em lote
  - Limpeza automática após 1 hora
  - Interface moderna e responsiva

- **Segurança**
  - Validação de tipos de arquivo
  - Limites de tamanho
  - Nomes de arquivo únicos
  - Remoção automática de arquivos antigos

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/RunawayDevil/dzip.git
cd dzip
```

2. Crie um ambiente virtual:
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
```bash
# Windows
set FLASK_APP=app.py
set FLASK_ENV=development

# Linux/Mac
export FLASK_APP=app.py
export FLASK_ENV=development
```

5. Inicialize o banco de dados:
```bash
flask db init
flask db migrate
flask db upgrade
```

6. Execute o aplicativo:
```bash
flask run
```

## ⚙️ Configuração

O DZip pode ser configurado através de variáveis de ambiente:

- `MAX_UPLOAD_SIZE`: Tamanho máximo de upload (padrão: 500MB)
- `MAX_FILES_PER_UPLOAD`: Número máximo de arquivos por upload (padrão: 100)
- `LINK_EXPIRATION_DAYS`: Dias até a expiração dos links (padrão: 7)
- `SECRET_KEY`: Chave secreta para a aplicação
- `DATABASE_URL`: URL do banco de dados (padrão: sqlite:///dzip.db)

## 📝 Uso

1. **Compactar Arquivos**
   - Acesse a aba "Compactar"
   - Arraste ou selecione os arquivos
   - Clique em "Compactar Arquivos"
   - Copie o link gerado

2. **Extrair Arquivos**
   - Acesse a aba "Extrair"
   - Arraste ou selecione o arquivo ZIP
   - Clique em "Extrair Arquivo"
   - Baixe os arquivos extraídos

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👨‍💻 Autor

- **RunawayDevil** - [GitHub](https://github.com/RunawayDevil)

## 🙏 Agradecimentos

- [Flask](https://flask.palletsprojects.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Font Awesome](https://fontawesome.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/) 