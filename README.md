# StatLines Backend

A FastAPI-based backend service for football statistics and data analysis. This project scrapes football data, stores it in PostgreSQL, and provides REST API endpoints for data access and analysis.

## 🏗️ Project Architecture

- **FastAPI**: Modern Python web framework for building APIs
- **PostgreSQL**: Primary database for storing football statistics
- **SQLAlchemy**: ORM for database operations
- **Web Scrapers**: Automated data collection from football websites
- **Docker**: Optional containerization for production deployment

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL (local installation) OR Docker
- Git

## 🚀 Quick Start

### 1. Clone and Setup Virtual Environment

```bash
git clone <your-repo-url>
cd statlines_backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

Choose **ONE** of the following database setup options:

#### Option A: Local PostgreSQL (Recommended for Development)

1. **Install PostgreSQL** (if not already installed):
   ```bash
   # macOS
   brew install postgresql@15
   brew services start postgresql@15
   
   # Ubuntu/Debian
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   sudo systemctl start postgresql
   ```

2. **Setup Database**:
   ```bash
   # Run the setup script
   python setup_local_db.py
   ```

3. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env and use the Local PostgreSQL option
   ```

#### Option B: Docker PostgreSQL

1. **Start PostgreSQL Container**:
   ```bash
   cp .env.example .env
   # Edit .env and uncomment the Docker PostgreSQL section
   docker-compose up -d
   ```

### 4. Test Database Connection

```bash
python test_db.py
```

You should see output confirming the database connection and 20 teams loaded.

### 5. Start the API Server

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once running, access the interactive documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🗄️ Database Management

### View Database with DBeaver

Connect to your database using these settings:
- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `statlines_dev` (local) or `statlines` (Docker)
- **Username**: `postgres` (local) or `statlines_user` (Docker)
- **Password**: Your configured password

### Database Schema

- **Teams Table**: Premier League teams with names, short codes
- **Matches Table**: Match results, scores, statistics, xG data

## 🕷️ Web Scrapers

The project includes scrapers for collecting football data:

```bash
# Run specific scrapers (when available)
python scrapers/match_scraper.py
python scrapers/team_scraper.py
```

## 🔧 Development Commands

### Start Everything
```bash
# Start database (if using Docker)
docker-compose up -d

# Start API server
uvicorn main:app --reload
```

### Stop Everything
```bash
# Stop API server: Ctrl+C in terminal

# Stop Docker database
docker-compose down
```

### Database Operations
```bash
# Test database connection
python test_db.py

# Check PostgreSQL status (local)
brew services list | grep postgresql  # macOS
sudo systemctl status postgresql      # Linux

# Access PostgreSQL directly (local)
psql -U postgres -d statlines_dev
```

## 📁 Project Structure

```
statlines_backend/
├── database/           # Database models and configuration
│   ├── __init__.py
│   ├── models.py      # SQLAlchemy models (Team, Match)
│   └── config.py      # Database connection setup
├── scrapers/          # Web scraping modules
├── scripts/           # Utility scripts
├── test/             # Test files
├── main.py           # FastAPI application entry point
├── requirements.txt  # Python dependencies
├── docker-compose.yml # Docker configuration
├── .env.example      # Environment template
└── README.md         # This file
```

## 🌍 Environment Configuration

The project uses environment variables for configuration. Key files:

- **`.env.example`**: Template file (committed to git)
- **`.env`**: Your actual configuration (ignored by git)
- **`.env.local`**: Alternative local config (ignored by git)

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/db` |
| `ENVIRONMENT` | Application environment | `development` |
| `API_HOST` | API server host | `localhost` |
| `API_PORT` | API server port | `8000` |
| `LOG_LEVEL` | Logging level | `DEBUG` |

## 🐳 Docker Usage

### Development with Docker
```bash
# Start PostgreSQL only
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

### Production Deployment
```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d
```

## 🧪 Testing

```bash
# Test database connection
python test_db.py

# Run unit tests
python -m pytest test/
```

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check if PostgreSQL is running: `brew services list | grep postgresql`
   - Verify connection details in `.env`
   - Test connection: `python test_db.py`

2. **Docker Issues**
   - Ensure Docker is running
   - Check container status: `docker ps`
   - View logs: `docker-compose logs`

3. **Import Errors**
   - Activate virtual environment: `source venv/bin/activate`
   - Install dependencies: `pip install -r requirements.txt`

4. **Port Already in Use**
   - Change `API_PORT` in `.env`
   - Or stop conflicting process: `lsof -ti:8000 | xargs kill -9`

## 📊 Available Endpoints

- `GET /`: Welcome message
- `GET /health`: Health check endpoint
- `GET /teams`: List all teams
- `GET /matches`: List matches with filtering options

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

---

**Need Help?** Check the troubleshooting section or create an issue in the repository. 