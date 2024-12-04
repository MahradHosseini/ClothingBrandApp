from socket import *
from threading import *
from threading import RLock

fileLock = RLock() # Using RLock mechanism to avoid race conditions

class ClientThread(Thread):
    def __init__(self, clientSocket, clientAddress):
        Thread.__init__(self)
        self.clientSocket = clientSocket
        self.clientAddress = clientAddress

    '''
        Method responsible for authenticating the users
        Takes client's message
        Returns a message to be sent to the client
    '''
    @staticmethod
    def loginCommand(clientMsg):
        # Client's login message format: login;username;password
        # Users.txt format: username;password;role
        username = clientMsg.split(";")[1]
        password = clientMsg.split(";")[2]
        authenticationSuccessful = False

        # Gaining the lock
        with fileLock:
            with open("users.txt", "r") as file:
                for line in file:
                    lineData = line.strip().split(";")
                    if username == lineData[0] and password == lineData[1]:
                        # Login approval format: loginsuccess;username;role
                        serverMsg = f"loginsuccess;{username};{lineData[2]}"
                        authenticationSuccessful = True
                        break

        if not authenticationSuccessful:
            serverMsg = "loginfailure"

        return serverMsg

    '''
        Method responsible for validating purchase request, updating the items.txt, and operations.txt if necessary
        Takes client's message
        Returns a message to be sent to the client
    '''
    @staticmethod
    def purchaseCommand(clientMsg):
        # Purchase format: purchase;store;totalQuantity;quantity-itemID-color, quantity-itemID-color...;customerName
        # Items.txt format: itemID;itemName;color;price;stockAvailable
        with fileLock:
            with open("items.txt", "r") as file:
                lines = file.readlines()

            order = clientMsg.split(";")[-2]
            suborders = order.split(",")

            # Separating available and unavailable items
            availableItems = []
            unavailableItems = []
            for suborder in suborders:
                suborderAvailable = False
                quantity, itemID, color = suborder.split("-")
                quantity = int(quantity)

                for line in lines:
                    lineData = line.strip().split(";")

                    if itemID == lineData[0] and color == lineData[2] and quantity <= int(lineData[4]):
                        suborderAvailable = True
                        availableItems.append((lineData, quantity))
                        break

                if not suborderAvailable:
                    for line in lines:
                        lineData = line.strip().split(";")
                        if itemID == lineData[0]:
                            itemName = lineData[1]
                            break
                    unavailableItems.append(f"{itemName} ({color})")

            if unavailableItems:
                serverMsg = "availabilityerror;" + ";".join(unavailableItems)
            else: # If there's no unavailable items requested then proceeds to here
                updatedItems = []
                totalOrderCost = 0

                # Preparing the updated items list plus calculating the total order cost
                for line in lines:
                    lineData = line.strip().split(";")
                    for item, qty in availableItems:
                        if lineData[0] == item[0] and lineData[2] == item[2]:
                            lineData[4] = str(int(lineData[4]) - qty)
                            totalOrderCost += qty * int(item[3])
                    updatedItems.append(";".join(lineData))

                # Writing the updated items list to the items.txt
                with open("items.txt", "w") as file:
                    file.write("\n".join(updatedItems) + "\n")

                # Adding the operation to the operations.txt
                with open("operations.txt", "a") as file:
                    # Purchase Op Format: purchase;store;customerName;quantity-itemID-color,quantity-itemID-color...
                    clientMsgData = clientMsg.split(";")
                    operationString = f"{clientMsgData[0]};{clientMsgData[1]};{clientMsgData[-1]};{clientMsgData[3]}"
                    file.write(operationString + "\n")

                serverMsg = f"purchasesuccess;{totalOrderCost}"

        return serverMsg

    '''
        Method responsible for validating return request, updating the items.txt, and operations.txt if necessary
        Takes client's message
        Returns a message to be sent to the client
    '''
    @staticmethod
    def returnCommand(clientMsg):
        # Format: return;store;totalQuantity;quantity-itemID-color,quantity-itemID-color...;customerName
        # Items.txt format: itemID;itemName;color;price;stockAvailable
        # Operations.txt format: purchase;store;customerName;quantity-itemID-color,... or return;store;customerName;quantity-itemID-color,...
        returnReq = clientMsg.split(";")
        store = returnReq[1]
        customerName = returnReq[-1]
        returnItems = returnReq[-2].split(",")

        with fileLock:
            with open("operations.txt", "r") as operationsFile:
                operations = operationsFile.readlines()

            # Checking to see if the items that are going to be returned, had been bought by the same customer before
            validReturn = True
            for item in returnItems:
                quantity, itemID, color = item.split("-")
                quantity = int(quantity)

                itemFound = False
                for operation in operations:
                    if(
                        operation.startswith("purchase") and
                        store in operation and
                        customerName in operation and
                        f"{quantity}-{itemID}-{color}" in operation
                    ):
                        itemFound = True
                        break

                if not itemFound:
                    validReturn = False
                    break

            if not validReturn:
                serverMsg = "returnerror"
            else: # If the return request is valid, proceeds to here
                with open("items.txt", "r") as itemsFile:
                    items = itemsFile.readlines()

                # Returning the returned items to the stock
                updatedItems = []
                for line in items:
                    itemData = line.strip().split(";")
                    for item in returnItems:
                        quantity, itemID, color = item.split("-")
                        quantity = int(quantity)

                        if itemID == itemData[0] and color == itemData[2]:
                            itemData[4] = str(int(itemData[4]) + quantity)
                    updatedItems.append(";".join(itemData))

                with open("items.txt", "w") as itemsFile:
                    itemsFile.write("\n".join(updatedItems) + "\n")

                # Adding the return operation to the operations.txt
                with open("operations.txt", "a") as operationsFile:
                    operationString = f"{returnReq[0]};{returnReq[1]};{returnReq[-1]};{returnReq[3]}"
                    operationsFile.write(operationString + "\n")

                serverMsg = "returnsuccess"

        return serverMsg

    '''
        Method responsible for generating report one (Most bought item/s)
        Returns a message to be sent to the client
    '''
    @staticmethod
    def reportOne():
        with fileLock:
            with open("operations.txt", "r") as operationsFile:
                operations = operationsFile.readlines()

            # Counting all the sold items and keeping them in a dict
            purchaseCounts = {}
            for operation in operations:
                if operation.startswith("purchase"):
                    purchaseItems = operation.strip().split(";")[3].split(",")
                    for item in purchaseItems:
                        quantity, itemID, _ = item.split("-")
                        quantity = int(quantity)

                        if itemID not in purchaseCounts:
                            purchaseCounts[itemID] = 0
                        purchaseCounts[itemID] += quantity

            # Extracting the most bought item/s from the dict
            maxCount = max(purchaseCounts.values())
            mostBoughtItems = [itemID for itemID, count in purchaseCounts.items() if count == maxCount]

            # Extracting the names of the items from their IDs
            with open("items.txt", "r") as itemsFile:
                itemsData = itemsFile.readlines()

            itemNames = []
            for itemID in mostBoughtItems:
                for line in itemsData:
                    lineData = line.strip().split(";")
                    if itemID == lineData[0]:
                        itemNames.append(lineData[1])
                        break
            serverMsg = f"report1;{';'.join(itemNames)}"

        return serverMsg

    '''
        Method responsible for generating report two (Store/s with the highest number of operations)
        Returns a message to be sent to the client
    '''
    @staticmethod
    def reportTwo():
        with fileLock:
            with open("operations.txt", "r") as operationsFile:
                operations = operationsFile.readlines()

        storeOperations = {}

        for operation in operations:
            operationParts = operation.strip().split(";")
            store = operationParts[1]

            if store not in storeOperations:
                storeOperations[store] = 0
            storeOperations[store] += 1

        maxOperations = max(storeOperations.values())
        topStores = [store for store, count in storeOperations.items() if count == maxOperations]
        serverMsg = f"report2;{';'.join(topStores)}"
        return serverMsg

    '''
        Method responsible for generating report three (Total generated income)
        Returns a message to be sent to the client
    '''
    @staticmethod
    def reportThree():
        with fileLock:
            with open("operations.txt", "r") as operationsFile:
                operations = operationsFile.readlines()
            with open("items.txt", "r") as itemsFile:
                items = itemsFile.readlines()

        priceLookup = {}
        for item in items:
            itemData = item.strip().split(";")
            itemID, color, price = itemData[0], itemData[2], int(itemData[3])
            priceLookup[f"{itemID}-{color}"] = price

        totalIncome = 0

        for operation in operations:
            operationData = operation.strip().split(";")
            operationType = operationData[0]
            itemsInOperation = operationData[3].split(",")

            for item in itemsInOperation:
                quantity, itemID, color = item.split("-")
                quantity = int(quantity)
                itemKey = f"{itemID}-{color}"

                if itemKey in priceLookup:
                    itemPrice = priceLookup[itemKey]
                    if operationType == "purchase":
                        totalIncome += quantity * itemPrice
                    elif operationType == "return":
                        totalIncome -= quantity * itemPrice

        serverMsg = f"report3;{totalIncome}"
        return serverMsg

    '''
        Method responsible for generating report four (Most returned color for Basic T-shirt)
        Returns a message to be sent to the client
    '''
    @staticmethod
    def reportFour():
        with fileLock:
            with open("operations.txt", "r") as operationsFile:
                operations = operationsFile.readlines()
            with open("items.txt", "r") as itemsFile:
                items = itemsFile.readlines()

        for item in items:
            itemData = item.strip().split(";")
            if itemData[1] == "Basic T-shirt":
                basicTShirtID = itemData[0]
                break

        returnsCount = {"red": 0, "black": 0}

        for operation in operations:
            if operation.startswith("return"):
                returnedItems = operation.strip().split(";")[3].split(",")
                for item in returnedItems:
                    quantity, itemID, color = item.split("-")
                    quantity = int(quantity)
                    if itemID == basicTShirtID:
                        returnsCount[color] += quantity

        if any(returnsCount.values()):
            maxReturns = max(returnsCount.values())
            mostReturnedColors = [color for color, count in returnsCount.items() if count == maxReturns]
            serverMsg = f"report4;{';'.join(mostReturnedColors)}"
        else:
            serverMsg = "report4;No returns"

        return serverMsg

    '''
        Overridden Run method responsible for reading the client's request and refer it to the correct function
    '''
    def run(self):
        try:
            serverMsg = "connectionsuccess".encode()
            self.clientSocket.send(serverMsg)
            while True:
                clientMsg = self.clientSocket.recv(1024).decode()
                if not clientMsg or clientMsg == "close":
                    break

                command = clientMsg.split(";")[0]

                if command == "login":
                    serverMsg = self.loginCommand(clientMsg)

                elif command == "purchase":
                    serverMsg = self.purchaseCommand(clientMsg)

                elif command == "return":
                    serverMsg = self.returnCommand(clientMsg)

                elif command == "report1":
                    serverMsg = self.reportOne()

                elif command == "report2":
                    serverMsg = self.reportTwo()

                elif command == "report3":
                    serverMsg = self.reportThree()

                elif command == "report4":
                    serverMsg = self.reportFour()

                else:
                    serverMsg = "unknowncommand"
                    print(f"Unknown command received: {clientMsg}")

                self.clientSocket.send(serverMsg.encode())

        except Exception as e:
            print(f"Error in client thread: {e}")

        finally:
            self.clientSocket.close()
            print(f"Connection closed with {self.clientAddress}")


if __name__ == "__main__":
    HOST = "127.0.0.1"
    PORT = 5000

    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serverSocket.bind((HOST, PORT))
    serverSocket.listen()

    print("Server is running....")

    # Accepting new clients and referring them to a new thread
    try:
        while True:
            clientSocket, clientAddress = serverSocket.accept()
            print(f"Connection established with {clientAddress}")
            newClient = ClientThread(clientSocket, clientAddress)
            newClient.start()

    except Exception as e:
        print(f"Error occurred during connection: {e}")

    # Making sure that the socket is closed properly at the end
    finally:
        serverSocket.close()
