from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
import os
import magic
from werkzeug.utils import secure_filename
import pyminizip
import rarfile
import uuid
import zipfile
import shutil
import tempfile
import subprocess

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///dzip.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['EXTRACT_FOLDER'] = 'extracted'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
app.config['ALLOWED_EXTENSIONS'] = {'zip', 'rar'}

# Criar diretórios se não existirem
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['EXTRACT_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
    download_count = db.Column(db.Integer, default=0)
    share_link = db.Column(db.String(255), unique=True)
    is_extracted = db.Column(db.Boolean, default=False)
    extracted_files = db.Column(db.JSON, nullable=True)
    extracted_path = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<File {self.filename}>'

def init_db():
    """Inicializa o banco de dados e executa as migrações necessárias."""
    with app.app_context():
        # Verifica se o diretório de migrações existe
        migrations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migrations')
        
        try:
            if not os.path.exists(migrations_dir):
                # Inicializa o sistema de migração
                subprocess.run(['flask', 'db', 'init'], check=True)
            
            # Tenta criar as migrações
            try:
                subprocess.run(['flask', 'db', 'migrate', '-m', 'Initial migration'], check=True)
            except subprocess.CalledProcessError as e:
                # Se falhar, pode ser porque já existem migrações
                print("Aviso: Migrações já existem ou não há mudanças para migrar.")
            
            # Tenta aplicar as migrações
            try:
                subprocess.run(['flask', 'db', 'upgrade'], check=True)
            except subprocess.CalledProcessError as e:
                # Se falhar, tenta recriar o banco de dados
                print("Aviso: Tentando recriar o banco de dados...")
                if os.path.exists('dzip.db'):
                    os.remove('dzip.db')
                subprocess.run(['flask', 'db', 'upgrade'], check=True)
            
            # Cria as tabelas se não existirem
            db.create_all()
            
        except Exception as e:
            print(f"Erro ao inicializar o banco de dados: {str(e)}")
            # Tenta recriar o banco de dados do zero
            try:
                if os.path.exists('dzip.db'):
                    os.remove('dzip.db')
                if os.path.exists(migrations_dir):
                    shutil.rmtree(migrations_dir)
                subprocess.run(['flask', 'db', 'init'], check=True)
                subprocess.run(['flask', 'db', 'migrate', '-m', 'Initial migration'], check=True)
                subprocess.run(['flask', 'db', 'upgrade'], check=True)
                db.create_all()
            except Exception as e2:
                print(f"Erro crítico ao recriar o banco de dados: {str(e2)}")
                raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files and 'files[]' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        # Verificar se é upload único ou múltiplo
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
            
            # Verificar tamanho do arquivo
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            
            if size > app.config['MAX_CONTENT_LENGTH']:
                return jsonify({'error': 'Arquivo muito grande (máximo 100MB)'}), 400
            
            # Salvar arquivo
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
            
            try:
                file.save(file_path)
                
                # Criar registro no banco de dados
                share_link = str(uuid.uuid4())
                file_record = File(
                    filename=os.path.basename(file_path),
                    original_filename=filename,
                    file_path=file_path,
                    share_link=share_link,
                    is_extracted=False,
                    extracted_files=None,
                    extracted_path=None
                )
                db.session.add(file_record)
                db.session.commit()
                
                return jsonify({
                    'message': 'Arquivo enviado com sucesso',
                    'share_link': share_link,
                    'expires_at': file_record.expires_at.strftime('%Y-%m-%d %H:%M:%S')
                })
                
            except Exception as e:
                # Limpar arquivo em caso de erro
                if os.path.exists(file_path):
                    os.remove(file_path)
                db.session.rollback()
                return jsonify({'error': f'Erro ao salvar arquivo: {str(e)}'}), 500
            
        else:  # Upload múltiplo para compactação
            files = request.files.getlist('files[]')
            if not files or files[0].filename == '':
                return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
            
            # Verificar tamanho total dos arquivos
            total_size = 0
            for file in files:
                file.seek(0, os.SEEK_END)
                total_size += file.tell()
                file.seek(0)
            
            if total_size > 500 * 1024 * 1024:  # 500MB
                return jsonify({'error': 'Tamanho total dos arquivos excede 500MB'}), 400
            
            # Criar diretório temporário para os arquivos
            temp_dir = tempfile.mkdtemp()
            zip_path = None
            
            try:
                # Salvar arquivos temporariamente
                saved_files = []
                for file in files:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(temp_dir, filename)
                    file.save(file_path)
                    saved_files.append(file_path)
                
                # Criar nome personalizado para o arquivo ZIP
                base_filename = os.path.splitext(secure_filename(files[0].filename))[0]
                if len(files) > 1:
                    base_filename = f"{base_filename}_e_mais_{len(files)-1}_arquivos"
                zip_filename = f"dzip_{base_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{zip_filename}")
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, 9) as zipf:
                    for file_path in saved_files:
                        zipf.write(file_path, os.path.basename(file_path))
                
                # Criar registro no banco de dados
                share_link = str(uuid.uuid4())
                file_record = File(
                    filename=os.path.basename(zip_path),
                    original_filename=zip_filename,
                    file_path=zip_path,
                    share_link=share_link,
                    is_extracted=False,
                    extracted_files=None,
                    extracted_path=None
                )
                db.session.add(file_record)
                db.session.commit()
                
                return jsonify({
                    'message': 'Arquivos compactados com sucesso',
                    'share_link': share_link,
                    'expires_at': file_record.expires_at.strftime('%Y-%m-%d %H:%M:%S')
                })
                
            except Exception as e:
                # Limpar em caso de erro
                if zip_path and os.path.exists(zip_path):
                    os.remove(zip_path)
                db.session.rollback()
                return jsonify({'error': f'Erro ao compactar arquivos: {str(e)}'}), 500
                
            finally:
                # Limpar arquivos temporários
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 500

