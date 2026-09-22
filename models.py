from dataclasses import dataclass
import pytz

@dataclass
class UserCreationData:
    user_name_prefix: str
    user_email_template: str
    user_first_name_prefix: str
    user_phone: str
    default_password: str
    user_last_name: str
    user_country: str
    user_role_id: int
    institution_id: int
    user_time_zone: str
    py_time_zone: any
    location_id: int
    user_state: str

@dataclass
class UserData:
    user_id:str
    uuid:str
    username:str
    email:str
    py_time_zone:pytz

@dataclass(frozen=True)
class ReservationInfo:
    id:str
    authenticity_token:str
    reservation_url:str
    username:str

