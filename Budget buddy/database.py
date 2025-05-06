from imports import *
from InvoiceClass import Invoice


def save_invoices(invoice):
    connection = sqlite3.connect('invoices.db')
    cursor = connection.cursor()
    command = "INSERT INTO Invoices (Number, Price, Date, Category) VALUES (?, ?, ?, ?)"
    cursor.execute(command, (invoice.number, invoice.price, invoice.date, invoice.category))
    connection.commit()
    connection.close()


def get_invoices():
    connection = sqlite3.connect('invoices.db')
    cursor = connection.cursor()
    command = "SELECT * FROM Invoices"
    cursor.execute(command)
    invoices = cursor.fetchall()

    invoices_list = []
    invoice_list_text = []

    for invoice in invoices:
        invoice_obj = Invoice(invoice[1], invoice[2], invoice[3], invoice[4])
        invoices_list.append(invoice_obj)

    for invoice in invoices_list:
        invoice_list_text.append(str(invoice))

    return invoice_list_text


print(get_invoices())
