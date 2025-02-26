"""
ManusService Module

This module implements the GRPC service for managing DexHand sensors. It provides functionality
for creating, reading, updating, and deleting sensors, as well as handling sensor data.

The module consists of three main classes:
- Sensor: Data model representing a sensor
- SensorController: Business logic for sensor management
- ManusService: GRPC service implementation
"""

import logging
import time
from uuid import uuid4
from grpc import ServicerContext, StatusCode
from client.ts import dexhand
from client.ts.dexhand.v1.manus_pb2 import (
    CreateSensorRequest,
    DeleteSensorRequest,
    GetSensorRequest,
    ListSensorsRequest,
    ListSensorsResponse,
    SetSensorDataRequest,
    UpdateSensorRequest,
    Sensor as SensorProto,
    SensorData as SensorDataProto,
)
from client.ts.dexhand.v1.manus_pb2_grpc import ManusServiceServicer
from dexhand_manager.models.dexhand_controller import DexHandController
from typing import List

LOG = logging.getLogger(__name__)


class Sensor:
    """
    Represents a sensor entity with its properties and data.

    Attributes:
        id (str): Unique identifier for the sensor
        name (str): Display name of the sensor
        type (str): Type classification of the sensor
        data (List[float]): Latest sensor readings
    """

    id: str
    name: str
    type: str
    data: List[float]

    def __init__(self, id: str, name: str, type: str) -> None:
        self.id = id
        self.name = name
        self.type = type
        self.data = []

    @classmethod
    def from_proto(cls, sensor_proto: SensorProto) -> "Sensor":
        """
        Creates a Sensor instance from a protobuf message.

        Args:
            sensor_proto (SensorProto): Protobuf message containing sensor data

        Returns:
            Sensor: New sensor instance
        """
        return cls(
            name=sensor_proto.name,
            type=sensor_proto.type,
            id=sensor_proto.id if sensor_proto.id else str(uuid4()),
        )

    def to_proto(self) -> SensorProto:
        """
        Converts the sensor instance to a protobuf message.

        Returns:
            SensorProto: Protobuf representation of the sensor
        """
        return SensorProto(
            id=self.id,
            name=self.name,
            type=self.type,
        )


class SensorController:
    """
    Manages the lifecycle and data of sensors.

    This class handles the business logic for sensor operations including
    CRUD operations and data retrieval.

    Attributes:
        sensors (dict[str, Sensor]): Dictionary of active sensors indexed by their IDs
    """

    sensors: dict[str, Sensor]

    def __init__(self):
        self.sensors = {}

    def list(self) -> List[Sensor]:
        """Returns all registered sensors."""
        LOG.info("List sensors")

        return list(self.sensors.values())

    def get(self, id: str) -> Sensor:
        """
        Retrieves a specific sensor by ID.

        Args:
            id (str): Sensor identifier

        Returns:
            Sensor: The requested sensor

        Raises:
            ValueError: If sensor with given ID doesn't exist
        """
        LOG.info(f"Get sensor: {id}")

        if id not in self.sensors:
            raise ValueError(f"Sensor {id} not found.")

        return self.sensors[id]

    def create(self, sensorProto: SensorProto) -> Sensor:
        """
        Creates a new sensor from protobuf data.

        Args:
            sensorProto (SensorProto): Sensor definition in protobuf format

        Returns:
            Sensor: Newly created sensor instance
        """
        LOG.info(f"Create sensor: {sensorProto}")
        new_sensor = Sensor.from_proto(sensorProto)
        self.sensors[new_sensor.id] = new_sensor
        return new_sensor

    def update(self, sensorProto: SensorProto) -> Sensor:
        """
        Updates an existing sensor.

        Args:
            sensorProto (SensorProto): Updated sensor data

        Returns:
            Sensor: Updated sensor instance

        Raises:
            ValueError: If sensor with given ID doesn't exist
        """
        LOG.info(f"Update sensor: {sensorProto}")

        if sensorProto.id not in self.sensors:
            raise ValueError(f"Sensor {sensorProto.id} not found.")

        sensor = Sensor.from_proto(sensorProto)
        self.sensors[sensor.id] = sensor
        return sensor

    def delete(self, id: str) -> None:
        """
        Removes a sensor from the system.

        Args:
            id (str): ID of sensor to delete

        Raises:
            ValueError: If sensor with given ID doesn't exist
        """
        LOG.info(f"Delete sensor: {id}")

        if id not in self.sensors:
            raise ValueError(f"Sensor {id} not found.")

        del self.sensors[id]

    def get_latest_data(self, id: str) -> List[float]:
        """
        Retrieves the most recent sensor readings.

        Args:
            id (str): Sensor identifier

        Returns:
            List[float]: Latest sensor data points

        Raises:
            ValueError: If sensor with given ID doesn't exist
        """
        LOG.info(f"Get latest data: {id}")

        if id not in self.sensors:
            raise ValueError(f"Sensor {id} not found.")

        return self.sensors[id].data


