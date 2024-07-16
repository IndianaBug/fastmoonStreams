import faust 
import aiohttp

from faust.exceptions import (
    Skip, FaustWarning, AlreadyConfiguredWarning, FaustPredicate, SameNode, PartitionsMismatch
)
from faust.exceptions import (
    NotReady, ConsumerNotStarted
)

from faust.exceptions import (
    FaustPredicate, ValidationError, DecodeError, KeyDecodeError, ValueDecodeError, ProducerSendError
)

from faust.exceptions import (
    SecurityError, ImproperlyConfigured, ConsistencyError
)

# log and proceed
faust_proceed_errors = (
    Skip,
    FaustWarning,
    AlreadyConfiguredWarning,
    FaustPredicate,
    SameNode,
    PartitionsMismatch
)

faust_backup_errors = (
    NotReady, 
    ConsumerNotStarted, 
)

faust_message_errors = (
    FaustPredicate,
    ValidationError,   
    DecodeError,
    KeyDecodeError,
    ValueDecodeError,
    ProducerSendError,
)

# log, shutdown faust
faust_shutdown_errors = (
    SecurityError,
    ImproperlyConfigured,
    ConsistencyError,
)


ws_backoff_errors = (
    aiohttp.ClientConnectionError,
    aiohttp.ClientResponseError,
    aiohttp.WSServerHandshakeError
)

ws_unrecoverable_errors = (
    aiohttp.WSMsgType.CLOSE,
    aiohttp.WSMsgType.ERROR
)