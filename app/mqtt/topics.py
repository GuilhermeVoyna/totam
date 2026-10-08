COMMAND_TOPIC = "pc/{hostname}/command"
BROADCAST_TOPIC = "pc/all/command"
STATUS_TOPIC = "pc/{hostname}/status"


def get_command_topic(hostname):
    return COMMAND_TOPIC.format(
        hostname=hostname
    )


def get_status_topic(hostname):
    return STATUS_TOPIC.format(
        hostname=hostname
    )