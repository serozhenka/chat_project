from enum import Enum

class FriendRequestStatus(Enum):
    THEM_SENT_TO_YOU = -1
    NO_REQUEST_SENT = 0
    YOU_SENT_TO_THEM = 1