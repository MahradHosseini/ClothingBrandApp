from socket import *
from threading import *
from re import *


class ClientThread(Thread):
    def __init__(self, clientSocket, clientAddress):
        Thread.__init__(self)
        self.clientSocket = clientSocket
        self.clientAddress = clientAddress

    def run(self):
        serverMsg = "connectionsuccess".encode()
        self.clientSocket.send(serverMsg)
        clientMsg = self.clientSocket.recv(1024).decode()

        while clientMsg != "close":

            command = clientMsg.split(";")[0]

            if command == "login":
                # Client's login message format: login;username;password
                # Users.txt format: username;password;role
                username = clientMsg.split(";")[1]
                password = clientMsg.split(";")[2]
                authenticationSuccessful = False
                with open("users.txt", "r") as file:
                    for line in file.readlines():
                        if username == line.split(";")[0] and password == line.split(";")[1]:
                            # Login approval format: loginsuccess;username;role
                            serverMsg = f"loginsuccess;{username};{line.split(";")[2]}".encode()
                            authenticationSuccessful = True

                if not authenticationSuccessful:
                    serverMsg = "loginfailure".encode()

                self.clientSocket.send(serverMsg)

            elif command == "purchase":
                # Purchase format: purchase;store;total;quantity-itemID-color, quantity-itemID-color...
                # Items.txt format: itemID;itemName;color;price;stockAvailable
                with open("items.txt", "r") as file:
                    order = clientMsg.split(";")[-1]
                    suborders = order.split(",")
                    availableItems = []
                    unavailableItems = []

                    lines = file.readlines()


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
                        unavailableItems.append(f"{lineData[1]} ({color})")

                if unavailableItems:
                    serverMsg = "availabilityerror" + ";".join(unavailableItems)
                    self.clientSocket.send(serverMsg.encode())
                else:
                    updatedItems = []
                    totalOrderCost = 0

                    for line in lines:
                        lineData = line.strip().split(";")
                        for item, qty in availableItems:
                            if lineData[0] == item[0] and lineData[2] == item[2]:
                                lineData[4] = str(int(lineData[4]) - qty)
                                totalOrderCost += qty * int(item[3])
                        updatedItems.append(";".join(lineData))

                    with open("items.txt", "w") as file:
                        file.write("\n".join(updatedItems) + "\n")

                    with open("operations.txt", "a") as file:
                        # Purchase Op Format: purchase;store;customerName;quantity-itemID-color,quantity-itemID-color...
                        file.write(clientMsg + "\n")

                    serverMsg = f"purchasesuccess;{totalOrderCost}".encode()
                    self.clientSocket.send(serverMsg)


        self.clientSocket.close()
