from notion_client import Client
import requests
import json

from InvoiceClass import Invoice

NOTION_TOKEN = "NOTION_TOKEN"
DATABASE_ID = "DATABASE_ID"
notion = Client(auth=NOTION_TOKEN)

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}


def get_pages():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {"page_size": 100}

    r = requests.post(url, json=payload, headers=headers)  # Use POST
    data = r.json()

    # Save to a file for inspection
    with open("notion_data.json", "w") as f:
        json.dump(data, f, indent=4)

    results = data["results"]
    return results


def write_data_to_notion(data):
    response = notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties={
                "Number": {
                    "title": [
                        {
                            "text": {
                                "content": data.number
                            }
                        }
                    ]
                },
                "Date": {
                    "rich_text": [
                        {
                            "text": {
                                "content": data.date
                            }
                        }
                    ]
                },
                "Price": {
                    "number": data.price
                },
                "Category": {
                    "rich_text": [
                        {
                            "text": {
                                "content": data.category
                            }
                        }
                    ]
                }
            }
        )
    print(f"Page created: {response['id']}")


def get_all_data():
    invoices_list = []
    pages = get_pages()

    for page in pages:
        props = page["properties"]

        number = props.get("Number", {}).get("title", [{}])[0].get("text", {}).get("content", None)
        date = props.get("Date", {}).get("rich_text", [{}])[0].get("text", {}).get("content", None)
        price = props.get("Price", {}).get("number", None)
        category = props.get("Category", {}).get("rich_text", [{}])[0].get("text", {}).get("content", None)

        row = Invoice(number, price, date, category)
        invoices_list.append(str(row))

    return invoices_list


# Call the function
print(get_all_data())
