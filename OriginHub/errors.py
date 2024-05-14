import websockets
import asyncio
import aiohttp
import json
import importlib
import kafka.errors

import websockets.exceptions

websockets_heartbeats_errors = (
    websockets.exceptions.ConnectionClosed, 
    websockets.exceptions.WebSocketException,
    websockets.exceptions.ConnectionClosedError,
    websockets.exceptions.InvalidHandshake,
    websockets.exceptions.SecurityError,
    websockets.exceptions.InvalidMessage,
    websockets.exceptions.InvalidHeader,
    websockets.exceptions.InvalidHeaderFormat,
    websockets.exceptions.InvalidHeaderValue,
    websockets.exceptions.InvalidOrigin,
    websockets.exceptions.InvalidUpgrade,
    websockets.exceptions.InvalidStatus,
    websockets.exceptions.InvalidStatusCode,
    websockets.exceptions.NegotiationError,
    websockets.exceptions.DuplicateParameter,
    websockets.exceptions.InvalidParameterName,
    websockets.exceptions.InvalidParameterValue,
    websockets.exceptions.AbortHandshake,
    websockets.exceptions.RedirectHandshake,
    websockets.exceptions.InvalidState,
    websockets.exceptions.InvalidURI,
    websockets.exceptions.PayloadTooBig,
    websockets.exceptions.ProtocolError,
    websockets.exceptions.WebSocketProtocolError,
    )

aiohttp_recoverable_errors = (
    ConnectionError,
    asyncio.TimeoutError,
    Exception,
    aiohttp.ClientResponseError,
    asyncio.CancelledError,
    aiohttp.ServerTimeoutError,
    json.JSONDecodeError,
    ValueError,
    TimeoutError
)


def get_kafka_errors():
    kafka_errors_module = importlib.import_module('kafka.errors')
    kafka_errors = {name: cls for name, cls in kafka_errors_module.__dict__.items() if isinstance(cls, type)}
    return kafka_errors
kafka_errors = get_kafka_errors()

reconnect_error_names = [
    "kafka_giveup_errors",  # Assuming this is a custom-defined error
    "KafkaTimeoutError",
    "KafkaConnectionError",
    "NotLeaderForPartitionError",
    "LeaderNotAvailableError",
    "NetworkException",
    "RetriableCommitFailedError",
    "RebalanceInProgressError",
    "CoordinatorLoadInProgress",
    "CoordinatorNotAvailable",
    "NotCoordinator",
    "UnknownServerException",
    "BrokerNotAvailableError",
    "ReplicaNotAvailableError",
    "RequestTimedOutError",
    "GroupLoadInProgressError",
    "GroupCoordinatorNotAvailableError",
    "NotCoordinatorForGroupError",
    "NotEnoughReplicasError",
    "NotEnoughReplicasAfterAppendError",
    "FetchSessionIdNotFoundError",
    "FencedLeaderEpochError",
    "UnknownTopicOrPartitionError",
    "OffsetOutOfRangeError",
]

send_error_names = [
    "UnknownTopicOrPartitionError",  # The specified topic or partition does not exist on this broker
    "MessageSizeTooLargeError",  # The message is too large to be sent
    "RecordListTooLargeError",  # The record list is too large
    "GroupAuthorizationFailedError",  # Authorization failed for the specified group
    "ClusterAuthorizationFailedError",  # Authorization failed for the cluster
    "TopicAuthorizationFailedError",  # Authorization failed for the topic
    "InvalidTopicError",  # The topic is invalid
    "CorruptRecordException",  # The record is corrupt
    "InvalidRequiredAcksError",  # Invalid required acknowledgments
    "NotEnoughReplicasError",  # Not enough replicas
    "NotEnoughReplicasAfterAppendError",  # Not enough replicas after appending
    "RequestTimedOutError",  # Request timed out
]

ignore_error_names_on_extraction = [
    "TopicAlreadyExistsError",
    "BrokerNotAvailableError", # used for different purpuse
    "KafkaError",
]

non_givup_errors = send_error_names+reconnect_error_names+ignore_error_names_on_extraction


kafka_restart_errors = list(kafka_errors[name] for name in reconnect_error_names if name in kafka_errors)
kafka_send_errors = tuple(kafka_errors[name] for name in send_error_names if name in kafka_errors)
kafka_giveup_errors = tuple(kafka_errors[name] for name in kafka_errors if name not in non_givup_errors)

kafka_restart_errors += [asyncio.TimeoutError, ConnectionError]
kafka_restart_errors = tuple(kafka_restart_errors)

print()