# Release v1.0.0

## What's New

DZip is a modern web application for file compression, extraction, and sharing. This first release includes all core features and a stable, production-ready version.

### Key Features

- **File Sharing**
  - Upload files up to 100MB
  - Generate shareable links valid for 7 days
  - Automatic file deletion after expiration

- **File Compression**
  - Compress multiple files into a single ZIP
  - Support for up to 10 files (500MB total)
  - Custom naming for compressed files
  - Progress bar for compression status

- **File Extraction**
  - Extract ZIP files with automatic cleanup
  - Download individual files or all at once
  - Files available for 1 hour after extraction
  - Progress bar for extraction status

### Technical Improvements

- Modern, responsive UI with Tailwind CSS
- Drag and drop support
- Progress indicators
- Mobile-friendly interface
- Automatic database initialization
- Robust error handling
- Secure file handling

## Installation

1. Clone the repository:
```bash
git clone https://github.com/RunawayDevil/dzip.git
cd dzip
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5009`

## Requirements

- Python 3.8+
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Other dependencies listed in requirements.txt

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

- **RunawayDevil** - [GitHub Profile](https://github.com/RunawayDevil) 