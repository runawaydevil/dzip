from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
import os
import magic
from werkzeug.utils import secure_filename
import pyminizip
import rarfile
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///dzip.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_UPLOAD_SIZE', 500 * 1024 * 1024))  # 500MB
app.config['ALLOWED_EXTENSIONS'] = {'zip', 'rar'}

# Criar diretório de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=int(os.environ.get('LINK_EXPIRATION_DAYS', 7))))
    download_count = db.Column(db.Integer, default=0)
    share_link = db.Column(db.String(255), unique=True)

    def __repr__(self):
        return f'<File {self.filename}>'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files[]' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    files = request.files.getlist('files[]')
    
    max_files = int(os.environ.get('MAX_FILES_PER_UPLOAD', 100))
    if len(files) > max_files:
        return jsonify({'error': f'Máximo de {max_files} arquivos permitidos'}), 400
    
    # Verificar tamanho total dos arquivos
    total_size = sum(len(file.read()) for file in files)
    if total_size > app.config['MAX_CONTENT_LENGTH']:
        return jsonify({'error': 'Tamanho total dos arquivos excede 500MB'}), 400
    
    # Reset file pointers
    for file in files:
        file.seek(0)
    
    # Gerar nome único para o arquivo zip
    zip_filename = f"{uuid.uuid4()}.zip"
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
    
    # Lista de arquivos para compactar
    files_to_zip = []
    for file in files:
        if file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            files_to_zip.append(file_path)
    
    # Compactar arquivos
    pyminizip.compress_multiple(files_to_zip, [], zip_path, "", 5)
    
    # Criar registro no banco de dados
    share_link = str(uuid.uuid4())
    file_record = File(
        filename=zip_filename,
        original_filename=files[0].filename,
        file_path=zip_path,
        share_link=share_link
    )
    db.session.add(file_record)
    db.session.commit()
    
    # Limpar arquivos temporários
    for file_path in files_to_zip:
        os.remove(file_path)
    
    return jsonify({
        'message': 'Arquivos compactados com sucesso',
        'share_link': share_link
    })

@app.route('/download/<share_link>')
def download_file(share_link):
    file_record = File.query.filter_by(share_link=share_link).first_or_404()
    
    if datetime.utcnow() > file_record.expires_at:
        return jsonify({'error': 'Link expirado'}), 410
    
    file_record.download_count += 1
    db.session.commit()
    
    # Retorna o arquivo ZIP compactado
    return send_file(
        file_record.file_path,
        as_attachment=True,
        download_name=f"{file_record.original_filename}.zip"  # Garante que o arquivo baixado tenha extensão .zip
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    host = os.environ.get('HOST', '0.0.0.0')
    port = 5009  # Forçando a porta 5009
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug) 