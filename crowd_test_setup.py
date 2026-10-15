import random
import re
from datetime import datetime
import logging_config
import pytz
from bs4 import BeautifulSoup
from constants import TimeZones, ErrorMessages, Domains, ReservationStatus, Regions
from models import UserCreationData, UserData, ReservationInfo
from web_utils import *

logger = logging_config.setup_logging(__name__)
def create_users(creation_data: UserCreationData, users_to_create: int, starting_sequence: int) -> list[UserData] | None:
    """Creates a user or multiple users. 
        - The user name is created using the user_name_prefix and the sequence number.
        - The user email is created using the user_email_template and the sequence number.
        - The user first name is created using the user_first_name_prefix and the sequence number.
        - The user last name is created using the user_last_name and the sequence number.
        - The user password is created using the default_password.
        - The user role is created using the user_role_id.
        - The user institution is created using the institution_id.
        - The user timezone is created using the user_time_zone.
        - The user phone is created using the user_phone.
        - The user country is created using the user_country.
        - The user state is created using the user_state.
    Args:
        creation_data (UserCreationData): The user creation data.
        users_to_create (int): The number of users to create.
        starting_sequence (int): The starting sequence for the users.
    Returns:
        list[UserData]: List of UserData objects.
    """
    logger.info(f'Creating users | {creation_data}')   
    url = f'{domain}users/new'  # call this method to get the authenticity token
    response = send_get_request(url)
    if not response:
        logger.error('Error creating the users')
        return None
    authenticity_token = get_authenticity_token(response.text)

    # Create the users
    url = f'{domain}users'
    headers = {
        "content-type": "application/x-www-form-urlencoded"
    }
    users = []
    # build the request body for all the users to create
    # Commented fields are not implemented as those are not required, left them here in case needed in the future.
    for x in range(users_to_create):
        user_sequence = x + starting_sequence
        # Prepare the form data
        form_data = {
            "authenticity_token": authenticity_token,
            "user[username]": creation_data.user_name_prefix.format(user_sequence),
            "user[email]": creation_data.user_email_template.format(user_sequence).replace(' ', '_'),
            "user[first_name]": creation_data.user_first_name_prefix.format(user_sequence),
            "user[last_name]": creation_data.user_last_name.format(user_sequence),
            "user[assign_password]": 1,  # Assign Password selected
            "user[password]": creation_data.default_password,
            "user[password_confirmation]": creation_data.default_password,
            "user[require_password_reset]": 0,  # Require Password Reset not selected
            "user[active]": 1,  # Active selected
            # "user[mfa_enabled]": item_data.get("mfa_enabled", ""),
            "user[role_id]": creation_data.user_role_id,
            # "user[enrollments_attributes][0][_destroy]": item_data.get("enrollments_attributes_0__destroy", "false"),
            "user[enrollments_attributes][0][institution_id]": creation_data.institution_id,
            # "user[enrollments_attributes][0][campus_id]": item_data.get("enrollments_attributes_0_campus_id", ""),
            # "user[enrollments_attributes][0][flag_notes_html]": item_data.get("enrollments_attributes_0_flag_notes_html", ""),
            # "files": ("", None, "application/octet-stream"),
            # "user[enrollments_attributes][0][always_recorded]": item_data.get("enrollments_attributes_0_always_recorded", "0"),
            # "user[enrollments_attributes][0][identifier]": item_data.get("enrollments_attributes_0_identifier", ""),
            # "user[enrollments_attributes][0][student_id]": item_data.get("enrollments_attributes_0_student_id", ""),
            # "user[enrollments_attributes][0][notify_on_schedule_emails]": item_data.get("enrollments_attributes_0_notify_on_schedule_emails", ""),
            "user[timezone]": creation_data.user_time_zone,
            "user[phone_mobile]": creation_data.user_phone,
            "user[country]": creation_data.user_country,
            "user[state]": creation_data.user_state,
            "user[location_id]": creation_data.location_id,
            # "user[pictures_attributes][0][image]": ("", None, "application/octet-stream"),
            # "user[pictures_attributes][0][image_url]": item_data.get("pictures_attributes_0_image_url", ""),
            # "user[pictures_attributes][0][retained_image]": item_data.get("pictures_attributes_0_retained_image", ""),
            "commit": "Create User"
        }
        logger.info(f'form data for user: {form_data}')
        response = send_post_request(url=url, headers=headers, payload=form_data)
        if not response: continue

        if 'Please correct the errors below.' in response.text:
            logger.error(ErrorMessages.USER_CREATION.value.format(sequence=user_sequence))
            get_errors_creating_user(response.text)
            continue
        username = creation_data.user_name_prefix.format(user_sequence)
        email = creation_data.user_email_template.format(user_sequence)
        py_time_zone = creation_data.py_time_zone
        user_id, uuid = get_user_ids_after_creation(response.text)
        user = UserData(user_id=user_id, uuid=uuid, username=username, email=email, py_time_zone=py_time_zone)
        logger.info(f'Created user {user.username}')
        confirm_user(user.user_id, authenticity_token)
        users.append(user)
    return users

