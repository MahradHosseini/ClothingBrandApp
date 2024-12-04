from socket import *
from tkinter import *
from tkinter import messagebox


class ClientScreen(Frame):
    def __init__(self, clientSocket):
        Frame.__init__(self)
        self.pack()
        self.username = None
        self.clientSocket = clientSocket

        width, height = 600, 300
        screenWidth, screenHeight = self.master.winfo_screenwidth(), self.master.winfo_screenheight()

        x = (screenWidth - width) // 2
        y = (screenHeight - height) // 2

        self.master.geometry(f"{width}x{height}+{x}+{y}")

        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

        self.showLoginScreen()

    def showLoginScreen(self):
        self.master.title("Login")
        self.pack(fill=BOTH, expand=True)

        for i in range(3):
            self.rowconfigure(i, weight=1)
        for j in range(2):
            self.columnconfigure(j, weight=1)

        usernameLabel = Label(self, text="Username:")
        usernameLabel.grid(row=0, column=0,sticky="se")

        self.usernameEntry = Entry(self)
        self.usernameEntry.grid(row=0, column=1,sticky="sw",padx=8)
        self.usernameEntry.bind("<Return>", lambda event: self.handleLogin())

        passwordLabel = Label(self, text="Password:")
        passwordLabel.grid(row=1, column=0,sticky="e")

        self.passwordEntry = Entry(self, show="*")
        self.passwordEntry.grid(row=1, column=1,sticky="w",padx=8)
        self.passwordEntry.bind("<Return>", lambda event: self.handleLogin())

        loginButton = Button(self, text="Login", command=self.handleLogin, width=10, height=1)
        loginButton.grid(row=2, column=0, columnspan=2,sticky="n")

        self.master.minsize(400, 300)
        self.master.maxsize(800, 400)

    def handleLogin(self):
        clientMsg = f"login;{self.usernameEntry.get()};{self.passwordEntry.get()}".encode()
        self.clientSocket.send(clientMsg)

        serverMsg = self.clientSocket.recv(1024).decode()

        if serverMsg == "loginfailure":
            messagebox.showerror("Login failure", "Login failure")
        else:
            self.username = serverMsg.split(";")[1]
            role = serverMsg.split(";")[-1]
            if role == "store":
                self.showStorePanel()
            elif role == "analyst":
                self.showAnalystPanel()

    def showStorePanel(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.master.title("Store Panel")

        itemsLabel = Label(self, text="Items", font=("Arial", 20))
        itemsLabel.grid(row=0, column=0, columnspan=2)

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
            quantityEntry.grid(row=i, column=2, sticky=W,padx=10)
            self.quantityEntries[item] = quantityEntry

            # Color buttons
            colorLabel = Label(self, text="Color:")
            colorLabel.grid(row=i, column=3, sticky="w")
            colorVar = StringVar(value="red")
            redRadio = Radiobutton(self, text="Red", variable=colorVar, value="red")
            blackRadio = Radiobutton(self, text="Black", variable=colorVar, value="black")
            redRadio.grid(row=i, column=3,sticky="e")
            blackRadio.grid(row=i, column=4,padx=10)
            self.colorVars[item] = colorVar

        customerLabel = Label(self, text="Customer Name:")
        customerLabel.grid(row=len(self.items) + 1, column=0, columnspan=2, padx=10,sticky="e")

        self.customerEntry = Entry(self, width=15)
        self.customerEntry.grid(row=len(self.items) + 1, column=1, columnspan=2, sticky="e")

        purchaseButton = Button(self, text="Purchase", command=self.handlePurchase, width=10, height=1)
        purchaseButton.grid(row=len(self.items) + 2, column=0, pady=10, padx=10,sticky="e")

        returnButton = Button(self, text="Return", command=self.handleReturn, width=10, height=1)
        returnButton.grid(row=len(self.items) + 2, column=1, pady=10, padx=10)

        closeButton = Button(self, text="Close", command=self.master.destroy, width=10, height=1)
        closeButton.grid(row=len(self.items) + 2, column=3, pady=10, padx=10)

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
            store = self.username
            customerName = self.customerEntry.get()
            totalQuantity = 0
            for item in selectedItems:
                totalQuantity += int(item.split("-")[0])
            clientMsg = f"purchase;{store};{totalQuantity};{','.join(selectedItems)};{customerName}"
            print(clientMsg)

            self.clientSocket.send(clientMsg.encode())
        else:
            messagebox.showerror("No Items Selected", "No items selected")
            return

        serverMsg = self.clientSocket.recv(1024).decode().split(";")

        if serverMsg[0] == "purchasesuccess":
            messagebox.showinfo("Purchase successful", f"Purchase with total cost of {serverMsg[1]} was successful.")
        else:
            messagebox.showerror("Availability Error", f"Following items not available:\n" + "\n".join(serverMsg[1:]))

    def handleReturn(self):
        selectedItems = self.getSelectedItems()

        if selectedItems:
            store = self.username
            customerName = self.customerEntry.get()
            totalQuantity = 0
            for item in selectedItems:
                totalQuantity += int(item.split("-")[0])
            clientMsg = f"return;{store};{totalQuantity};{','.join(selectedItems)};{customerName}"
            self.clientSocket.send(clientMsg.encode())
        else:
            messagebox.showerror("No Items Selected", "No items selected")
            return

        serverMsg = self.clientSocket.recv(1024).decode().split(";")

        if serverMsg[0] == "returnsuccess":
            messagebox.showinfo("Message", "Returned Successfully")
        else:
            messagebox.showerror("Message", "unsuccessful operation – please recheck the items")


    def showAnalystPanel(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.master.title("Analyst Panel")

        self.frame1 = Frame(self)
        self.frame1.pack(padx=5, pady=5)

        self.Label1 = Label(self.frame1, text="Reports", font=("Arial", 20))
        self.Label1.pack(padx=5, pady=10)
        # Creating the report options
        report_options = [
            "What is the most bought item?",
            "Which store has the highest number of operations?",
            "What is the total generated income of the store?",
            "What is the most returned color for the basic T-shirt?"
        ]
        self.chosenReport = StringVar()
        self.chosenReport.set(report_options[0])

        for report in report_options:
            aButton = Radiobutton(self.frame1, text=report, variable=self.chosenReport, value=report)
            aButton.pack(padx=5, pady=5, anchor="w")

        # Creating the Create and Close buttons
        self.frame2 = Frame(self)
        self.frame2.pack(padx=5, pady=5)

        self.CreateButton = Button(self.frame2, text="Create", command=self.handleCreateReport, width=10, height=1)
        self.CreateButton.pack(padx=40, pady=20, side=LEFT)

        self.CloseButton = Button(self.frame2, text="Close", command=self.master.destroy, width=10, height=1)
        self.CloseButton.pack(padx=40, pady=20, side=LEFT)


    def handleCreateReport(self):
       # Check which report option is selected and send the msg to server
       if self.chosenReport.get() == "What is the most bought item?":
           clientMsg = "report1"
       elif self.chosenReport.get() == "Which store has the highest number of operations?":
           clientMsg = "report2"
       elif self.chosenReport.get() == "What is the total generated income of the store?":
           clientMsg = "report3"
       else:
           clientMsg = "report4"
       # Communicate with the server
       self.clientSocket.send(clientMsg.encode())
       serverMsg = self.clientSocket.recv(1024).decode()
       report = serverMsg.split(";")[1:]

       # Display the message box
       messagebox.showinfo("Report", "\n".join(report))

def connectToServer(host, port):
    try:
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.connect((host, port))
        return clientSocket
    except Exception as e:
        messagebox.showerror("Error", f"Failed to connect to server: {e}")
        return None


if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 5000

    clientSocket = connectToServer(HOST, PORT)
    if clientSocket:
        try:
            # Wait for the server's initial response
            initialResponse = clientSocket.recv(1024).decode()
            if initialResponse == 'connectionsuccess':
                # Launch the client GUI
                window = ClientScreen(clientSocket)
                window.mainloop()
            else:
                messagebox.showerror("Error", "Connection Error: Unexpected server response")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            # Close the socket when done
            clientSocket.close()
