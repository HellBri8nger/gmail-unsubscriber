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
from icecream import ic
import logging
import os.path


logging.basicConfig(
   level=logging.CRITICAL,
   format="%(asctime)s %(levelname)s %(message)s",
   datefmt="%Y-%m-%d_%H-%M-%S",
   filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
)

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
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")


def get_mail_ids(service, user_id, search_string):
    try:
        print('[Gathering mail IDs please wait]')
        search_id = service.users().messages().list(userId=user_id, q=search_string, labelIds=['INBOX'],
                                                    maxResults=500).execute()

        # ic(search_id)

        if search_id['resultSizeEstimate'] > 0:
            id_gatherer(search_id)

            if 'nextPageToken' in search_id:
                next_page_token = search_id['nextPageToken']

                with alive_bar() as bar:
                    while True:
                        try:
                            search_id = service.users().messages().list(userId=user_id, q=search_string, maxResults=500,
                                                                        labelIds=['INBOX'],
                                                                        pageToken=next_page_token).execute()

                            id_gatherer(search_id)

                            if 'nextPageToken' in search_id:
                                next_page_token = search_id['nextPageToken']
                            else:
                                print('[Finished Searching for mails]')
                                break

                        except HttpError as error:
                            print(error)
                            logging.error(error)
                    bar()

        else:
            ic('Found 0 mails')
            input()

    except HttpError as error:
        ic(f'An error occurred {error}')
        logging.error(error)


def id_gatherer(search_id):
    global final_list

    for ids in search_id['messages']:
        final_list.append(ids['id'])


def get_next_page(service, next_page_token):
    search_id = service.users().messages().list(userId='me', pageToken=next_page_token, maxResults=500,
                                                labelIds=['INBOX']).execute()

    if search_id['resultSizeEstimate'] > 0:
        try:
            next_page_token = search_id['nextPageToken']

        except KeyError as error:
            next_page_token = None

        final_list = []
        for ids in search_id['messages']:
            final_list.append(ids['id'])

        # ic(final_list)
        return final_list, next_page_token
    else:
        ic('Found 0 mails')
        return None, None


def mark_as_spam(service, mail_ids):
    print(f'[Archiving {len(mail_ids)} mails]')

    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    with alive_bar(len(mail_ids)) as bar:
        for i in range(len(mail_ids)):
            message = service.users().messages().get(userId='me', id=mail_ids[i], format='metadata').execute()
            current_labels = message['labelIds']
            from_and_link = []

            for j in range(len(message['payload']['headers'])):

                header_dict = message['payload']['headers'][j]
                if header_dict['name'] == 'From':
                    print(f'From: {header_dict["value"]}')
                    from_and_link.append(header_dict['value'])

                # Extracts out the unsubscribe link if there is one and appends it to a link
                if header_dict['name'] == 'List-Unsubscribe':
                    unsubscribe_link = header_dict['value'].split(',')
                    if len(unsubscribe_link) > 1:
                        unsubscribe_link[0] = unsubscribe_link[0][1:-1]
                        unsubscribe_link[1] = unsubscribe_link[1][2:-1]

                        for k in unsubscribe_link:
                            if k.startswith('http'):
                                driver.get(k)
                                # from_and_link.append(k)
                    break

                logging.info(from_and_link)

            print('-'*20)

            # Remove existing labels and add the "SPAM" label
            # modified_labels = {'removeLabelIds': current_labels, 'addLabelIds': ['SPAM']}
            modified_labels = {'removeLabelIds': current_labels}

            # Modify the labels using the users.messages.modify method
            service.users().messages().modify(userId='me', id=mail_ids[i], body=modified_labels).execute()
            bar()


get_mail_ids(get_service(), 'me', 'unsubscribe')
ic(len(final_list))

# ic(count_duplicates(final_list))
mark_as_spam(get_service(), final_list)

# message = get_service().users().messages().get(userId='me', id=final_list[5000], format='metadata').execute()
# print(message)
# for i in range(len(message['payload']['headers'])):
#
#     header_dict = message['payload']['headers'][i]
#
#     if header_dict['name'] == 'From':
#         print(f'From: {header_dict["value"]}')
#
#     if header_dict['name'] == 'List-Unsubscribe':
#         print(f'Unsubscribe:  {header_dict["value"]}')