def get_user_ids_after_creation(html) -> tuple[str, str]:
    """Helper function to get the user ids after creation
    Args:
        html (str): The html response from the server
    Returns:
        tuple[str, str]: The user id and uuid
    """
    logger.info('Getting user ids after creation')
    soup = BeautifulSoup(html, 'html.parser')
    id_a_element = soup.find('a', {'href': re.compile(r'^/alias')})
    user_id = match_user_id(id_a_element.get('href'))
    uuid_a_element = soup.find('a', {'href': re.compile(r'^/exams/select\?user')})
    if uuid_a_element:
        uuid = match_uuid(uuid_a_element.get('href'))
    else:
        uuid = None
    return (user_id, uuid)

def confirm_user(user_id:str, authenticity_token:str):
    """Confirms the user to set the cookies into the requests session.
    Args:
        user_id (str): The user id of the user to confirm
        authenticity_token (str): The authenticity token to confirm the user
    """
    logger.info(f'Confirming user {user_id}')
    url = f'{domain}internal/account_confirmations?user_account_id={user_id}'
    body = {
        'authenticity_token': authenticity_token,
    }
    response = send_post_request(url=url, headers=None, payload=body)
    if response:
        logger.info(f'user: {user_id} confirmed')

def update_username(search_string:str, user_name_pattern:str, institution_id:str):
    """Updates the username of users that match the search string.
    This method assumes that the username is in the format of 'username_sequence', 
    therefore it will update the username to 'user_name_pattern_sequence' if the username does not contain 
    the provided user_name_pattern.
    
    Args:
        search_string (str): The string to search for in the username.
        user_name_pattern (str): The pattern to use for the new username.
    """
    logger.info(f'Updating username for {search_string}')
    users = get_user_ids_from_search(search_string, institution_id)
    if not users: return
    base_url = f'{domain}users'
    for user in users:
        logger.info(f'Updating {user.username}')
        url = f'{base_url}/{user.user_id}'
        response = send_get_request(url)
        if not response:
            logger.error(ErrorMessages.USER_UPDATE.value.format(user.username))
            continue
        authenticity_token = get_authenticity_token(response.text)
        soup = BeautifulSoup(response.text, 'html.parser')
        label_tag = soup.find('dt', string="Username:")
        if not label_tag:
            continue
        username_tag = label_tag.find_next_sibling('dd')
        username = username_tag.get_text(strip=True)
        if user_name_pattern in username:
            logger.info(ErrorMessages.USER_ALREADY_HAS_PATTERN.value.format(user.username, user_name_pattern))
            continue
        match = re.search(r'(\d+)$', username)
        if not match:
            logger.info(ErrorMessages.NO_SEQUENCE_FOUND.value.format(user.username))
            continue
        sequence = match.group(1)

        form_data = {
            "_method": "patch",
            "authenticity_token": authenticity_token,
            "user[username]": f'{user_name_pattern}{sequence}'
        }
        response = send_post_request(url=url, headers=None, payload=form_data)
        if response: # The assumption is that if the request was successful, the username was updated. 
            logger.info(f'User {user.username} updated')

def schedule_sessions_searching_users(search_string:str, schedule_dates: list[str], 
                                      iteration_ids: list[str], institution_id:str) -> list[ReservationInfo]:
    """Schedules sessions for users that match the search string.
    
    Args:
        search_string (str): The search string to use for the search.
        schedule_dates (list[str]): The list of dates to schedule sessions for.
        iteration_ids (list[str]): The list of iteration ids to schedule sessions for.
        institution_id (str): The institution id to use for the search.
    
    Returns:
        list[ReservationInfo]: The list of reservation info.
    """ 
    logger.info(f'Scheduling sessions by searching users')
    users = get_user_ids_from_search(search_string, institution_id)
    return schedule_sessions(users, schedule_dates, iteration_ids)

