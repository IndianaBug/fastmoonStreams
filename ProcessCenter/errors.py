import faust 

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

# logging, alerting, inspect these messages later, 
# Just log the message, log the error and proceed
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


# insert into database errors wrapper