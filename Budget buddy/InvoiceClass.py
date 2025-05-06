class Invoice:

    def __init__(self, number, price, date, category):
        self.number = number
        self.price = price
        self.date = date
        self.category = category

    def __str__(self):
        return f'Number: {self.number}, Date: {self.date}, Category: {self.category}, Price: {self.price}'