def schedule_sessions(users: list[UserData], schedule_dates: list[str], iteration_ids: list[str]) -> list[ReservationInfo]:
    """Schedules sessions for the given users.
    
    Args:
        users (list[UserData]): The list of users to schedule sessions for.
        schedule_dates (list[str]): The list of dates to schedule sessions for.
        iteration_ids (list[str]): The list of iteration ids to schedule sessions for.
    
    Returns:
        list[ReservationInfo]: The list of reservation info.
    """ 
    logger.info(f'Scheduling sessions for {len(users)} users')
    reservations = []
    schedule_idx = 0
    total_iterations = len(iteration_ids)
    total_dates = len(schedule_dates)
    for user in users:
        index = random.randint(0, total_iterations - 1)
        get_impersonation_cookies(user)
        authenticity_token = get_authenticity_token_to_schedule(
                user_uuid=user.uuid,
                schedule_date=schedule_dates[schedule_idx],
                iteration_id=iteration_ids[index]
            )
        reservations.append(make_reservation(user_data=user,
                                             authenticity_token=authenticity_token,
                                             schedule_date=schedule_dates[schedule_idx],
                                             iteration_id=iteration_ids[index]
                                             ))
        schedule_idx = schedule_idx + 1 if schedule_idx < total_dates - 1 else 0
    return reservations

def get_user_ids_from_search(search_param:str=None, institution_id:int=None, region:str=Regions.US_WEST.value):
    """Gets the user ids from the search results based on the search param, institution id and region.
    
    Args:
        search_param (str): The search param to use for the search.
        institution_id (int): The institution id to use for the search.
        region (str): The region to use for the search.
    Returns:
        list[UserData]: The list of user ids.
    """
    logger.info(f'Searching for users with search param: {search_param}, institution id: {institution_id}, region: {region}')
    page = 1
    users = []
    while True:
        url = f'{domain}users?utf8=%E2%9C%93&search={search_param}&institution={institution_id}&role=&status=active&data_region={region}&commit=Search&limit=100&page={page}'
        response = send_get_request(url=url)
        page += 1
        if not response:
            break
        # authenticity_token = get_authenticity_token(response.text)
        soup = BeautifulSoup(response.text, 'html.parser')
        no_results_msg = soup.find('span',
                                   string="Not seeing the results you're looking for? Try searching in another region.")
        if no_results_msg:
            break
        elements = soup.find_all(has_users_href_and_not_btn)

        for element in elements:
            href = element.get('href')
            match = re.search(r'/users/(\d+)', href)
            if match:
                user_id = match.group(1)
                # Get email
                email_td = element.parent.find_next_sibling('td', class_='text-truncate')
                email = email_td.find('a', {'href': re.compile(r'^mailto:')}).text
                # get user uuid
                uuid_td = email_td.find_next_sibling('td', class_='text-right')
                uuid_href = uuid_td.find('a', {'href': re.compile(r'^/exams/select')}).get('href')
                user_uuid = match_uuid(uuid_href)
                url = f'{domain}users/{user_id}'
                response = send_get_request(url=url) #, cookie=self.cookies)
                if response:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    #get user_name
                    dt_user_name = soup.select_one('dt:-soup-contains("Username:")')
                    username = dt_user_name.find_next_sibling('dd').text if dt_user_name else None
                    #get time_zone TODO revisit this, for now leaving it as the default timezone
                    # dt_time_zone = soup.select_one('dt:-soup-contains("Time Zone:")')
                    # time_zone = dt_time_zone.find_next_sibling('dd').text if dt_time_zone else None
                    py_time_zone = TimeZones.US_CENTRAL.value
                    user = UserData(user_id, user_uuid, username, email, py_time_zone)
                    users.append(user)
    return users

def get_impersonation_cookies(user:UserData):
    """Gets the impersonation cookies for the given user.
    
    Args:
        user (UserData): The user to get the impersonation cookies for.
    
    Returns:
        None
    """
    logger.info(f'Getting impersonation cookies for user {user.username}')  
    clear_impersonation_cookies()
    url = f'{domain}/users/{user.user_id}'
    response = send_get_request(url=url)
    if not response:
        logger.error(ErrorMessages.IMPERSONATION_COOKIES.value.format(user.username))
        return
    authenticity_token = get_authenticity_token(response.text)
    referrer = f'{domain}users?utf8=%E2%9C%93&search={user.username}&role=&status=active&data_region=us-west-2&commit=Search'
    url = f'{domain}alias?id={user.user_id}'
    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "referer": referrer,
        "Referrer-Policy": "strict-origin-when-cross-origin"}
    payload = {'authenticity_token': authenticity_token}
    response = send_post_request(url=url, headers=headers, payload=payload)
    if not response:
        logger.error(ErrorMessages.IMPERSONATION_COOKIES.value.format(user.username))
        return

