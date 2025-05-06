# FastAPI S3 Data Processing Service

## AWS Architecture

```
                                 AWS Cloud (us-east-1)
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│  VPC (10.0.0.0/16)                                                    │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                                                                │   │
│  │  Public Subnet                     Private Subnet              │   │
│  │  ┌──────────────┐                 ┌─────────────┐            │   │
│  │  │EC2 Instance  │                 │   RDS       │            │   │
│  │  │t2.micro      │Security         │  ┌───────┐  │            │   │
│  │  │  ┌────────┐  │Group           │  │Postgre│  │            │   │
│  │  │  │FastAPI │──┼─────────────────▶  │SQL DB │  │            │   │
│  │  │  └────────┘  │Allow:5432      │  └───────┘  │            │   │
│  │  │              │                 │             │            │   │
│  │  └─────┬────────┘                 └─────────────┘            │   │
│  │        │                          Not Public                 │   │
│  │        │                          Accessible                 │   │
│  └────────┼──────────────────────────────────────────────────────┘   │
│           │                                                          │
│           │          ┌─────────────┐                                 │
│           └─────────▶│ S3 Bucket   │                                 │
│                     │aircraft-data │                                 │
│                     │  ┌───────┐   │                                 │
│                     │  │Flight │   │                                 │
│                     │  │ Data  │   │                                 │
│                     │  └───────┘   │                                 │
│                     └─────────────┘                                 │
└────────────────────────────────────────────────────────────────────────┘

Components and Configuration:

1. EC2 Instance (Public Subnet):
   - Instance Type: t2.micro
   - OS: Amazon Linux 2
   - Security Group:
     * Inbound: HTTP (80), HTTPS (443) from Internet
     * Outbound: All traffic to RDS (5432), S3 (443)
   - IAM Role: EC2-S3-Access
   - Hosts: FastAPI application

2. RDS PostgreSQL (Private Subnet):
   - Instance: db.t3.micro
   - Multi-AZ: No (Development)
   - Security Group:
     * Inbound: PostgreSQL (5432) from EC2 SG only
     * Outbound: None
   - Not Publicly Accessible
   - Storage: 20GB gp2
   - Database: aircraft_db

3. S3 Bucket (aircraft-data):
   - Access: Private
   - Versioning: Enabled
   - Access Control:
     * IAM Role attached to EC2
     * Read-only permissions
   - Contents: Flight data JSON files

Network Flow:
1. Client → EC2: HTTPS requests to API endpoints
2. EC2 → RDS: Secure database queries (5432)
3. EC2 → S3: HTTPS requests for flight data
4. EC2 → Client: JSON responses (<20ms latency)

Security Measures:
- EC2 in public subnet with restricted SG
- RDS in private subnet, no public access
- S3 access via IAM roles only
- All credentials in environment variables
- HTTPS for all external communication
```


This project implements a FastAPI service that processes aircraft data from AWS S3 and stores statistics in a PostgreSQL database.

## Features

- Process S3 data endpoint (`/process-s3-data`)
- Retrieve aircraft statistics endpoint (`/aircraft-stats/{icao}`)
- PostgreSQL database integration
- AWS S3 integration
- Comprehensive test suite with mocked AWS services

## Prerequisites

- Docker and Docker Compose
- Python 3.11+

## Project Structure

```
├── bdi_api/
│   ├── s7/
│   │   ├── api.py         # Main FastAPI application
│   │   └── __init__.py
│   ├── settings.py        # Application settings
│   └── __init__.py
├── tests/
│   ├── s7/
│   │   ├── test_api.py   # API tests
│   │   └── conftest.py   # Test fixtures
│   └── __init__.py
├── docker-compose.yml     # Docker configuration
├── Dockerfile            # API service build configuration
└── requirements.txt      # Python dependencies
```

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd aws_assignment
```

2. Set up AWS credentials:
   - Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   - Edit `.env` and add your AWS credentials:
     - AWS_ACCESS_KEY_ID
     - AWS_SECRET_ACCESS_KEY
     - AWS_REGION (default: us-east-1)
     - S3_BUCKET (your S3 bucket name)

3. Start the services:
```bash
docker compose up -d
```

4. The API will be available at `http://localhost:8001`
   - Interactive API documentation: `http://localhost:8001/docs`
   - Alternative API documentation: `http://localhost:8001/redoc`

## API Endpoints

### Process S3 Data
- **URL**: `/process-s3-data`
- **Method**: POST
- **Description**: Processes aircraft data from S3 and stores statistics in the database

### Get Aircraft Statistics
- **URL**: `/aircraft-stats/{icao}`
- **Method**: GET
- **Parameters**: `icao` - Aircraft ICAO code
- **Description**: Retrieves stored statistics for a specific aircraft

## Running Tests

To run the test suite:

```bash
docker compose exec api python -m pytest tests/s7/test_api.py -v
```

## Environment Variables

The following environment variables are used:

```
# PostgreSQL credentials
DB_HOST=aircraft-db
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=aircraft_db

# AWS credentials
# Configure your AWS credentials in environment variables
```

## Development

The project uses:
- FastAPI for the web framework
- SQLAlchemy for database operations
- Pytest for testing
- Boto3 for AWS S3 interactions

All AWS S3 interactions are mocked in tests to prevent actual AWS calls.

## Notes

- Configure proper AWS credentials for production use
- The database is automatically initialized when the containers start

## AWS Security Configuration

### EC2 Security Group
- Inbound Rules:
  - Port 8000: API access
  - Source: 0.0.0.0/0 (for demonstration, restrict in production)
- Outbound Rules:
  - Port 5432: to RDS Security Group
  - Port 443: to S3

### RDS Security Group
- Inbound Rules:
  - Port 5432: from EC2 Security Group only
- Security Features:
  - No public IP
  - No public access
  - Located in private subnet

### S3 Configuration
- Bucket Policy:
  - Private access only
  - Access through EC2 IAM role
  - No public access

### Network Security
- VPC Configuration:
  - EC2 in public subnet (with internet access)
  - RDS in private subnet (no internet access)
  - Proper route tables and NACLs
