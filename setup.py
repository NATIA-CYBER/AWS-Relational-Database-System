from setuptools import setup, find_packages

setup(
    name="bdi_api",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.68.0",
        "uvicorn==0.15.0",
        "boto3==1.26.137",
        "psycopg2-binary==2.9.9",
        "python-dotenv==1.0.0",
        "pytest==7.3.1",
        "pytest-cov==4.0.0",
        "httpx==0.24.0",
        "sqlalchemy==2.0.15",
    ],
)
