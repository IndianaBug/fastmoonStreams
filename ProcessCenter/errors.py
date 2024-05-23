import faust 
import aiocouch
import aiohttp


# log and proceed
faust_proceed_errors = (
    faust.exceptions.Skip,
    faust.exceptions.FaustWarning,
    faust.exceptions.AlreadyConfiguredWarning,
    faust.exceptions.FaustPredicate,
    faust.exceptions.SameNode,
    faust.exceptions.PartitionsMismatch
)

faust_backup_errors = (
    faust.exceptions.NotReady, 
    faust.exceptions.ConsumerNotStarted, 
)

faust_message_errors = (
    faust.exceptions.FaustPredicate,
    faust.exceptions.ValidationError,   
    faust.exceptions.DecodeError,
    faust.exceptions.KeyDecodeError,
    faust.exceptions.ValueDecodeError,
    faust.exceptions.ProducerSendError,
)

# log, shutdown faust
faust_shutdown_errors = (
    faust.exceptions.SecurityError,
    faust.exceptions.ImproperlyConfigured,
    faust.exceptions.ConsistencyError,
)

db_backup_errors = (
    aiocouch.exception.UnauthorizedError,    
    aiocouch.exception.ConflictError,             
    aiocouch.exception.ExpectationFailedError,    
    aiohttp.ClientConnectionError,
    aiohttp.ClientResponseError
)
db_proceed_errors = (
    aiocouch.exception.BadRequestError,
    aiocouch.exception.ForbiddenError,
    aiocouch.exception.NotFoundError,
    aiocouch.exception.PreconditionFailedError,
    aiocouch.exception.UnsupportedMediaTypeError,
    KeyError,
    TypeError,
    Exception
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