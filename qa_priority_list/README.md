This script allows us to read/write documents on GOOGLE drive

Configuration:
==============

- Follow instructions on https://pygsheets.readthedocs.io/en/latest/authorizing.html in order to allow python to read/write
  * Select storage Admin
  * Copy the "Service account ID" created
- Share the document with the email created as "Service account ID"
- Store the credentials json file because we need it so python can perform actions on drive.
- Add ENV variables like
  * FILE_KEY: is the key of the google sheet, you can get it from the url
  * SHARE_ACCOUNTS: the emails that will be able to see the files generated
  * CREDENTIALS: The json that was generated used the above steps.
  * DB_HOST = Database host
  * DB_NAME = Database name
  * DB_USER = Database user
  * DB_PWD = Database pass
  