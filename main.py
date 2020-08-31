from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import tkinter as tk
from tkinter import filedialog
import re

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/contacts']

def main():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            root = tk.Tk()
            root.withdraw()
            credentials_path = filedialog.askopenfilename()
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('people', 'v1', credentials=creds)

    # Call the People API
    results = service.people().connections().list(
        resourceName='people/me',
        personFields='names,phoneNumbers').execute()
    connections = results.get('connections', [])

    print('Scanning', len(connections), 'contacts...')

    number_count = 0
    contact_count = 0
    for person in connections:
        names = person.get('names', [])
        phones = person.get('phoneNumbers', [])
        resName = person.get('resourceName', [])
        etag = person.get('etag', [])
        name = ''
        if names:
            name = names[0].get('displayName')
        if phones:
            update = False
            new_numbers = list()
            old_numbers = list()
            for phone in phones:
                number = phone.get('value')
                m = re.search(r'^\s*\+52\s*1?\s*', number)
                if m:
                    update = True
                    span = m.span()
                    new_number = number[span[1]:]
                    new_numbers.append(new_number)
                    old_numbers.append(number)
                    number_count += 1
            if update:
                contact_count += 1
                print(name, ':')
                phoneNumbers = []
                for new_number, old_number in zip(new_numbers, old_numbers):
                    phoneNumbers.append({
                        "value": new_number
                    })
                    print(old_number, '>>>', new_number)
                r = service.people().updateContact( resourceName=resName, updatePersonFields='phoneNumbers', body={
                    "phoneNumbers": phoneNumbers,
                    "etag": etag
                }).execute()
    
    print('Updated', number_count, 'numbers in', contact_count, 'contacts!')

if __name__ == '__main__':
    main()