from fastapi import FastAPI, Depends, HTTPException
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from typing import Dict, Any
from sqlalchemy import select, update, insert
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from ..settings import SessionLocal, settings
import boto3
import json
from datetime import datetime

app = FastAPI()
Base = declarative_base()

class AircraftStats(Base):
    __tablename__ = 'aircraft_stats'
    __table_args__ = (
        Index('idx_aircraft_stats_icao', 'icao'),
    )
    id = Column(Integer, primary_key=True)
    icao = Column(String(10), unique=True, index=True)  # Add index for faster lookups
    total_flights = Column(Integer)
    avg_altitude = Column(Float)
    avg_speed = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_s3_client():
    session = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )
    return session.client('s3')

@app.get("/aircraft/{icao}/stats")
def get_aircraft_stats(icao: str, db: Session = Depends(get_db)) -> Dict:
    """Get statistics for a specific aircraft by ICAO code."""
    stmt = select(
        AircraftStats.icao,
        AircraftStats.total_flights,
        AircraftStats.avg_altitude,
        AircraftStats.avg_speed
    ).where(AircraftStats.icao == icao)\
    .execution_options(index_copy=True)
    
    result = db.execute(stmt).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Aircraft not found")
    
    return {
        "icao": result.icao,
        "total_flights": result.total_flights,
        "avg_altitude": result.avg_altitude,
        "avg_speed": result.avg_speed
    }

@app.post("/process-s3-data")
def process_s3_data(
    db: Session = Depends(get_db),
    s3: Any = Depends(get_s3_client)
) -> Dict:
    logger.info(f"Using bucket: {settings.S3_BUCKET}")
    logger.info(f"Using region: {settings.AWS_REGION}")
    """Process aircraft data from S3 and store statistics in PostgreSQL."""
    try:
        response = s3.list_objects_v2(Bucket=settings.S3_BUCKET)
        if 'Contents' not in response:
            return {"message": "No files to process"}

        updates = []
        for obj in response['Contents']:
            data = s3.get_object(Bucket=settings.S3_BUCKET, Key=obj['Key'])
            flights = json.loads(data['Body'].read())

            for flight in flights:
                icao = flight.get('icao')
                if not icao:
                    continue

                # Get existing stats
                existing = db.execute(
                    select(AircraftStats).where(AircraftStats.icao == icao)
                ).scalar_one_or_none()

                if existing:
                    # Update existing stats
                    total_flights = existing.total_flights + 1
                    avg_altitude = (existing.avg_altitude * existing.total_flights + flight.get('altitude', 0)) / total_flights
                    avg_speed = (existing.avg_speed * existing.total_flights + flight.get('speed', 0)) / total_flights

                    stmt = update(AircraftStats)\
                        .where(AircraftStats.icao == icao)\
                        .values(
                            total_flights=total_flights,
                            avg_altitude=avg_altitude,
                            avg_speed=avg_speed,
                            updated_at=datetime.utcnow()
                        )
                    db.execute(stmt)
                    db.commit()
                else:
                    # Create new stats
                    stmt = insert(AircraftStats).values(
                            icao=icao,
                            total_flights=1,
                            avg_altitude=flight.get('altitude', 0),
                            avg_speed=flight.get('speed', 0)
                        )
                    db.execute(stmt)
                    db.commit()
                updates.append(icao)

        db.commit()
        return {"message": "Data processed successfully", "records_processed": len(updates)}

    except Exception as e:
        error_msg = f"Error processing S3 data: {str(e)}"
        logger.error(error_msg)
        db.rollback()
        raise HTTPException(status_code=500, detail=error_msg)