def clear_impersonation_cookies():
    """Clears the impersonation cookies to switch to another user."""
    logger.info('Clearing impersonation cookies')
    for cookie_name, cookie_value in session.cookies.items():
        if cookie_name.startswith('alias_'):
            session.cookies.pop(cookie_name)

def get_authenticity_token_to_schedule(user_uuid: str, schedule_date: str, iteration_id: str) -> str:
    """Get the authenticity token to schedule an appointment for a user.
        
        Args:
            user_uuid (str): The UUID of the user to schedule an appointment for
            schedule_date (str): The date to schedule the appointment for
            iteration_id (str): The iteration ID of the exam
        Returns:
            authenticity_token (str): The authenticity token to schedule the appointment
    """
    logger.info('Getting authenticity token to schedule')
    search_date = schedule_date.replace(' ', 'T')

    url = f'{domain}students/reservations/slots?iteration_id={iteration_id}&date={search_date}&user={user_uuid}'
    response = send_get_request(url=url)
    if response and ErrorMessages.TIME_IN_PAST.value in response.text:
        logger.error(ErrorMessages.TIME_IN_PAST.value)
        return None
    soup = BeautifulSoup(response.text, 'html.parser')
    # Convert the date to Month day, Year
    date_object = datetime.strptime(schedule_date[0:10], '%Y-%m-%d')
    month = date_object.strftime('%B')
    day = int(date_object.strftime('%d')) #removing the leading 0
    year_short = date_object.strftime('%Y')
    schedule_time = datetime.strptime(schedule_date[-5:], '%H:%M').strftime('%I:%M%p')
    schedule_time = schedule_time.lstrip('0') # removing the leading 0
    pattern = re.compile(rf".*{re.escape(schedule_time)}.*{month}\s*{day},\s*{year_short}.*", re.IGNORECASE)
    button = soup.find('button', {'aria-label': pattern})
    if button:
        form = button.find_next_sibling('form', {'data-behavior': 'reservation-destination-form'})
        return form.find('input', {'name': 'authenticity_token'})['value']
    else:
        logger.error(ErrorMessages.SLOT_NOT_AVAILABLE.value.format(month=month, 
                                                        day=day, 
                                                        year_short=year_short, 
                                                        schedule_time=schedule_time))
        return None

def make_reservation(user_data:UserData, authenticity_token:str, schedule_date:str, iteration_id:int):
    """Makes a reservation for the given user at the given schedule date and exam id (iteration id).
    
    Args:
        user_data (UserData): The user data.
        authenticity_token (str): The authenticity token.
        schedule_date (str): The schedule date in the format %Y-%m-%d %H:%M. Example: 2025-12-15 10:00.
        iteration_id (int): The exam id (iteration id).
    """
    logger.info(f'Making reservation for user {user_data.username} @ {schedule_date}')
    url = f'{domain}students/reservations'
    headers = {
        'content-type': 'application/x-www-form-urlencoded'
    }
    try:
        schedule_date_time = datetime.strptime(schedule_date, '%Y-%m-%d %H:%M')
    except ValueError:
        logger.error(ErrorMessages.DATE_FORMAT.value.format(schedule_date=schedule_date))
        return None
    schedule_date_user_tz = user_data.py_time_zone.localize(schedule_date_time)
    schedule_date_utc = schedule_date_user_tz.astimezone(pytz.utc)

    payload = {
            'authenticity_token': authenticity_token,
            'user_uuid': user_data.uuid,
            'reservation[iteration_id]': iteration_id,
            'reservation[starts_at]': schedule_date_utc,
            'commit': 'SCHEDULE'
        }
    response = send_post_request(url=url, headers=headers, payload=payload)
    if response and 'Order Successful!' in response.text:
        logger.info(f'Appointment scheduled successfully for user {user_data.username} @ {schedule_date}')
        return {'user_name': user_data.username,
                'schedule_date': schedule_date,
                'iteration_id': iteration_id}
    else:
        logger.error(ErrorMessages.APPOINTMENT_NOT_SCHEDULED.value.format(username=user_data.username,
                                                                          schedule_date=schedule_date))
        return None

