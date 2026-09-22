import pandas as pd
import streamlit as st
from datetime import datetime, time
from constants import *
import crowd_test_setup as cts
from models import UserCreationData


# """Streamlit design"""
st.set_page_config(page_title='Crowd Test Data Setup', page_icon='proki.svg')

st.title('Crowd Test Data Setup')
if 'num_fields' not in st.session_state:
    st.session_state['num_fields'] = 1
if 'schedule_dates' not in st.session_state:
    st.session_state['schedule_dates'] = []
if 'num_iterations' not in st.session_state:
    st.session_state['num_iterations'] = 1

initial_datetime = datetime.today()
# cookies = {}
user_creation_data = None
iteration_ids = []
institution_id = None
schedule_dates = []
create_fields = []
schedule_fields = []
total_users_to_create = None
starting_sequence = None
search_string = ''
roles = [role.name for role in UserRoles]
timezones = [timezone.name for timezone in TimeZones]

# """Methods"""
def get_next_10_minute_interval():
    now = datetime.now().time()
    current_minute = now.minute
    remainder = current_minute % 5  #10
    minutes_to_add = 5 - remainder  #10
    next_minute = current_minute + minutes_to_add
    next_hour = now.hour + (next_minute // 60)
    next_minute %= 60
    return time(hour=next_hour % 24, minute=next_minute, second=0)


def add_field(key):
    st.session_state[key] += 1


def remove_fields(index_to_remove):
    st.session_state['num_fields'] -= 1
    st.session_state.pop(f'date_{index_to_remove}', None)
    st.session_state.pop(f'time_{index_to_remove}', None)
    st.session_state.pop(f'delete_{st.session_state['num_fields']}', None)

    for idx in range(index_to_remove, st.session_state['num_fields']):
        st.session_state[f'date_{idx}'] = st.session_state[f'date_{idx + 1}']
        st.session_state[f'time_{idx}'] = st.session_state[f'time_{idx + 1}']

    st.session_state.pop(f'date_{st.session_state['num_fields']}', None)
    st.session_state.pop(f'time_{st.session_state['num_fields']}', None)

    save_dates()


def remove_iterations(index_to_remove):
    st.session_state['num_iterations'] -= 1
    st.session_state.pop(f'iteration_{index_to_remove}', None)

    for idx in range(index_to_remove, st.session_state['num_iterations']):
        st.session_state[f'iteration_{idx}'] = st.session_state[f'iteration_{idx + 1}']

    st.session_state.pop(f'iteration_{st.session_state['num_iterations']}', None)


def format_dates(dates):
    formatted_dates = []
    for date in dates:
        formatted_dates.append(date.strftime('%Y-%m-%d %H:%M'))
    return formatted_dates

def save_dates():
    st.session_state['schedule_dates'] = []
    for idx in range(st.session_state['num_fields']):
        date_key = f"date_{idx}"
        time_key = f"time_{idx}"
        if date_key in st.session_state and time_key in st.session_state:
            combined_dt = datetime.combine(st.session_state[date_key], st.session_state[time_key])
            st.session_state['schedule_dates'].append(combined_dt)


def required_fields_filled():
    all_fields_filled = False
    # if not st.session_state.get('auth_token', False) and not st.session_state.get('session_token', False):
    #     return all_fields_filled
    if (st.session_state.get('create_users')
            and all(create_fields)
            # and all(value for value in user_creation_data.values())):
            and user_creation_data):
        all_fields_filled = True
    if (st.session_state.get('schedule_session')
            and all(schedule_fields)
            and all(iteration_ids)):
        all_fields_filled = True
    return all_fields_filled


def process():
    if st.session_state.get('create_users'):

        # data_setup = CrowdTestSetup(domain=domain,
        #                             cookies= cookies,
        #                             user_creation_data=user_creation_data,
        #                             users_to_create=total_users_to_create,
        #                             starting_user=starting_user,
        #                         iteration_ids=iteration_ids,
        #                         institution_id=institution_id,
        #                         schedule_dates=schedule_dates,
        #                         search_string=search_string)
        users_data = cts.create_users(creation_data=user_creation_data,
                                    users_to_create=total_users_to_create,
                                    starting_sequence=starting_sequence)
        display_data_created('Users created', users_data)
        if st.session_state.get('schedule_session'):
            # data_setup.search_string = None
            reservations = cts.schedule_sessions(users_data, schedule_dates, iteration_ids)
            display_data_created('Reservations', reservations)
    elif st.session_state.get('schedule_session'):
            reservations = data_setup.schedule_sessions(None)
            display_data_created('Reservations', reservations)

def display_data_created(table_title, data):
    if data:
        df = pd.DataFrame(data)
        st.subheader(table_title)
        st.dataframe(df)


def clear_session():
    st.session_state.clear()
    st.session_state['auth_token'] = ''
    st.session_state['session_token'] = ''
    st.session_state['create_users'] = False
    st.session_state['schedule_session'] = False

domain_names = [domain.name for domain in Domains]
col_domain, col_username, col_passweord, col_login_btn = st.columns(4)
with col_domain:
    selected_domain = st.selectbox('Select the domain',
                    options=domain_names,
                    index=0,
                    key='domain')
    cts.domain = Domains[selected_domain].value
with col_username:
    username = st.text_input('Username', key='username')
with col_passweord:
    password = st.text_input('Password', type='password', key='password')
with col_login_btn:
    st.button('Login',
              on_click=cts.user_login,
              args=(username, password),
              key="login")

if st.checkbox('Create Users', key='create_users'):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        total_users_to_create = st.number_input('Number of users to create',
                                                min_value=1,
                                                value=1,
                                                key='num_users')
        user_name_prefix = f'{st.text_input(label='User name prefix',
                                            placeholder='eg. crowd_tester_', )}{{}}'
        user_email_template = f'{user_name_prefix}@ml.com'
        user_first_name_prefix = f'{st.text_input(label='First name')} {{}}'
        user_phone = st.text_input(label='User phone',
                                   placeholder='format 123-456-7890')

    with col_b:
        starting_sequence = st.number_input('Starting user sequence',
                                        min_value=1,
                                        value=1,
                                        key='starting_sequence')
        default_password = st.text_input(label='Default password')
        user_last_name = f'{st.text_input(label='Last name')} {{}}'
        user_country = 'United States'

    with col_c:
        user_role_id = st.number_input(label='User Role Id',
                                       step=1,
                                       help='Student = 4 in Staging, 925085493 in Demo')
        
        # st.selectbox(label='User Role',
        #                             options=roles,
        #                             index=31)  # student
        institution_id = st.number_input(label='Institution id',
                                         step=1,
                                         help='eg. 6054 for Staging, 958428203 for Demo')
        user_time_zone = st.selectbox(label='User Timezone',
                                      options=timezones,
                                      index=0)
        user_state = 'TX'
        user_creation_data = UserCreationData(user_name_prefix=user_name_prefix,
                                             user_email_template=user_email_template,
                                             user_first_name_prefix=user_first_name_prefix,
                                             user_phone=user_phone,
                                             user_last_name=user_last_name,
                                             user_country=user_country,
                                             user_role_id=user_role_id,
                                             institution_id=institution_id,
                                             user_time_zone='US/Central',
                                             py_time_zone=TimeZones[user_time_zone].value,
                                             user_state=user_state,
                                             default_password=default_password)