@app.route('/extract', methods=['POST'])
def extract():
    try:
        if 'zip_file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['zip_file']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if not file.filename.endswith('.zip'):
            return jsonify({'error': 'Apenas arquivos ZIP são suportados'}), 400
        
        # Verificar tamanho do arquivo
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        if size > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'error': 'Arquivo muito grande (máximo 100MB)'}), 400
        
        # Salvar arquivo temporariamente
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(temp_path)
        
        extract_dir = None
        try:
            # Extrair arquivos imediatamente
            extract_dir = os.path.join(app.config['EXTRACT_FOLDER'], str(uuid.uuid4()))
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Listar arquivos extraídos
            extracted_files = []
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    extracted_files.append({
                        'name': file,
                        'path': file_path,
                        'size': os.path.getsize(file_path)
                    })
            
            # Criar registro no banco de dados
            share_link = str(uuid.uuid4())
            file_record = File(
                filename=os.path.basename(temp_path),
                original_filename=filename,
                file_path=temp_path,
                share_link=share_link,
                is_extracted=True,
                extracted_files=extracted_files,
                extracted_path=extract_dir,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            db.session.add(file_record)
            db.session.commit()
            
            return jsonify({
                'message': 'Arquivo extraído com sucesso',
                'share_link': share_link,
                'expires_at': file_record.expires_at.strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except Exception as e:
            db.session.rollback()
            if extract_dir and os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            raise e
            
        finally:
            # Limpar arquivo temporário
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        return jsonify({'error': f'Erro ao extrair arquivo: {str(e)}'}), 500

@app.route('/extract/<share_link>')
def extract_file(share_link):
    try:
        file_record = File.query.filter_by(share_link=share_link).first_or_404()
        
        if datetime.utcnow() > file_record.expires_at:
            return jsonify({'error': 'Link expirado'}), 410
        
        if not file_record.is_extracted or not file_record.extracted_files:
            return jsonify({'error': 'Arquivo não foi extraído corretamente'}), 400
        
        return render_template('extracted.html', file_record=file_record)
        
    except Exception as e:
        return jsonify({'error': f'Erro ao acessar arquivo: {str(e)}'}), 500

@app.route('/download/extracted/<int:file_id>/<path:filename>')
def download_extracted_file(file_id, filename):
    file_record = File.query.get_or_404(file_id)
    
    if datetime.utcnow() > file_record.expires_at:
        return jsonify({'error': 'Link expirado'}), 410
    
    file_path = os.path.join(file_record.extracted_path, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'Arquivo não encontrado'}), 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename
    )

@app.route('/download/all/<int:file_id>')
def download_all_extracted(file_id):
    file_record = File.query.get_or_404(file_id)
    
    if datetime.utcnow() > file_record.expires_at:
        return jsonify({'error': 'Link expirado'}), 410
    
    # Criar arquivo ZIP temporário com todos os arquivos extraídos
    zip_filename = f"{uuid.uuid4()}.zip"
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, 9) as zipf:
        for file_info in file_record.extracted_files:
            zipf.write(file_info['path'], file_info['name'])
    
    return send_file(
        zip_path,
        as_attachment=True,
        download_name=f"extracted_files_{file_id}.zip"
    )

@app.route('/download/<share_link>')
def download_file(share_link):
    file_record = File.query.filter_by(share_link=share_link).first_or_404()
    
    if datetime.utcnow() > file_record.expires_at:
        return jsonify({'error': 'Link expirado'}), 410
    
    file_record.download_count += 1
    db.session.commit()
    
    return send_file(
        file_record.file_path,
        as_attachment=True,
        download_name=file_record.original_filename
    )

# Tarefa para limpar arquivos expirados
def cleanup_expired_files():
    with app.app_context():
        expired_files = File.query.filter(File.expires_at < datetime.utcnow()).all()
        for file in expired_files:
            if file.is_extracted and file.extracted_path:
                shutil.rmtree(file.extracted_path, ignore_errors=True)
            if os.path.exists(file.file_path):
                os.remove(file.file_path)
            db.session.delete(file)
        db.session.commit()

if __name__ == '__main__':
    # Inicializa o banco de dados automaticamente
    init_db()
    
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5009))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug) 