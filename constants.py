import pytz
from enum import Enum

class UserRoles(Enum):
    ADMIN_OBSERVER = 60,
    ADMINISTRATOR_TL = 62,
    ADMINISTRATOR = 1,
    ASSESSMENT_SERVICES_MANAGER = 52,
    ASSESSMENT = 45,
    DON_T_USE_THIS = 61,
    ETS_SUPPORT_ROLE = 103,
    ETS_TEST = 67,
    EXAM_PROCTOR = 3,
    ILO_STUDENT_ADVOCATE = 106,
    INCIDENT_REVIEWER = 69,
    INCIDENT_USER = 104,
    INSTITUTION_ADMINISTRATOR = 53,
    INSTITUTION_EXAM_ADMINISTRATOR = 65,
    INSTITUTION_INSTRUCTOR_AUTO_ONLY = 63,
    INSTITUTION_INSTRUCTOR_OBSERVER = 58,
    INSTITUTION_INSTRUCTOR = 54,
    INSTITUTION_OBSERVER = 39,
    INSTITUTION_USER_EDITOR = 66,
    MANAGER = 42,
    MEDIA = 55,
    ORIENTATION = 47,
    PARTNERSHIPS = 57,
    PHONES_ALTERNATE = 56,
    PHONES = 51,
    PLACEHOLDER = 23,
    QC_AUDIT = 49,
    QC_INCIDENT_REPORTS = 50,
    QC_TRAINER = 48,
    REVIEWER = 64,
    STUDENT_ADVOCATE = 41,
    STUDENT = 4,
    SUPER_ADMINISTRATOR = 43,
    SUPER_MANAGER = 59,
    SUPPORT_LEVEL_1 = 107,


class Domains(Enum):
    STAGING = 'https://staging.proctoru.com/'
    PRODUCTION = 'https://go.proctoru.com/'
    DEMO = 'https://demo.proctoru.com/'


class TimeZones(Enum):
    US_CENTRAL = pytz.timezone('America/Chicago')

class ErrorMessages(Enum):
    TIME_IN_PAST = 'It appears the time you selected is in the past. Please search again.'
    LOGGING_IN = 'Error while logging in. Please try again.'
    UNAUTHENTICATED = 'Unauthenticated. Please review the cookies and try again.'
    REQUEST_EXCEPTION = 'Error sending request for url: {url} \nwith headers: {headers} \nand cookies: {cookies}'
    SLOT_NOT_AVAILABLE = 'There is no slot available for {month} {day}, {year_short} @ {schedule_time}, \nGrabbing a random authenticity_token'
    USER_CREATION = 'Error creating user name {sequence}'
    USER_UPDATE = 'Error updating user {user}'
    USER_ALREADY_HAS_PATTERN = 'User {user_name} already has the pattern {user_name_pattern}'
    NO_SEQUENCE_FOUND = 'No sequence found for user {user_name}. User name not updated'
    APPOINTMENT_NOT_SCHEDULED = 'Couldn\'t schedule exam for user {username} @ {schedule_date}'
    IMPERSONATION_COOKIES = 'Error getting impersonation cookies for user {username}'
    DATE_FORMAT = 'Schedule date {schedule_date} format is not correct. Should be YYYY-MM-DD HH:MM'


class ReservationStatus(Enum):
    PENDING = 'pending'
    CANCELLED = 'cancelled'
    FULFILLED = 'fulfilled'
    SCHEDULED = 'scheduled'
    RUNNING = 'running'
    ABORTED = 'aborted'

class Regions(Enum):
    """ Regions available in our solution"""
    US_WEST = 'us-west-2'
    CA = 'ca-central-1'
    EUROPE = 'eu-central-1'
    ASIA_PACIFIC = 'ap-southeast-1'

SELF_HEALING_PAIRS = {
    'WEBCAM_VIDEO_IS_BAD': 'WEBCAM_VIDEO_IS_RESTORED',
    'WEBCAM_VARIANCE_TOO_LOW': 'WEBCAM_VARIANCE_LOW_RECOVERED',
    'AV_STREAM_STOPPED': 'AV_STREAM_REPLACED',
    # 'WEBCAM_VIDEO_IS_CLOSED': ''
}

CRITICAL_ERRORS = [
    'ERROR',
    'INPUT_PERMISSION_DENIED'
]

INITIALIZATION_EVENTS = {
    ('CJS_INITIALIZED', None),
    ('ROOM_INITIALIZED', None),
    ('AV_STREAM_STARTED', 'media.webcam'),
    ('AV_STREAM_STARTED', 'media.screen'),
    ('AV_STREAM_STARTED', 'media.chat'),
    ('RECORDING_STARTED', None)
}

TEST_USERS = [
    'pktest sre',
    'pktest sreone'
]