class ManusService(ManusServiceServicer):
    """
    GRPC service implementation for the Manus API.

    This class implements the protobuf-defined service interface for sensor management.
    It delegates business logic to the SensorController.

    Attributes:
        controller (SensorController): Backend controller handling sensor operations
    """

    controller: SensorController

    def __init__(self, controller: SensorController):
        self.controller = controller

    def ListSensors(self, request: ListSensorsRequest, context: ServicerContext):
        """
        GRPC endpoint to list all sensors.

        Args:
            request (ListSensorsRequest): Client request (currently unused)
            context (ServicerContext): GRPC service context

        Returns:
            ListSensorsResponse: List of all sensors
        """
        LOG.info(f"Get ListSensors request: {request}")

        if not self.controller:
            LOG.error("Manus is not initialized.")
            context.set_code(StatusCode.UNAVAILABLE)
            context.set_details("sensor is not initialized yet.")

        else:
            return ListSensorsResponse(
                sensors=[sensor.to_proto() for sensor in self.controller.list()]
            )

    def GetSensor(self, request: GetSensorRequest, context: ServicerContext):
        """
        GRPC endpoint to retrieve a specific sensor by ID.

        Args:
            request (GetSensorRequest): Client request containing sensor ID
            context (ServicerContext): GRPC service context

        Returns:
            SensorProto: Protobuf representation of the requested sensor
        """
        LOG.info(f"Get GetSensor request: {request}")

        if not self.controller:
            LOG.error("Manus is not initialized.")
            context.set_code(StatusCode.UNAVAILABLE)
            context.set_details("sensor is not initialized yet.")

        else:
            sensor = self.controller.get(request.id)
            return sensor.to_proto()

    def CreateSensor(self, request: CreateSensorRequest, context: ServicerContext):
        """
        GRPC endpoint to create a new sensor.

        Args:
            request (CreateSensorRequest): Client request containing sensor data
            context (ServicerContext): GRPC service context

        Returns:
            SensorProto: Protobuf representation of the created sensor
        """
        LOG.info(f"Get CreateSensor request: {request}")

        if not self.controller:
            LOG.error("Manus is not initialized.")
            context.set_code(StatusCode.UNAVAILABLE)
            context.set_details("sensor is not initialized yet.")
        else:
            sensor = self.controller.create(request.sensor)
            return sensor.to_proto()

    def UpdateSensor(self, request: UpdateSensorRequest, context: ServicerContext):
        """
        GRPC endpoint to update an existing sensor.

        Args:
            request (UpdateSensorRequest): Client request containing updated sensor data
            context (ServicerContext): GRPC service context

        Returns:
            SensorProto: Protobuf representation of the updated sensor
        """
        LOG.info(f"Get UpdateSensor request: {request}")

        if not self.controller:
            LOG.error("Manus is not initialized.")
            context.set_code(StatusCode.UNAVAILABLE)
            context.set_details("sensor is not initialized yet.")
        else:
            sensor = self.controller.update(request.sensor)
            return sensor.to_proto()

    def DeleteSensor(self, request: DeleteSensorRequest, context: ServicerContext):
        """
        GRPC endpoint to delete a sensor by ID.

        Args:
            request (DeleteSensorRequest): Client request containing sensor ID
            context (ServicerContext): GRPC service context
        """
        LOG.info(f"Get DeleteSensor request: {request}")

        if not self.controller:
            LOG.error("Manus is not initialized.")
            context.set_code(StatusCode.UNAVAILABLE)
            context.set_details("sensor is not initialized yet.")
        else:
            self.controller.delete(request.id)
            return

    def SetSensorData(self, request: SetSensorDataRequest, context: ServicerContext):
        """
        GRPC endpoint to set sensor data.

        Args:
            request (SetSensorDataRequest): Client request containing sensor data
            context (ServicerContext): GRPC service context

        Returns:
            SensorDataProto: Protobuf representation of the sensor data
        """
        LOG.info(f"Get SetSensorData request: {request}")

        if not self.controller:
            LOG.error("Manus is not initialized.")
            context.set_code(StatusCode.UNAVAILABLE)
            context.set_details("sensor is not initialized yet.")
        else:
            data = self.controller.get_latest_data(request.id)

            return SensorDataProto(
                id=request.id,
                timestamp=time.time_ns(),
                num_sequence=0,
                num_data=len(data),
                data=data,
            )