def cancel_reservations_as_admin(search_param:str, institution_id:str, status:str, region:str):
    """Cancel reservations as admin. Use this when test taker cannot cancel the reservation.
    Args:
        institution_id (str): Institution id to search for reservations.
        status (str): Status of the reservation(s) to cancel.
        region (str): Region of the reservation(s) to cancel.
    Returns:
        None
    """
    logger.info('Canceling reservations as admin')
    reservations = get_reservation_urls(search_param=search_param, 
                                        institution_id=institution_id, 
                                        status=status, 
                                        region=region)
    logger.info(f'Found {len(reservations)} reservations to cancel')
    if reservations:
        for reservation in reservations:
            fulfillment_url = get_fulfillment_url(reservation.reservation_url)
            cancellation_url = get_cancellation_links(fulfillment_url)
            response = cancel_reservation(cancellation_url, fulfillment_url, reservation.authenticity_token)
            if response:
                logger.info(f'Reservation for {reservation.username} cancelled')

def get_reservation_urls(search_param:str, institution_id:str, status:str, region:str) -> list[ReservationInfo]:
    """Get reservation urls from the reservation (Sessions) search page.
    Args:
        institution_id (str): Institution id to search for reservations.
        status (str): Status of the reservation(s) to search.
        region (str): Region of the reservation(s) to search.
    Returns:
        list[ReservationInfo]: List of ReservationInfo objects.
    """
    logger.info(f'Getting reservation urls for institution id: {institution_id}, appointment status: {status}, region: {region}')
    reservations = []
    page = 1
    while True:
        url = (f'{domain}reservations?utf8=%E2%9C%93&search={search_param}&exam=&status={status}&order=&'
           f'institution={institution_id}&data_region={region}&commit=Search&limit=100&page={page}')
        response = send_get_request(url=url)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            tbody_tag = soup.find('tbody')
            tr_tags = tbody_tag.find_all('tr')
            if not tr_tags:
                break   
            for tr in tr_tags:
                a_tags = tr.find_all('a')
                if len(a_tags) > 1:
                    reservation_url = a_tags[0].get('href')
                    id = a_tags[0].text.strip()
                    user_name = a_tags[1].text.strip()
                    reservations.append(ReservationInfo(
                        reservation_url=reservation_url,
                        username=user_name,
                        id = id,
                        authenticity_token = get_authenticity_token(response.text)))
        page += 1
    return reservations

def get_fulfillment_url(reservation_url:str):
    """Get fulfillment url using the reservation url.
    Args:
        reservation_url (str): Reservation url to get fulfillment url from.
    Returns:
        str: Fulfillment url.
    """
    logger.info(f'Getting fulfillment url for reservation url {reservation_url}')
    response = send_get_request(url=reservation_url)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.find('a', {'class':'btn-secondary','href': re.compile('^/fulfillments/')})
        if element:
                return f'{domain}{element.get('href')[1:]}'
        return None

def get_cancellation_links(fulfillment_url:str):
    """Get cancellation links using the fulfillment url.
    Args:
        fulfillment_url (str): Fulfillment url to get cancellation links from.
    Returns:
        str: Cancellation links.
    """
    logger.info(f'Getting cancellation links for fulfillment url {fulfillment_url}')
    response = send_get_request(url=fulfillment_url)
    if response:
        authenticity_token = get_authenticity_token(response.text)
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.find('a', {'class':'btn-danger', 'data-target':'#cancel-modal'})
        if element:
            return f'{domain}{element.get('data-form-url')[1:]}'
    return None

def cancel_reservation(url, referrer, authenticity_token):
    """Cancel a reservation for a given appointment.
    Args:
        url (str): URL to cancel the reservation. ex. https://staging.proctoru.com/reservations/30506035/cancellations?fulfillment_id=42137121
    Returns:    
        Response: Response from the server
    """
    logger.info(f'Canceling reservation for {url}')
    headers = {'content-type': 'application/x-www-form-urlencoded',
               'referrer': referrer,
               'x-csrf-token': authenticity_token,
                'x-requested-with': 'XMLHttpRequest'}
    payload = {'cancellation[cancellation_reason_id]': 37,
            'cancellation[explaination]': 'Session cancelled by Test-Taker',
            'cancellation[xvoucher_excused]': 'false',
            'cancellation[credit]': 'none',
            'cancellation[is_waived]': 'false'
        }
    return send_post_request(url=url,
                             headers=headers,
                             payload=payload)

