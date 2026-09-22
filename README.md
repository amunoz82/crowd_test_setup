# Crowd Test Setup

Scripts and a small Streamlit app for setting up ProctorU crowd-test data: create users, rename them, schedule sessions, and cancel reservations.

`crowd_test_setup.py` is the script entry point. The commented blocks inside `main()` are working samples. Uncomment the sample you want, fill in the ids, and run the file. Leave the other samples commented so you only run one action.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the script:

```bash
python crowd_test_setup.py
```

Run the UI:

```bash
streamlit run ui.py
```

Logs go to the console at INFO. Debug output is configured in `logging_config.py`.

## Environment

Set the target host in `web_utils.py` by leaving one `domain` assignment uncommented:

```python
domain = Domains.STAGING.value      # https://staging.proctoru.com/
# domain = Domains.DEMO.value        # https://demo.proctoru.com/
# domain = Domains.PRODUCTION.value  # https://go.proctoru.com/
```

Change this before you run the script. `domain` is a module-level variable, and every request URL is built from it.

You do not need a setter for the script. Editing that line is the switch.

A `set_domain()` function is worth adding only if you want to change the host from code, or from the Streamlit app, without editing the file. The UI currently does this:

```python
cts.domain = Domains[selected_domain].value
```

That updates the `domain` name imported into `crowd_test_setup`. `user_login` lives in `web_utils` and reads `web_utils.domain`. After `from web_utils import *`, those are two separate bindings, so login can still hit the host hardcoded in `web_utils.py` while later calls use the UI selection. A setter should assign `web_utils.domain` and then copy that same value onto `crowd_test_setup.domain` so both stay aligned. For the samples in `main()`, uncommenting the line is enough.

## Login

Every sample starts with a logged-in admin session. Put your credentials in the `user_login` call at the top of `main()`:

```python
user_login(user_name='your_admin_username', password='your_password')
```

The session cookies are stored on the shared `requests` session in `web_utils.py`. Later calls reuse them.

## Samples in `main()`

### Create users

`{}` in the name, email, first name, and last name templates is replaced with the sequence number. `starting_sequence` is the first number. `users_to_create` is how many users to make from that number.

```python
user_data = UserCreationData(
    user_name_prefix="stagingproctor{}@proctoru.com",
    user_email_template="stagingproctor{}@proctoru.com",
    user_first_name_prefix="Staging ",
    user_last_name="Proctor{}",
    user_phone="123-456-7890",
    default_password="your_password",
    user_country="United States",
    user_state="AL",
    user_role_id=4,                  # student role in Staging; Demo student role is 925085493
    institution_id=6054,             # Staging crowd-test institution
    user_time_zone="US/Central",     # value sent to ProctorU
    py_time_zone=TimeZones.US_CENTRAL.value,  # pytz timezone used when scheduling
    location_id=6,
)
users = create_users(user_data, users_to_create=37, starting_sequence=14)
```

`starting_sequence=14` and `users_to_create=37` creates users 14 through 50. Each user is confirmed after creation. The return value is a list of `UserData` (`user_id`, `uuid`, `username`, `email`, `py_time_zone`).

### Update usernames

Finds active users whose username matches `search_string`, and rewrites the trailing number onto `user_name_pattern`. A user named `andres_test_2` becomes `am_test_2`. Users that already contain the new pattern are skipped.

```python
update_username(
    user_name_pattern='am_test_',
    search_string='andres_test_2',
    institution_id=6054,
)
```

The username must end in digits. If it does not, it is left unchanged.

### Schedule one session

Schedule for users you already have. Dates use `YYYY-MM-DD HH:MM` in the user's `py_time_zone`. Each user is assigned a random iteration id from the list. Dates are reused in order when there are more users than dates.

```python
user = UserData(
    user_id='10097569',
    uuid='db8454f4-4db1-44f0-a184-bfa3278b8501',
    username='am_test_2',
    email='andres_test_2@ml.com',
    py_time_zone=TimeZones.US_CENTRAL.value,
)
reservation = schedule_sessions([user], ['2025-12-15 16:00'], ['11933087'])
```

### Schedule sessions by search

Same scheduling, but the users come from a search. The search string must match only the users you intend to schedule.

```python
reservations = schedule_sessions_searching_users(
    search_string='crowd_tester_',
    schedule_dates=['2026-08-25 10:00'],
    iteration_ids=['12017220'],
    institution_id=6054,
)
```

### Cancel reservations as admin

Use this when the test taker cannot cancel. `status` filters which sessions are cancelled.

```python
cancel_reservations_as_admin(
    search_param='Kurento',
    institution_id=6054,
    status=ReservationStatus.SCHEDULED.value,
    region=Regions.US_WEST.value,
)
```

`ReservationStatus` values: `pending`, `scheduled`, `running`, `fulfilled`, `cancelled`, `aborted`.

### Cancel reservations as the test taker

Impersonates each user found by the search and cancels that user's reservation.

```python
cancel_reservations_as_test_taker(
    search_param='crowd_tester_',
    institution_id=6054,
    region=Regions.US_WEST.value,
)
```

`region` defaults to `Regions.US_WEST` (`us-west-2`). Other regions are `ca-central-1`, `eu-central-1`, and `ap-southeast-1`.

## Reference ids

These ids are noted at the bottom of `main()`:

| What | Id |
| --- | --- |
| Staging crowd-test institution | 6054 |
| Demo institution (Ren's Demo) | 958428203 |
| Production institution (Licata School of Ruby) | 721 |
| Staging student role | 4 |
| Demo student role | 925085493 |
| Iteration Cop GB | 11933087 |
| Live+ test iteration | 11214101 |

Confirm the institution, role, and iteration in the environment you selected before running a sample. The same numeric id is not valid on Staging, Demo, and Production.

## Streamlit UI

`ui.py` wraps create-users and schedule-session. Pick the domain, log in, fill the form, and press Process.

The domain dropdown writes `cts.domain` only. See [Environment](#environment) for why login can still use the host set in `web_utils.py`. Until a setter exists, set `domain` in `web_utils.py` to the same environment you pick in the dropdown.
