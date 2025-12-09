from pypdf import PdfReader
import pandas as pd
from io import StringIO
import re
import logging

#Read text from PDF
reader = PdfReader("../artifacts/Statements.pdf")
page = reader.pages[2]
page_content = page.extract_text()
match = re.search(
    r"ACCOUNT ACTIVITY.*?\$ Amount\s*(.*?)\s*Total fees charged in",
    page_content,
    flags=re.DOTALL
)
if match:
    account_activity = match.group(1).strip()
else:
    account_activity = None

account_activity_lines_list = account_activity.split("\n")
account_activity_header_csv = "Date of Transaction,Description,$ Amount,Category,Sub-Category\n"

#Get date from PDF
page = reader.pages[0]
page_content = page.extract_text()
pattern = r"(\d{1,2}\/\d{1,2}\/\d{2})\s*-\s*(\d{1,2}\/\d{1,2}\/\d{2})"
match = re.search(pattern, page_content)
statement_end_date = match.groups()[1].replace("/","-")

def redact (transaction) :
    if "SIMMS" in transaction:
        transaction = "%"
    return transaction

def categorize (transaction) :
    groceries = ("WHOLE", "KING SOOPERS", "EDWARDS")
    pets = ("Pet", "PetCo")
    subscriptions = ("VIX", "Paramount", "Audible", "ESPN", "Spotify")
    car = ("Conoco", "Phillips 66")
    if any(keyword in transaction.upper() for keyword in groceries):
        return "Groceries"
    if any(keyword in transaction.upper() for keyword in pets):
        return "Pets"
    if any(keyword in transaction.upper() for keyword in subscriptions):
        return "Pets"
    return ""

#Convert lines to CSV format
def convert_account_activity_content_to_csv (list_of_activity_lines) :
    converted_activity_line_str = ""
    for line in list_of_activity_lines:
        pattern = r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+(-?\d+\.\d{2})$'
        match = re.match(pattern, line)
        if match:
            transaction_date, description, amount = match.groups()
            description = redact(description)
            category = categorize(description)
            statement = transaction_date + "," + description + "," + amount + "," + category + "\n"
            converted_activity_line_str += statement
    return converted_activity_line_str

#Write to csv
def write_to_csv (pdf_content_str, statement_end_date_str) :
    filename = "../artifacts/monthly_statement_{date_str}.csv".format(date_str=statement_end_date_str)
    df = pd.read_csv(StringIO(pdf_content_str))
    df.to_csv(filename, index=False)
    logging.info("Transaction activity saved to {filename}".format(filename=filename))

def main():
    logging.info("Starting main function")
    account_activity_content_csv = convert_account_activity_content_to_csv(account_activity_lines_list)
    account_activity_complete_csv = account_activity_header_csv + account_activity_content_csv
    write_to_csv(account_activity_complete_csv, statement_end_date)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,  # Set minimum log level
        format="%(asctime)s %(levelname)s %(message)s",
    )
    main()