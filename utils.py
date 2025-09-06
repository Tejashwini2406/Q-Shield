import psutil
from sqlalchemy import text

#♡ Example geo-fence
GEOFENCE = {
    "lat_min": 12.90,
    "lat_max": 13.10,
    "lon_min": 77.50,
    "lon_max": 77.70
}

#♡ Get CPU, Memory, DB stats
def get_metrics(db):
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    db_count = db.execute(text("SELECT COUNT(*) FROM devices")).scalar()
    return cpu, mem, db_count

#♡ Check geofence
def check_geofence(lat, lon):
    return GEOFENCE["lat_min"] <= lat <= GEOFENCE["lat_max"] and \
           GEOFENCE["lon_min"] <= lon <= GEOFENCE["lon_max"]
