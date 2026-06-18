import logging
import json
from sqlalchemy.orm import Session
from backend.app.core.database import WorldEvent, EventStore
from backend.app.services.world_model.ingestion import RSSIngestor, TrendFilter
from backend.app.services.world_model.relevance import RelevanceMatcher, StrategicAlertSystem
from backend.app.services.pcc.service import PCCService

logger = logging.getLogger(__name__)

# Default standard feeds to monitor
DEFAULT_FEEDS = [
    "https://hnrss.github.io/newest?q=AI",  # Mock AI Trend RSS
    "https://nvd.nist.gov/feeds/xml/cve/misc" # Mock CVE RSS
]

class WorldModelService:
    @staticmethod
    def ingest_feeds(db: Session, feed_urls: list[str] | None = None) -> dict:
        """
        Orchestrates WME feed scraping, classification, relevance mapping,
        strategic alerts registration, and PKG synchronization.
        """
        urls = feed_urls or DEFAULT_FEEDS
        logger.info(f"Initiating world model ingestion for {len(urls)} feeds.")
        
        events_ingested = 0
        alerts_triggered = []
        
        for url in urls:
            items = RSSIngestor.fetch_and_parse(url)
            for item in items:
                title = item["title"]
                desc = item["description"]
                src_url = item["source_url"]
                
                # 1. Deduplicate check (check if URL already logged)
                exists = db.query(WorldEvent).filter(WorldEvent.source_url == src_url).first()
                if exists:
                    continue
                    
                # 2. Classify event trend category
                category = TrendFilter.classify_item(title, desc)
                
                # 3. Score personal relevance
                relevance = RelevanceMatcher.score_relevance(db, title, desc)
                
                # 4. Save to relational DB world_events
                event_payload = {
                    "description": desc,
                    "relevance_score": relevance,
                    "pub_date": item.get("pub_date", "")
                }
                
                world_event = WorldEvent(
                    title=title,
                    category=category,
                    event_payload=event_payload,
                    source_url=src_url
                )
                db.add(world_event)
                db.commit()
                db.refresh(world_event)
                events_ingested += 1
                
                # 5. Process and trigger strategic alerts
                alert = StrategicAlertSystem.process_and_alert(
                    db=db,
                    world_event_id=str(world_event.id),
                    title=title,
                    description=desc,
                    category=category,
                    relevance_score=relevance,
                    source_url=src_url
                )
                if alert:
                    alerts_triggered.append(alert)
                    
                # 6. Synchronize with Personal Knowledge Graph if highly relevant
                if relevance >= 0.7:
                    try:
                        # Ensure user profile node exists
                        PCCService.upsert_node(db, "user_me", "user", "Owner Profile")
                        
                        # Add world event node
                        node_id = f"world_event_{world_event.id}"
                        PCCService.upsert_node(
                            db=db,
                            node_id=node_id,
                            node_type="world_event",
                            label=f"World Event: {title[:40]}...",
                            properties={
                                "category": category,
                                "relevance": relevance,
                                "url": src_url
                            }
                        )
                        
                        # Link user to event node
                        PCCService.upsert_edge(
                            db=db,
                            source_node_id="user_me",
                            relationship_type="RELEVANT_EVENT",
                            target_node_id=node_id,
                            weight=relevance
                        )
                    except Exception as e:
                        logger.error(f"Failed to sync WME event {world_event.id} to PKG: {e}")
                        
        # Log WME cycle event
        if events_ingested > 0 or alerts_triggered:
            event = EventStore(
                event_type="wme_ingestion_complete",
                payload={
                    "events_ingested": events_ingested,
                    "alerts_triggered_count": len(alerts_triggered)
                }
            )
            db.add(event)
            db.commit()
            
        return {
            "status": "success",
            "events_ingested": events_ingested,
            "alerts_triggered": alerts_triggered
        }
