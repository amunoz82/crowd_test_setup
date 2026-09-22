
import json
import re
import requests
import logging_config
import os
from constants import Domains, ErrorMessages
from bs4 import BeautifulSoup, Tag
from typing import Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from math import ceil

HEADER_AGENT = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'}

logger = logging_config.setup_logging(__name__)
session = requests.Session()
domain = Domains.STAGING.value
# domain = Domains.DEMO.value
# domain = Domains.PRODUCTION.value

def send_post_request(url: str, payload: dict[str, Any], headers: dict | None=None) -> requests.Response | None:
    """Sends a POST request to the specified URL with the given headers, and form data.
        
        Args:
            url (str): The URL to send the POST request to
            headers (dict): The headers to send with the request
            payload (dict): The payload to send with the request
        Returns:
            response (requests.Response)| None: The response from the server
    """
    logger.info(f'Sending post request to url: {url}')
    logger.debug(f'with headers: {headers} and payload: {payload}')
    if headers:
        headers.update(HEADER_AGENT)
    else:
        headers = HEADER_AGENT
    try:
        response = session.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(ErrorMessages.REQUEST_EXCEPTION.value.format(url=url, 
                                                        headers=headers, 
                                                        cookies=session.cookies.get_dict()))
        logger.error(f"Error details: {e}")
        return None

def send_get_request(url: str, payload: dict[str, Any] | None=None, headers: dict | None=None):
    """Sends a GET request to the specified URL with the given headers.
        
        Args:
            url (str): The URL to send the GET request to
            headers (dict): The headers to send with the request
        Returns:
            response (requests.Response): The response from the server
    """
    logger.info(f'Sending get request to url: {url}')
    logger.debug(f'with headers: {headers}')
    if headers:
        headers.update(HEADER_AGENT)
    else:
        headers = HEADER_AGENT
    try:
        response = session.get(url, params=payload, headers=headers)
        response.raise_for_status()
        if 'data: unauthenticated' in response.text: 
            logger.error(ErrorMessages.UNAUTHENTICATED.value)
            return None
        return response
    except requests.exceptions.RequestException as e:
        logger.error(ErrorMessages.REQUEST_EXCEPTION.value.format(url=url, 
                                                        headers=headers, 
                                                        cookies=session.cookies.get_dict()))
        logger.error(f"Error details: {e}")
        return None

def user_login(user_name: str, password: str):
    """Logs in the user to set the cookies into the requests session.
    Args:
        user_name (str): The username of the user to log in
        password (str): The password of the user to log in
    """
    logger.info(f'Logging in user {user_name}')
    header = {
        "accept-language": "en-US,en;q=0.9,es;q=0.8",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    }
    # Initial call when loading the login screen
    url = f"{domain}session/new"
    response = send_get_request(url=url, headers=header)
    if not response:
        logger.error(ErrorMessages.LOGGING_IN.value)
        return None

    authenticity_token = get_authenticity_token(response.text)

    # Actual login, this call will set the auth_token
    url = f'{domain}session'
    payload = {
        'authenticity_token': authenticity_token,
        'username': user_name,
        'password': password,
        'commit': 'Log in'
    }
    response = send_post_request(url=url, headers=header, payload=payload)
    if not response:
        logger.error(ErrorMessages.LOGGING_IN.value)
        return None
    return None

def get_errors_creating_user(html):
    """Helper function to get the error messages from the html response when creating a user
    Args:
        html (str): The html response from the server
    """ 
    logger.info('Getting errors creating user')
    soup = BeautifulSoup(html, 'html.parser')
    div_element = soup.find('div', {'id': 'form-error-messages'})
    if not isinstance(div_element, Tag):
        logger.error("No error messages found")
        return
    ul_element = div_element.find('ul')
    if not isinstance(ul_element, Tag):
        logger.error("No error messages found")
        return
    li_elements = ul_element.find_all('li')
    if not li_elements:
        logger.error("No error messages found")
        return
    error_messages = [li.text for li in li_elements]
    logger.error(error_messages)

