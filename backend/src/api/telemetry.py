import os
import logging

from azure.monitor.opentelemetry import configure_azure_monitor

logger = logging.getLogger("brand-guardian-telemetry")

def setup_telemetry():
    connection_string = os.getenv("AZURE_MONITOR_CONNECTION_STRING")
    if not connection_string:
        logger.warning("AZURE_MONITOR_CONNECTION_STRING is not set. Telemetry will not be sent.")
        return
    try:
        configure_azure_monitor(connection_string=connection_string
                                logger_name="brand-guardian-telemetry")
        logger.info("Azure Monitor telemetry configured successfully.")
    except Exception as e:
        logger.error(f"Failed to configure Azure Monitor telemetry: {e}")
        