create_fields = [total_users_to_create, starting_sequence, user_creation_data]
# term_id = 278753  # Guardian Browser      278754 Guardian Extension
# """Date & time fields"""
if st.checkbox('Schedule Session', key='schedule_session'):
    st.write('Select the schedule dates where the sessions will be scheduled')
    for i in range(st.session_state['num_fields']):
        col_date, col_time, col_delete_input = st.columns(3)
        with col_date:
            st.date_input(f"Schedule date {i + 1}",
                          min_value=initial_datetime,
                          value=initial_datetime,
                          key=f"date_{i}")
        with col_time:
            st.time_input(f"Schedule time {i + 1}",
                          value=get_next_10_minute_interval(),
                          step=300,
                          key=f"time_{i}")
        with col_delete_input:
            if st.session_state['num_fields'] > 1:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                st.button("Delete",
                          on_click=remove_fields,
                          args=[i],
                          key=f"delete_{i}")
    col_add_date, col_save_date = st.columns(2)
    with col_add_date:
        st.button("Add More Date/Time",
                  on_click=add_field,
                  args=['num_fields'],
                  key="button_add_date")

    with col_save_date:
        st.button("Save Dates",
                  on_click=save_dates,
                  key="button_save_dates")
        schedule_dates = format_dates(st.session_state['schedule_dates'])
        st.write(schedule_dates)
    st.text('If you are creating users and scheduling sessions at the same time, this field will not have effect.')
    search_string = st.text_input('Search string',
                                  placeholder='String to search users. eg. crowd_tester', )
    st.text('Make sure the search result using the provided string only return the users you want to impact.')
    col_A, col_B = st.columns(2)
    with col_A:
        col_1, col_2 = st.columns([2, 1])
        for i in range(st.session_state['num_iterations']):
            with col_1:
                iteration_ids.append(st.text_input('Iteration id',
                                                   value=11933088,
                                                   key=f'iteration_{i}'))
                # GB - Cop Refactor Test 11933087 |  11933088 GX - Copernicus Refactor Test
            with col_2:
                if st.session_state['num_iterations'] > 1:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    st.button("Delete",
                              on_click=remove_iterations,
                              args=[i],
                              key=f"delete_iteration_{i}")
        st.button('Add Iteration',
                  on_click=add_field,
                  args=['num_iterations']
                  )
    with col_B:
        if not institution_id:
            institution_id = st.number_input('Institution id',
                                             value=6054,
                                             key='search_institution_id')
schedule_fields = [schedule_dates, iteration_ids, institution_id]

col_process, col_clear = st.columns(2)
with col_process:
    st.button('Process',
              on_click=process,
              disabled=not required_fields_filled(),
              key=f"process")
with col_clear:
    st.button("Clear form values", on_click=clear_session)
