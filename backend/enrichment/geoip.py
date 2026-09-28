import os
import ipaddress
import maxminddb
from backend.schema import IPEnrichment

class GeoIPEnricher:
    def __init__(self, city_db_path: str = "data/geolite/GeoLite2-City.mmdb", asn_db_path: str = "data/geolite/GeoLite2-ASN.mmdb"):
        self.city_db_path = city_db_path
        self.asn_db_path = asn_db_path
        
        self.city_reader = None
        self.asn_reader = None
        
        city_exists = os.path.exists(self.city_db_path)
        asn_exists = os.path.exists(self.asn_db_path)
        
        if city_exists:
            try:
                self.city_reader = maxminddb.open_database(self.city_db_path)
            except Exception:
                pass
                
        if asn_exists:
            try:
                self.asn_reader = maxminddb.open_database(self.asn_db_path)
            except Exception:
                pass
                
        if self.city_reader and self.asn_reader:
            self.status = "ENRICHED"
        elif self.city_reader or self.asn_reader:
            self.status = "PARTIAL"
        else:
            self.status = "NOT AVAILABLE"

    def close(self):
        if self.city_reader:
            self.city_reader.close()
        if self.asn_reader:
            self.asn_reader.close()

    def enrich_ip(self, ip_str: str) -> IPEnrichment:
        """
        Looks up an IP address (IPv4 or IPv6) and returns an IPEnrichment object.
        - Private/reserved/loopback IPs return None for geo_country and asn.
        - Unresolved IPs return None for geo_country and asn.
        - Malformed IPs raise ValueError.
        """
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            raise ValueError(f"Malformed IP address: {ip_str}")

        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_multicast or ip_obj.is_unspecified:
            return IPEnrichment(ip_address=ip_str, geo_country=None, asn=None)

        geo_country = None
        asn = None

        if self.city_reader:
            city_data = self.city_reader.get(ip_str)
            if city_data:
                country = city_data.get('country', {})
                geo_country = country.get('iso_code')

        if self.asn_reader:
            asn_data = self.asn_reader.get(ip_str)
            if asn_data:
                asn_num = asn_data.get('autonomous_system_number')
                if asn_num:
                    asn = f"AS{asn_num}"

        return IPEnrichment(ip_address=ip_str, geo_country=geo_country, asn=asn)
