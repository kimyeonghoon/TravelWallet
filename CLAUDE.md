# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Japan travel expense tracking application project. The codebase is currently empty and awaiting initial setup.

## Development Setup

### Git Repository
- Repository: https://github.com/kimyeonghoon/JAPAN_TRAVEL_EXPENSE.git
- Main branch: `main`
- Git user configured as: 김영훈 <me@yeonghoon.kim>

### Technology Stack
- **Backend**: Python FastAPI
- **Frontend**: HTML/CSS/JavaScript with jQuery and Bootstrap 5
- **Styling**: Bootstrap 5 + Custom CSS
- **Data Storage**: SQLite database with persistent volume
- **Deployment**: Docker Compose ready

### Development Commands
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run development server
python main.py
# or
uvicorn main:app --reload

# Access application
# Frontend: http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild after changes
docker-compose up --build --force-recreate
```

### Common Git Commands
```bash
git status                  # Check repository status
git add .                   # Stage all changes
git commit -m "message"     # Commit changes
git push origin main        # Push to GitHub
git pull origin main        # Pull latest changes
```

## Project Structure

```
japan_travel_expense/
├── main.py                 # FastAPI main application
├── models.py              # SQLAlchemy database models
├── database.py            # Database service layer
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker container configuration
├── docker-compose.yml     # Docker Compose setup
├── .dockerignore          # Docker ignore file
├── templates/
│   └── index.html         # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css      # Custom styles
│   └── js/
│       └── app.js         # jQuery application logic
├── data/                  # SQLite database directory (Docker volume)
└── .claude/               # Claude Code configuration
```

## Architecture

- **Frontend**: Single-page application using jQuery and Bootstrap
- **Backend**: FastAPI serves templates and provides REST API endpoints
- **Database**: SQLite with SQLAlchemy ORM for data persistence
- **Container**: Docker with persistent volume for database storage
- **Responsive Design**: Mobile-first approach with Bootstrap grid system

## Current Status

- ✅ Git repository initialized and connected to GitHub
- ✅ Technology stack configured (FastAPI + jQuery + Bootstrap + SQLite)
- ✅ Project structure created with all necessary files
- ✅ Frontend UI implemented with mobile responsive design
- ✅ Complete REST API implementation with database integration
- ✅ SQLite database with SQLAlchemy ORM
- ✅ Docker containerization with Docker Compose
- ✅ Production-ready deployment configuration

## Notes

- Project directory: `C:\workspace\japan_travel_expense`
- Repository URL: https://github.com/kimyeonghoon/JAPAN_TRAVEL_EXPENSE.git
- Claude Code permissions configured for git operations