from socket import *
from tkinter import *
from tkinter import messagebox

from bokeh.layouts import column


class ClientScreen(Frame):
    def __init__(self, clientSocket):
        Frame.__init__(self)
        self.clientSocket = clientSocket
        self.showLoginScreen()

    def showLoginScreen(self):
        self.master.title("Login")
        self.pack()

        self.usernameLabel = Label(self, text="Username:")
        self.usernameLabel.pack(side=LEFT)

        self.usernameEntry = Entry(self)
        self.usernameEntry.pack(side=RIGHT)

        self.passwordLabel = Label(self, text="Password:")
        self.passwordLabel.pack(side=LEFT)

        self.passwordEntry = Entry(self)
        self.passwordEntry.pack(side=RIGHT)

        self.loginButton = Button(self, text="Login", command=self.handleLogin)
        self.loginButton.pack(side=CENTER)

    def handleLogin(self):
        clientMsg = f"login;{self.usernameEntry.get()};{self.passwordEntry.get()}".encode()
        self.clientSocket.send(clientMsg)

        serverMsg = self.clientSocket.recv(1024).decode()

        if serverMsg == "loginfailure":
            messagebox.showerror("Login failure", "Login failure")
        else:
            role = serverMsg.split(";")[-1]
            if role == "store":
                self.showStorePanel()
            elif role == "analyst":
                self.showAnalystPanel()

    def showStorePanel(self):
        self.itemsLabel = Label(self, text="Items", font=("Arial", 20))
        self.itemsLabel.grid(row=0, column=0, columnspan=2)

        self.items = ["Basic T-shirt", "Leather Jacket", "Robe of the Weave",
                 "Plaid Shirt", "D4C Graphic T-shirt",
                 "Denim Jeans", "Hodd-Toward Designer Shorts"]

        self.itemVars = {}
        self.quantityEntries = {}
        self.colorVars = {}

        for i, item in enumerate(self.items, start=1):
            # The items' checkboxes
            itemVar = BooleanVar()
            checkbox = Checkbutton(self, text=item, variable=itemVar)
            checkbox.grid(row=i, column=0, sticky=W, padx=10)
            self.itemVars[item] = itemVar

            # Quantity labels and entries
            quantityLabel = Label(self, text="Quantity:")
            quantityLabel.grid(row=i, column=1, sticky=E, padx=10)
            quantityEntry = Entry(self, width=10)
            quantityEntry.grid(row=i, column=2, sticky=W)
            self.quantityEntries[item] = quantityEntry

            # Color buttons
            colorVar = StringVar(value="red")
            redRadio = Radiobutton(self, text="Red", variable=colorVar, value="red")
            blackRadio = Radiobutton(self, text="Black", variable=colorVar, value="black")
            redRadio.grid(row=i, column=3, sticky=W)
            blackRadio.grid(row=i, column=4, sticky=W)
            self.colorVars[item] = colorVar

        customerLabel = Label(self, text="Customer Name:")
        customerLabel.grid(row=len(self.items) + 1, column=0, columnspan=2, sticky=W)

        self.customerEntry = Entry(self, width=10)
        self.customerEntry.grid(row=len(self.items) + 1, column=1, columnspan=2, sticky=W)

        purchaseButton = Button(self, text="Purchase", command=self.handlePurchase)
        purchaseButton.grid(row=len(self.items) + 2, column=1, pady=10)

        returnButton = Button(self, text="Return", command=self.handleReturning)
        returnButton.grid(row=len(self.items) + 2, column=2, pady=10)

        closeButton = Button(self, text="Close", command=self.destroy)
        closeButton.grid(row=len(self.items) + 2, column=3, pady=10)


    def getSelectedItems(self):
        selectedItems = []
        for i, item in enumerate(self.items, start=1):
            if self.itemVars[item].get():
                quantity = self.quantityEntries[item].get()
                color = self.colorVars[item].get()
                if quantity.isdigit() and int(quantity) > 0:
                    selectedItems.append(f"{quantity}-{i}-{color}")
        return selectedItems

    def handlePurchase(self):
        selectedItems = self.getSelectedItems()

        if selectedItems:
            store = self.usernameEntry.get()
            customerName = self.customerEntry.get()
            clientMsg = f"purchase;{store};{customerName};{','.join(selectedItems)}".encode()
            clientSocket.send(clientMsg)
        else:
            messagebox.showerror("No Items Selected", "No items selected")

        serverMsg = self.clientSocket.recv(1024).decode().split(";")

        if serverMsg[0] == "purchasesuccess":
            messagebox.showinfo("Purchase successful", f"Purchase with total cost of {serverMsg[1]} was successful.")
        else:
            messagebox.showerror("Availability Error", f"Following items not available:\n" + "\n".join(serverMsg[1:]))
            

    def showAnalystPanel(self):
        pass


if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 5000
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((HOST, PORT))

    if clientSocket.recv(1024).decode() == 'connectionsuccess':
        window = ClientScreen(clientSocket)
        window.mainloop()
    else:
        messagebox.showerror("Error", "Connection Error")
