from webdriver_manager.chrome import ChromeDriverManager
from google_auth_oauthlib.flow import InstalledAppFlow
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from alive_progress import alive_bar
from selenium import webdriver
from datetime import datetime
import traceback
import os.path

log = open(f'{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', 'w', encoding='utf-8')
SCOPES = ["https://mail.google.com/"]
final_list = []


def get_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)

        return service

    except HttpError as error:
        print(f"An error occurred: {error}")
        log.write(traceback.format_exc())


def get_mail_ids(service, user_id, search_string):
    try:
        print('[Gathering mail IDs please wait]')
        search_id = service.users().messages().list(userId=user_id,
                                                    q=search_string, labelIds=['INBOX'],
                                                    maxResults=500).execute()

        if search_id['resultSizeEstimate'] > 0:
            id_gatherer(search_id)

            if 'nextPageToken' in search_id:
                next_page_token = search_id['nextPageToken']

                with alive_bar() as bar:
                    while True:
                        try:
                            search_id = service.users().messages().list(userId=user_id, q=search_string,
                                                                        labelIds=['INBOX'], maxResults=500,
                                                                        pageToken=next_page_token).execute()

                            id_gatherer(search_id)

                            if 'nextPageToken' in search_id:
                                next_page_token = search_id['nextPageToken']
                            else:
                                print('[Finished Searching for mails]')
                                break

                        except HttpError as error:
                            print(error)
                            log.write(traceback.format_exc())
                    bar()

        else:
            print('Found 0 mails')
            log.write('Found 0 mails')

    except HttpError as error:
        print(f'An error occurred {error}')
        log.write(traceback.format_exc())


def id_gatherer(search_id):
    global final_list

    try:
        for ids in search_id['messages']:
            final_list.append(ids['id'])

    except KeyError as error:
        print(search_id)
        print(traceback.format_exc())
        log.write(traceback.format_exc())


def mark_as_spam(service, mail_ids):
    print(f'[Archiving {len(mail_ids)} mails]')

    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    with alive_bar(len(mail_ids)) as bar:
        for i in range(len(mail_ids)):
            message = service.users().messages().get(userId='me', id=mail_ids[i], format='metadata').execute()
            current_labels = message['labelIds']

            for j in range(len(message['payload']['headers'])):

                header_dict = message['payload']['headers'][j]
                if header_dict['name'] == 'From':
                    log.write(f'in {i} From: {header_dict["value"]} \n')
                    log.flush()

                # Extracts out the unsubscribe link and opens the link in browser
                if header_dict['name'] == 'List-Unsubscribe':
                    unsubscribe_link = header_dict['value'].split(',')
                    if len(unsubscribe_link) > 1:
                        unsubscribe_link[0] = unsubscribe_link[0][1:-1]
                        unsubscribe_link[1] = unsubscribe_link[1][2:-1]

                        for k in unsubscribe_link:
                            if k.startswith('http'):
                                log.write(f'in {i}: {k} \n')
                                log.flush()
                                driver.get(k)
                    else:
                        unsubscribe_link[0] = unsubscribe_link[0][1:-1]
                        if unsubscribe_link[0].startswith('http'):
                            log.write(f'in {i}: {unsubscribe_link[0]} \n')
                            log.flush()
                            driver.get(unsubscribe_link[0])

                    break

            log.write('-'*20 + '\n')
            log.flush()

            # uncomment this line if you want your messages to be marked as spam
            # modified_labels = {'removeLabelIds': current_labels, 'addLabelIds': ['SPAM']}
            modified_labels = {'removeLabelIds': current_labels}  # comment this line if you uncommented the above line

            service.users().messages().modify(userId='me', id=mail_ids[i], body=modified_labels).execute()
            bar()


get_mail_ids(get_service(), 'me', 'unsubscribe')

mark_as_spam(get_service(), final_list)
log.close()