def cancel_reservations_as_test_taker(search_param:str, institution_id:str, region:str=Regions.US_WEST.value):
    """Cancel reservations as test taker finding the user(s) by search param.
    Args:
        search_param (str): Search parameter to find the user. ex. 'crowd_tester_'
    Returns:
        None
    """
    logger.info(f'Canceling reservations as test taker for {search_param}')
    users = get_user_ids_from_search(search_param, institution_id, region)
    for user in users:
        get_impersonation_cookies(user)
        reservation_info = get_reservation_info()
        if not reservation_info:
            continue
        url = f'{domain}students/reservations/{reservation_info.id}/cancellations'
        # headers.update({'x-csrf-token': reservation_info.authenticity_token})
        response = cancel_reservation(url, reservation_info.reservation_url, reservation_info.authenticity_token)
        if response:
            logger.info(f'Reservation for {user.username} cancelled')

def get_reservation_info() -> ReservationInfo | None:
    """Get reservation info from the reservation page
    Returns:
        ReservationInfo | None: Reservation info if found, None otherwise
    """
    logger.info('Getting reservation info')
    url = f'{domain}students/reservations'
    response = send_get_request(url=url)
    if response:
        authenticity_token = get_authenticity_token(response.text)
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.find('a',  class_='start_button')
        if element:
            id = element.get('data-reservation-id')
            url = element.get('href')
            return ReservationInfo(id=id, 
                                   authenticity_token=authenticity_token,
                                   reservation_url=url,
                                   username=None)
        return None

def main():

    # login
    user_login(user_name='amunoz@meazurelearning.com', password='L@rry$2405')
    # # **** Sample how to create users ****
    user_data = UserCreationData(
            user_name_prefix="crowd_tester_{}", #alpha_tester{}",   #TIO_Crowd_Test
            user_email_template="crowd_tester_{}@ml.com",
            user_first_name_prefix="Tester {} ",
            user_phone="123-456-7890",
            default_password="Testing123",
            user_last_name="Crowd",
            user_country="United States",
            user_role_id=4,   # student demo role 925085493
            institution_id="6054", #2099, # 6054, #958428203 institution demo
            user_time_zone="US/Central",
            py_time_zone=TimeZones.US_CENTRAL.value,
            location_id=6,
            user_state="AL"
    )
    users = create_users(user_data, users_to_create=99, starting_sequence=102)
    logger.info(f'Users created: {users}')
    
    
    ## **** Sample how to update username ****
    # update_username(user_name_pattern='am_test_', search_string='andres_test_2', institution_id=6054)

    ## **** Sample how to schedule sessions ****
    # user = UserData(user_id='10097569', uuid='db8454f4-4db1-44f0-a184-bfa3278b8501', username='am_test_2', 
    #                 email='andres_test_2@ml.com', py_time_zone=TimeZones.US_CENTRAL.value)
    # reservation = schedule_sessions([user], ['2025-12-15 16:00'], ['11933087'])
    # logger.info(f'Reservation scheduled: {reservation}')

    # # **** Sample how to cancel reservations as admin ****
    # cancel_reservations_as_admin(search_param='crowd_tester_', 
    #                              institution_id=6054, 
    #                              status=ReservationStatus.SCHEDULED.value, 
    #                              region=Regions.US_WEST.value)

    ## **** Sample how to schedule sessions from search ****
    # reservations = schedule_sessions_searching_users(search_string='crowd_tester_', 
    #                                                 schedule_dates=['2026-08-25 10:00'], 
    #                                                 iteration_ids=['12017220'],
    #                                                 institution_id=6054)
    # logger.info(f'Reservations scheduled: {reservations}')  

    # **** Sample how to cancel reservations as test taker ****
    # cancel_reservations_as_test_taker(search_param='crowd_tester_', 
    #                                   institution_id=6054, 
    #                                   region=Regions.US_WEST.value)

    # ***Licata School of Ruby*** Prod institution id - 721
    # Live+ test iteration id - 11214101
    # Internal crowd test Staging institution id - 6054
    # Iteration Cop GB - 11933087
    #### Demo Info
    #Ren's Demo Institution = 958428203
    # Demo role_id = 925085493

if __name__ == "__main__":
    main()
