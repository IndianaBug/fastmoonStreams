import websockets
import asyncio
import aiohttp
import json
import importlib
import aiokafka.errors as kafka

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

from kafka.errors import RETRY_ERROR_TYPES

kafka_reconnect_errors = RETRY_ERROR_TYPES

kafka_message_errors = (
    kafka.OffsetMetadataTooLargeError,
    kafka.StaleControllerEpochError,
    kafka.MessageSizeTooLargeError,
    kafka.ReplicaNotAvailableError,
    kafka.BrokerNotAvailableError,
    kafka.RequestTimedOutError,
    kafka.NotLeaderForPartitionError,
    kafka.InvalidRequiredAcksError,
    kafka.CorruptRecordException,
    kafka.InvalidTopicError,
    kafka.ClusterAuthorizationFailedError,
    kafka.GroupAuthorizationFailedError,
    kafka.RecordListTooLargeError,
    kafka.UnknownTopicOrPartitionError,
    kafka.TopicAuthorizationFailedError
)

restart_producer_errors = (
    kafka.NotEnoughReplicasError,
    kafka.NotEnoughReplicasAfterAppendError,
    kafka.InvalidReplicationFactorError,
    kafka.InvalidRequestError,
    kafka.UnsupportedVersionError,
    asyncio.TimeoutError,
    ConnectionError,
)

from kafka.errors import kafka_errors

kafka_giveup_errors = tuple(
    set(list(kafka_errors.values())) - set(restart_producer_errors) - set(kafka_reconnect_errors) - set(kafka_message_errors)
)







