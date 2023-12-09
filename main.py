import selenium.common
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
from logger import Logger
from enums import SCOPES
import traceback
import os.path


class GmailService:
    @staticmethod
    def get_service():
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES.SCOPES.value)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES.SCOPES.value
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
            Logger.write_to_log(traceback.format_exc())


class MailFetcher:
    @staticmethod
    def get_mail_ids(service, user_id, search_string):
        try:
            print('[Gathering mail IDs please wait]')
            search_id = service.users().messages().list(userId=user_id,
                                                        q=search_string, labelIds=['INBOX'],
                                                        maxResults=500).execute()

            if search_id['resultSizeEstimate'] > 0:
                MailFetcher.id_gatherer(search_id)

                if 'nextPageToken' in search_id:
                    next_page_token = search_id['nextPageToken']

                    with alive_bar() as bar:
                        while True:
                            try:
                                search_id = service.users().messages().list(userId=user_id, q=search_string,
                                                                            labelIds=['INBOX'], maxResults=500,
                                                                            pageToken=next_page_token).execute()

                                MailFetcher.id_gatherer(search_id)

                                if 'nextPageToken' in search_id:
                                    next_page_token = search_id['nextPageToken']
                                else:
                                    print('[Finished Searching for mails]')
                                    break

                            except HttpError as error:
                                Logger.write_to_log(traceback.format_exc())
                        bar()

            else:
                print('Found 0 mails')
                Logger.write_to_log('Found 0 mails')

        except HttpError as error:
            Logger.write_to_log(traceback.format_exc())

    @staticmethod
    def id_gatherer(search_id):
        global final_list

        try:
            for ids in search_id['messages']:
                final_list.append(ids['id'])

        except KeyError as error:
            Logger.write_to_log(traceback.format_exc())

    @staticmethod
    def get_excluded_mails():  # Parses all the mails inside exclude.txt and returns a dictionary
        excluded_mails = {}
        try:
            with open('exclude.txt', 'r') as f:
                lines = f.readlines()
                s1 = slice(0, -1)
                for line in range(len(lines) - 1):
                    excluded_mails[lines[line][s1]] = True

                excluded_mails[lines[-1]] = True

            return excluded_mails

        except IndexError as error:
            excluded_mails['noValue'] = True
            Logger.write_to_log('exclude.txt is empty \n')
            return excluded_mails


class MailArchiver:
    @staticmethod
    def mark_as_archived(service, mail_ids):
        print(f'[Archiving {len(mail_ids)} mails]')

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--log-level=3")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        sender_address = ''
        excluded_mails = MailFetcher.get_excluded_mails()
        with alive_bar(len(mail_ids)) as bar:
            for i in range(len(mail_ids)):
                message = service.users().messages().get(userId='me', id=mail_ids[i], format='metadata').execute()
                current_labels = message['labelIds']

                for j in range(len(message['payload']['headers'])):

                    header_dict = message['payload']['headers'][j]
                    if header_dict['name'] == 'From':
                        sender_address = header_dict['value'].split('<')
                        if len(sender_address) > 1:
                            sender_address = sender_address[1][0:-1]
                        else:
                            sender_address = sender_address[0][0:-1]

                        Logger.write_to_log(f'in {i} From: {header_dict["value"]} \n')
                        break

                if sender_address not in excluded_mails:
                    for j in range(len(message['payload']['headers'])):
                        header_dict = message['payload']['headers'][j]

                        # Extracts out the unsubscribe link and opens the link in browser
                        if header_dict['name'] == 'List-Unsubscribe':
                            unsubscribe_link = header_dict['value'].split(',')
                            if len(unsubscribe_link) > 1:
                                unsubscribe_link[0] = unsubscribe_link[0][1:-1]
                                unsubscribe_link[1] = unsubscribe_link[1][2:-1]

                                for k in unsubscribe_link:
                                    if k.startswith('http'):
                                        Logger.write_to_log(f'in {i}: {k} \n')
                                        driver.get(k)
                            else:
                                unsubscribe_link[0] = unsubscribe_link[0][1:-1]
                                if unsubscribe_link[0].startswith('http'):
                                    Logger.write_to_log(f'in {i}: {unsubscribe_link[0]} \n')
                                    try:
                                        driver.get(unsubscribe_link[0])
                                    except selenium.common.WebDriverException as error:
                                        Logger.write_to_log(f'Unable to load {unsubscribe_link[0]} \n')

                            break

                else:
                    Logger.write_to_log(f'[Excluded]: {sender_address} \n')

                Logger.write_to_log('-' * 20 + '\n')

                # uncomment this line if you want your messages to be marked as spam
                # modified_labels = {'removeLabelIds': current_labels, 'addLabelIds': ['SPAM']}
                modified_labels = {
                    'removeLabelIds': current_labels}  # comment this line if you uncommented the above line

                service.users().messages().modify(userId='me', id=mail_ids[i], body=modified_labels).execute()
                bar()


if __name__ == '__main__':
    Logger.create_log()  # Remove this line if you don't want logging

    final_list = []
    MailFetcher.get_mail_ids(GmailService.get_service(), 'me', 'Unsubscribe')

    MailArchiver.mark_as_archived(GmailService.get_service(), final_list)
    Logger.close_log()