def get_authenticity_token(html) -> str:
    """Helper function to get the authenticity token from the html response
    Args:
        html (str): The html response from the server
    Returns:
        str: The authenticity token
    """
    logger.info('Getting authenticity token')
    soup = BeautifulSoup(html, 'html.parser')
    input_element = soup.find('input', {'name': 'authenticity_token'})
    if isinstance(input_element, Tag) and input_element.has_attr('value'):
        value = input_element['value']
        if isinstance(value, list):
            return value[0] if value else ''
        return value
    else:
        return soup.find('meta', {'name': 'csrf-token'})['content']

def has_users_href_and_not_btn(tag) -> bool:
    """Helper function to check if the tag has a users href and not a button
    Args:
        tag (Tag): The tag to check
    Returns:
        bool: True if the tag has a users href and not a button, False otherwise
    """
    logger.info('Checking if tag has users href and not btn')
    return tag.name == 'a' and \
        tag.has_attr('href') and \
        tag['href'].startswith('/users/') and \
        not tag.has_attr('class')

def match_user_id(string) -> str | None:
    """Helper function to match the user id from the string
    Args:
        string (str): The string to match the user id from
    Returns:
        str | None: The user id
    """
    logger.info('Matching user id')
    match = re.search(r'^/alias\?id=(\d+)', string)
    if not match:
        logger.error(f'Couldn\'t get user id {string}')
        return None
    return match.group(1)

def match_uuid(string) -> str | None:
    """Helper function to match the user uuid from the string
    Args:
        string (str): The string to match the user uuid from
    Returns:
        str | None: The user uuid
    """
    logger.info('Matching user uuid')
    match = re.search(r'user=([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', string)
    if not match:
        logger.error(f'Couldn\'t get user uuid {string}')
        return None
    return match.group(1)

def extract_fulfillment_id(html) -> str | None:
    """Helper function to get the fullfilment id from the html response
    Args:
        html (str): The html response from the server
    Returns:
        str | None: The fullfilment id
    """
    logger.info('Getting fullfilment id')
    soup = BeautifulSoup(html, "html.parser")
    strict_numeric_pattern = re.compile(r"/fulfillments/(\d+)/")
    for tag in soup.find_all(True):
        for attr_name, attr_value in tag.attrs.items():
            if isinstance(attr_value, str):
                match = strict_numeric_pattern.search(attr_value)
                if match:
                    return match.group(1)
    return None

def extract_fulfillment_uuid(string) -> str | None:
    """Helper function to extract the fulfillment uuid from the string
    Args:
        string (str): The string to extract the fulfillment uuid from
    Returns:
        str | None: The fulfillment uuid
    """
    logger.info('Extracting fulfillment uuid')
    match = re.search(r'/fulfillments/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', string)
    if not match:
        logger.error(f'Couldn\'t get fulfillment uuid from {string}')
        return None
    return match.group(1).strip()
    
def extract_reservation_uuid(html) -> str:
    """Helper function to extract the reservation id from the html response
    Args:
        html (str): The html response from the server
    Returns:
        str: The reservation id
    """
    logger.info('Extracting reservation id')
    soup = BeautifulSoup(html, "html.parser")
    view_session_tag = soup.find(
        "a", string=re.compile(r"\s*View Session\s*")
    )

    if view_session_tag and view_session_tag.has_attr("href"):
        href_value = view_session_tag["href"]
        uuid_pattern = r"/reservations/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"

        match = re.search(uuid_pattern, href_value)
        if match:
            return match.group(1)

    return ""

