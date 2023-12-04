<h2 style="border-bottom: 1px solid white;">Gmail Unsubscriber</h2>

## Description
Gmail Unsubscriber is a Python-based project designed to automate the process of unsubscribing from spam emails. It achieves this by archiving all spam mails and unsubscribing them using the header links. This project uses the Gmail API to interact with your Gmail account and perform the unsubscription process.

## Table of Contents
- [Installation](#installation)
- [How it works](#how-it-works)
- [Contributing](#contributing)

## Installation
To get started with Gmail Unsubscriber, follow these steps:

1. **Get a Gmail API Key**: You will need a Gmail API key to interact with your Gmail account. Follow the instructions provided in this tutorial to get your Gmail API key.[![Video Tutorial](https://i.ytimg.com/vi/1Ua0Eplg75M/maxresdefault.jpg)](https://www.youtube.com/watch?v=1Ua0Eplg75M)

2. **Download the Credentials File**: After obtaining the Gmail API key, download the credentials.json file and place it inside the directory of your project. 
3. **Install Python Dependencies**: Open your terminal inside the project directory and do the command below to install all the dependencies. 
```commandline
pip install -r requirements.txt
```
3.5(Optional): **Exclude Mails**: Add mails you want to exclude into exclude.txt

4.**Run the Project**: Run the main.py file It will prompt you to select a gmail account select one, and It'll get to work.


## How It Works
Gmail Unsubscriber works by following a series of steps to automate the process of unsubscribing from spam emails:

1. **Search for Mails with "Unsubscribe" Label**: The project starts by searching all mails with the label "Unsubscribe". This label is commonly used by email service providers to indicate spam or unwanted emails.

2. **Find Mail IDs**: After finding all the mails with the "Unsubscribe" label, the project will search until it finds all the mail IDs. These IDs are unique identifiers for each email and are used to interact with the emails programmatically.

3. **Extract Unsubscribe Link**: For each email, the project will extract the unsubscribe link from the raw message header. This link is typically found in the email header and is used to unsubscribe the recipient from the email list.

4. **Open Unsubscribe Link**: The project will then open the unique links in the file, which is mandatory as browsers are not built for 3000+ tabs. This is done using Selenium, a tool for automating web browsers.

5. **Unsubscribe and Archive**: If some links did the unsubscription automatically, some needed to click on buttons and gave feedback. After the unsubscribe link is opened, the project will attempt to unsubscribe the email. After successful unsubscription, the email is moved to the archive.

Please note that due to the nature of the Gmail API and the way email clients handle unsubscribe links, not all emails can be unsubscribed. However, the project will attempt to unsubscribe a majority of them.


## Contributing
Contributions are always welcome. If you'd like to contribute, please fork the repository and use a feature branch. Pull requests are warmly welcome.

## Contact
If you need any help or have any questions, feel free to reach out to me on Discord. My Discord ID is @hellbri8nger
