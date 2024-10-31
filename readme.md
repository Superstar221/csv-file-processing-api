# CSV File Processing API

A Django REST API for processing and analyzing CSV files with automatic type inference and validation.

## Features

- Upload and validate CSV files
- Automatic data type inference for columns
- File validation (size, format, rows/columns limits)
- Sample data preview
- Column statistics (null counts, unique values, min/max values)
- Support for multiple file encodings
- Batch processing capabilities
- Export functionality for processed data

## Requirements

- Python 3.8+
- Django 4.2+
- Django REST Framework 3.14+
- Pandas 2.0+
- Additional dependencies in `requirements.txt`

## Quick Start

1. Clone and setup:
```bash
git clone https://github.com/Superstar221/csv-file-processing-api.git
cd csv-file-processing-api

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate
```

2. Start the server:
```bash
python manage.py runserver
```

3. Access the API at: `http://localhost:8000/api/`

## API Documentation

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/files/` | GET | List all files |
| `/api/files/` | POST | Upload new file |
| `/api/files/{id}/` | GET | Get file details |
| `/api/files/{id}/` | PUT | Update file details |
| `/api/files/{id}/` | PATCH | Partially update file details |
| `/api/files/{id}/` | DELETE | Remove file |
| `/api/files/{id}/process_file/` | POST | Process and analyze file contents |

## Production Deployment

1. Security checklist:
- [ ] Change `SECRET_KEY` in settings.py
- [ ] Disable `DEBUG` mode
- [ ] Configure proper CORS settings
- [ ] Set up production database
- [ ] Configure proper static/media file serving
- [ ] Set up proper authentication

## License

This project is licensed under the MIT License - see the LICENSE file for details.
