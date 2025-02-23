import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os
from datetime import datetime

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mqtt_server import MQTTServer
from plant_controller import PlantController
from db_handler import DataBaseHandler


class MQTTServerIntegrationTest(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Create a mock MQTT client first
        self.mock_mqtt_client = Mock()
        with patch('paho.mqtt.client.Client', return_value=self.mock_mqtt_client):
            self.server = MQTTServer()
            self.server.client = self.mock_mqtt_client  # Ensure we use our mock

        # Sample sensor data that matches Arduino format
        self.sensor_data = {
            "id": 101,  # Added ID to match plant_id
            "moisture": 75,
            "temperature": 65,
            "humidity": 80,
            "light_level": 85,
            "timestamp": "2025-02-21 14:30:22"
        }

        # Sample plant settings that match database format
        self.plant_settings = {
            "plant_id": 101,
            "moisture_threshold": 70,
            "light_threshold": 80,
            "watering_duration": 5,
            "light_schedule_start": "2025-02-21 14:30:22",
            "light_schedule_end": "2025-02-21 16:30:22",
            "plant_type": "herbs",
            "ml_enabled": False
        }

    def test_sensor_data_validation(self):
        """Test that sensor data validation works correctly"""
        # Test valid data
        valid = self.server.validate_sensor_data(self.sensor_data)
        self.assertTrue(valid, "Valid sensor data should pass validation")

        # Test missing field
        invalid_data = self.sensor_data.copy()
        del invalid_data["moisture"]
        self.assertFalse(self.server.validate_sensor_data(invalid_data))

    @patch('paho.mqtt.client.Client')
    @patch.object(DataBaseHandler, 'store_sensor_data')
    @patch.object(DataBaseHandler, 'get_plant_settings')
    @patch.object(PlantController, 'get_control_decisions')
    def test_message_processing(self, mock_decisions, mock_get_settings, mock_store_data, mock_mqtt):
        """Test the complete message processing flow"""
        # Setup mock MQTT message
        mock_msg = Mock()
        mock_msg.topic = "garden/101/sensors"
        mock_msg.payload = json.dumps(self.sensor_data).encode()

        # Setup database mocks
        mock_store_data.return_value = None
        mock_get_settings.return_value = self.plant_settings

        # Setup mock decisions
        mock_decisions.return_value = [{
            "plant_id": 101,
            "water_pump": {"active": True, "duration": 5},
            "grow_light": {"active": True}
        }]

        # Process message
        self.server.on_message(self.mock_mqtt_client, mock_msg)

        # Verify sensor data was stored
        mock_store_data.assert_called_once_with(101, self.sensor_data)

        # Verify settings were retrieved
        mock_get_settings.assert_called_once_with(101)

        # Verify decision was requested
        mock_decisions.assert_called_once()

        # Verify control message was published
        self.mock_mqtt_client.publish.assert_called_once()

    def test_mqtt_connection(self):
        """Test MQTT connection handling"""
        with patch('paho.mqtt.client.Client', return_value=self.mock_mqtt_client) as mock_client:
            # Test connection
            self.server.client = self.mock_mqtt_client
            self.server.on_connect(self.mock_mqtt_client, None, flags={}, rc=0)  # Fixed signature

            # Verify subscription
            self.mock_mqtt_client.subscribe.assert_called_with(self.server.SENSOR_TOPIC)

            # Test disconnection handling
            self.server.on_disconnect(self.mock_mqtt_client, 1)
            self.mock_mqtt_client.reconnect.assert_called()

    def test_end_to_end_flow(self):
        """Test the entire flow from receiving sensor data to generating control decisions"""
        # Create a mock MQTT message
        mock_msg = Mock()
        mock_msg.topic = "garden/101/sensors"
        mock_msg.payload = json.dumps(self.sensor_data).encode()

        # Process the message
        with patch.object(DataBaseHandler, 'store_sensor_data') as mock_store:
            with patch.object(DataBaseHandler, 'get_plant_settings') as mock_settings:
                with patch.object(PlantController, 'get_rule_based_decisions') as mock_decisions:
                    # Setup the mocks
                    mock_settings.return_value = self.plant_settings
                    mock_decisions.return_value = [{
                        "plant_id": 101,
                        "water_pump": {"active": True, "duration": 5},
                        "grow_light": {"active": True}
                    }]

                    # Process message
                    self.server.on_message(self.mock_mqtt_client, mock_msg)

                    # Verify database interactions
                    mock_store.assert_called_once()
                    mock_settings.assert_called_once()
                    mock_decisions.assert_called_once()

                    # Verify MQTT publish
                    self.mock_mqtt_client.publish.assert_called_once()

                    # Verify published message format
                    call_args = self.mock_mqtt_client.publish.call_args
                    self.assertIsNotNone(call_args)
                    published_topic = call_args[0][0]
                    published_payload = json.loads(call_args[0][1])

                    self.assertEqual(published_topic, f"garden/101/control")
                    self.assertIn("water_pump", published_payload[0])
                    self.assertIn("grow_light", published_payload[0])


if __name__ == '__main__':
    unittest.main()