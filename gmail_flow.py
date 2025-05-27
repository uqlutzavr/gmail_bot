import os.path
import time
import json

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import logger, GmailBotConfig


class Gmail:
    def __init__(self):
        self.config = GmailBotConfig()
        self.creds = self._gmail_authorization()
        self.service = None

    def _gmail_authorization(self):
        try:
            creds = None
            if os.path.exists("token.json"):
                creds = Credentials.from_authorized_user_file("token.json", self.config.scopes)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        "credentials.json", self.config.scopes
                    )
                    creds = flow.run_local_server(port=0)

                with open("token.json", "w") as token:
                    token.write(creds.to_json())

            return creds
        except Exception as e:
            logger.error(f"Error in authorization - {e}")
            return None

    def _build_service(self):
        if not self.creds:
            logger.error("No valid credentials available")
            return None

        try:
            self.service = build("gmail", "v1", credentials=self.creds)
            return self.service
        except Exception as e:
            logger.error(f"Error building Gmail service - {e}")
            return None

    def start_monitoring(self, max_retries=5, retry_delay=30, check_interval=5):
        retry_count = 0
        print(max_retries, retry_delay, check_interval)

        while True:
            try:
                logger.info("Starting Gmail monitoring...")
                logger.info("Gmail connection established successfully")
                retry_count = 0
                self._monitoring_loop(check_interval=check_interval)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                retry_count += 1
                logger.error(f"Error in Gmail monitoring (attempt {retry_count}): {e}")
                if max_retries and retry_count >= max_retries:
                    logger.error(f"Max retries ({max_retries}) reached. Stopping.")
                    break

                logger.info(f"Reconnecting in {retry_delay} seconds...")
                time.sleep(retry_delay)

    def get_unread_messages(self, max_results=10):
        if not self.service:
            self.service = self._build_service()

        if not self.service:
            return []

        try:
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            return messages
        except Exception as e:
            logger.error(f"Error getting unread messages: {e}")
            return []

    def get_message_details(self, message_id):
        if not self.service:
            return None

        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')

            return {
                'subject': subject,
                'email_link': f'https://mail.google.com/mail/u/0/#inbox/{message_id}'
            }
        except Exception as e:
            logger.error(f"Error getting message details for {message_id}: {e}")
            return None

    def send_to_slack(self, message_id: int):
        data = self.get_message_details(message_id)
        try:
            message = (
                "*Support - New Email Received*\n"
                f"*Subject:* {data['subject']}\n"
                f"*Link:* <{data['email_link']}|Open in Gmail>"
            )

            payload = {'text': message}
            response = requests.post(self.config.slack_webhook_url, json=payload)
            if response.status_code != 200:
                logger.error(f"Slack returned error: {response.status_code}, response: {response.text}")
        except Exception as e:
            logger.error(f"Error in sending message to slack - {e}")

    def _monitoring_loop(self, check_interval=30):
        print(check_interval)
        logger.info(f"Starting monitoring loop with {check_interval}s interval")
        already_sent = set()
        try:
            with open("ids.json", "r") as f:
                text = f.read()
                ids = json.loads(text)
                already_sent = set(ids)
        except FileNotFoundError:
            logger.error("Error: The file ids.json was not found")
        except json.JSONDecodeError:
            logger.error("Error: ids.json is empty")
        except Exception as e:
            logger.error(f"Error in opening id.json - {e}")

        while True:
            try:
                logger.info("Checking for new messages...")
                unread_messages = self.get_unread_messages(max_results=5)

                for message in unread_messages:
                    message_id = message['id']

                    if message_id not in already_sent:
                        self.send_to_slack(message_id)
                        already_sent.add(message_id)
                    else:
                        pass
                    logger.info(f"Message was already sent in slack - {message_id}")

            except KeyboardInterrupt:
                logger.info("Monitoring loop interrupted")
                raise
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                raise
            finally:
                with open("ids.json", "w") as f:
                    json.dump(list(already_sent), f)
                    time.sleep(check_interval)


if __name__ == "__main__":
    gmail_bot = Gmail()
    gmail_bot.start_monitoring()
    # gmail_bot.start_monitoring(check_interval=120)
