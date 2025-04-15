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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
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
        file.save(file_path)
        
        try:
            # Criar registro no banco de dados
            share_link = str(uuid.uuid4())
            file_record = File(
                filename=os.path.basename(file_path),
                original_filename=filename,
                file_path=file_path,
                share_link=share_link,
                is_extracted=False
            )
            db.session.add(file_record)
            db.session.commit()
            
            return jsonify({
                'message': 'Arquivo enviado com sucesso',
                'share_link': share_link,
                'expires_at': file_record.expires_at.strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'error': 'Erro ao processar arquivo'}), 500
    
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
        try:
            # Salvar arquivos temporariamente
            saved_files = []
            for file in files:
                filename = secure_filename(file.filename)
                file_path = os.path.join(temp_dir, filename)
                file.save(file_path)
                saved_files.append(file_path)
            
            # Criar arquivo ZIP
            zip_filename = f"{uuid.uuid4()}.zip"
            zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, 9) as zipf:
                for file_path in saved_files:
                    zipf.write(file_path, os.path.basename(file_path))
            
            # Criar registro no banco de dados
            share_link = str(uuid.uuid4())
            file_record = File(
                filename=zip_filename,
                original_filename=f"arquivos_compactados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                file_path=zip_path,
                share_link=share_link,
                is_extracted=False
            )
            db.session.add(file_record)
            db.session.commit()
            
            # Limpar arquivos temporários
            shutil.rmtree(temp_dir)
            
            return jsonify({
                'message': 'Arquivos compactados com sucesso',
                'share_link': share_link,
                'expires_at': file_record.expires_at.strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except Exception as e:
            # Limpar em caso de erro
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            if os.path.exists(zip_path):
                os.remove(zip_path)
            return jsonify({'error': 'Erro ao compactar arquivos'}), 500

@app.route('/extract', methods=['POST'])
def extract():
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
        # Criar registro no banco de dados
        share_link = str(uuid.uuid4())
        file_record = File(
            filename=os.path.basename(temp_path),
            original_filename=filename,
            file_path=temp_path,
            share_link=share_link,
            is_extracted=False
        )
        db.session.add(file_record)
        db.session.commit()
        
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
        
        # Atualizar registro no banco de dados
        file_record.is_extracted = True
        file_record.extracted_files = extracted_files
        file_record.extracted_path = extract_dir
        file_record.expires_at = datetime.utcnow() + timedelta(hours=1)  # Expira em 1 hora
        db.session.commit()
        
        return jsonify({
            'message': 'Arquivo extraído com sucesso',
            'share_link': share_link,
            'expires_at': file_record.expires_at.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        # Limpar em caso de erro
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if extract_dir and os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        return jsonify({'error': 'Erro ao extrair arquivo'}), 500

@app.route('/extract/<share_link>')
def extract_file(share_link):
    file_record = File.query.filter_by(share_link=share_link).first_or_404()
    
    if datetime.utcnow() > file_record.expires_at:
        return jsonify({'error': 'Link expirado'}), 410
    
    return render_template('extracted.html', file_record=file_record)

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
    with app.app_context():
        db.create_all()
    
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5009))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug) 