def convert_date_iso_utc(date_str: str, tz_name: str = "America/Chicago") -> str:
    """
    Converts a MM/DD/YYYY date string into an ISO 8601 string,
    accounting for the user's specific timezone.
    Args:
        date_str (str): date string with format MM/DD/YYYY
        tz_name (str): The timezone name
    Returns:
        str: The converted date string
    """
    combined_str = f"{date_str} 00:00:00"
    local_dt = datetime.strptime(combined_str, "%m/%d/%Y %H:%M:%S")
    local_dt = local_dt.replace(tzinfo=ZoneInfo(tz_name))
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
    
    return utc_dt.replace(tzinfo=None).isoformat(timespec='milliseconds')

def add_hours_to_utc_string(utc_str: str, hours_to_add: float) -> str:
    """
    Takes a UTC ISO string, adds hours, and returns the updated UTC ISO string.
    Args:
        utc_str (str): The UTC ISO string
        hours_to_add (float): The hours to add
    Returns:
        str: The updated UTC ISO string
    """
    dt = datetime.fromisoformat(utc_str)
    updated_dt = dt + timedelta(hours=hours_to_add)
    
    return updated_dt.isoformat(timespec='milliseconds')

def extract_start_time(html) -> dict:
    """
    Extract the start time and timezone from the html response
    Args:
        html (str): The html response from the server
    Returns:
        dict: The start time and timezone
    """
    logger.info('Extracting start time')
    soup = BeautifulSoup(html, "html.parser")
    target_div = soup.find("div", {"data-react-class": "Fulfillments/TestTakerProfilePanel/TestTakerProfilePanel"})

    if isinstance(target_div, Tag) and target_div.has_attr('data-react-props'):
        try:
            props = json.loads(target_div['data-react-props'])
            panel_info = props.get('profile_panel_info', {})
            fulfillment = panel_info.get('fulfillment', {})
            test_taker = panel_info.get('test_taker', {})
            raw_start_time = fulfillment.get('starts_at', '')
            timezone = test_taker.get('timezone', 'UTC')
            duration = fulfillment.get('duration', '')
            # format date to ISO 8601
            cleaned_time = raw_start_time[4:].strip()
            cleaned_time = cleaned_time[:-4].strip()
            cleaned_time = " ".join(cleaned_time.split())
            start_time = datetime.strptime(cleaned_time, "%m/%d/%y %I:%M %p")
            start_time = start_time.isoformat(timespec='milliseconds')
            # Calculate end_time using duration and start_time rounding it up to the nearest hour
            duration = ceil(float(int(duration.split()[0])/60))
            end_time = add_hours_to_utc_string(start_time, duration)

            return {
                'start_time': start_time,
                'timezone': timezone,
                'end_time': end_time
            }
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse target React props data: {e}")
            return {}

    logger.warning("Target React profile panel div or props attribute not found.")
    return {}

def save_data_to_json(data: dict, filename: str) -> None:
    """Saves a dictionary into a structured, human-readable JSON file.

    Args:
        data (dict): The dictionary payload to save.
        filename (str): The destination file path (e.g., 'incident_report.json').
    """
    try:
        with open(filename, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)

        logger.info(
            f"Successfully saved data to {os.path.abspath(filename)}"
        )

    except IOError as e:
        logger.error(f"Failed to write JSON data to file {filename}: {e}")
    except TypeError as e:
        logger.error(f"Data contains objects that cannot be serialized: {e}")

def load_data_from_json(filename: str) -> dict:
    """Reads a JSON file and parses it back into a Python dictionary.

    Args:
        filename (str): The path to the JSON file to read.

    Returns:
        dict: The parsed dictionary data, or an empty dict if it fails.
    """
    if not os.path.exists(filename):
        logger.error(f"File not found: {os.path.abspath(filename)}")
        return {}

    try:
        with open(filename, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        logger.info(
            f"Successfully loaded data from {os.path.abspath(filename)}"
        )
        return data

    except json.JSONDecodeError as e:
        logger.error(
            f"Failed to parse JSON. File may be corrupted or malformed: {e}"
        )
        return {}
    except IOError as e:
        logger.error(f"Failed to read file {filename}: {e}")
        return {}
