import threading
import time
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.analytics.analytics_service import AnalyticsService
from app.models import DashboardCache

class AnalyticsScheduler:
    def __init__(self, interval_seconds: int = 300):
        self.interval_seconds = interval_seconds
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()
        print("Analytics Scheduler started.")

    def stop(self):
        self.stop_event.set()
        self.thread.join()
        print("Analytics Scheduler stopped.")

    def _run(self):
        while not self.stop_event.is_set():
            self._update_cache()
            self.stop_event.wait(self.interval_seconds)

    def _update_cache(self):
        db = SessionLocal()
        try:
            service = AnalyticsService(db)
            dashboard_json = service.generate_dashboard_json()
            
            cache = db.query(DashboardCache).filter(DashboardCache.dashboard_key == "main").first()
            if not cache:
                cache = DashboardCache(dashboard_key="main")
                db.add(cache)
                
            cache.dashboard_json = dashboard_json
            cache.generated_at = datetime.utcnow()
            cache.expires_at = datetime.utcnow() + timedelta(seconds=self.interval_seconds + 30)
            
            db.commit()
            print(f"[{datetime.utcnow().isoformat()}] Analytics dashboard cache updated.")
        except Exception as e:
            db.rollback()
            print(f"Error updating analytics cache: {e}")
        finally:
            db.close()

# Global instance
scheduler = AnalyticsScheduler(interval_seconds=300)
