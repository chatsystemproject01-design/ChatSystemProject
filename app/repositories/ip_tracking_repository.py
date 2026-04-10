from app.models.ip_tracking import IPSecurityTracking
from app.repositories.base_repository import BaseRepository

class IPTrackingRepository(BaseRepository):
    def __init__(self):
        super().__init__(IPSecurityTracking)

    def get_by_ip(self, ip_address):
        return self.model.query.filter_by(ip_address=ip_address).first()
