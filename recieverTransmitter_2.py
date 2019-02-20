"""
Event Monitor for Cozmo
============================
Based on Event Monitor for cozmo-tools:
https://github.com/touretzkyds/cozmo-tools
Created by: David S. Touretzky, Carnegie Mellon University
Edited by: GrinningHermit
=====
"""
#
# import re
import threading
# import time
# import cozmo
import socket
import queue
import sys
import time
# import traceback

q = queue.Queue() # dependency on queue variable for messaging instead of printing to event-content directly
# custom eventlistener for picked-up and falling state, more states could be added
class Reciever (threading.Thread):
    def __init__(self, thread_id, name, _q, flag,sock, address, poc_address):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.q = _q
        self.flag = flag
        self.sock = sock
        self.sock.bind(address)
        self.seenAddress = []
        self.poc_address = poc_address
        self.serverAddress = address

    def run(self):
        if not (self.poc_address[0] == '0.0.0.0' and self.poc_address[1] == 0):
            tempPacket = "4" + self.flag +"," +self.serverAddress[0] + "," + str(self.serverAddress[1])
            self.q.put((tempPacket.encode('utf-8'), self.poc_address))
            self.seenAddress.append(('F', self.poc_address[0], self.poc_address[1]))
        while True:
            # try:
            #     error = None
            #     result = None
            #     data, addr = self.sock.recvfrom(self.port)
            #     print
            #     "Got message..."
            #     temp = self.analyze(data, addr)
            #     self.q.put(temp)
            # except:
            temp = "failure"
            print(temp)
            data, addr = self.sock.recvfrom(1024)
            print ('data received = ', data, ', address received from = ', addr)
            self.analyze(data, addr)


    def analyze(self, data, addr):
        tempDataValue = data.decode('utf-8')
        packetType = tempDataValue[0]
        dataValue = tempDataValue[1:]
        if packetType == '4':
            print("Peer Discovery packet received")
            self.peerdiscovery(dataValue, addr)
        elif self.flag == 'F':
            #please add ring logic to figure out next server address
            #modify this
            print("seen addresses ", addr)
            if addr not in self.seenAddress:
                self.seenAddress.append(addr)
                self.q.put((data, self.seenAddress[0]))
            elif addr == self.seenAddress[0]:
                temp = self.seenAddress[1]
                self.q.put((data, temp))
            elif addr == self.seenAddress[1]:
                temp = self.seenAddress[0]
                self.q.put((data, temp))


        elif self.flag == 'R':
            #please add ring logic to figure out next server address
            if packetType == '1':
                self.q.put((data, addr))
            elif packetType == '2':
                print("keep alive packet received")
            elif packetType == '3':
                print("RTT packet received")
            elif packetType == '5':
                print("acknowledge packet received")
            else:
                print("unsupported packet")

    def peerdiscovery(self, data, addr):
        split = data.split(",")
        tempAddr = (split[0],split[1], int(split[2]))
        if tempAddr not in self.seenAddress:
            for addressTemp in self.seenAddress:
                tempPair = (addressTemp[1], addressTemp[2])
                if(tempPair!=addr):
                    tempPacket = "4" + addressTemp[0]+ "," + addressTemp[1] + "," + str(addressTemp[2])
                    print("temp send back to sender", tempPacket, "address", addr)
                    self.q.put((tempPacket.encode('utf-8'), addr))
                tempPacket1 = "4" + data
                print("temp sender address to others", tempPacket1, "address", addressTemp)

                self.q.put((tempPacket1.encode('utf-8'), tempPair))
            self.seenAddress.append(tempAddr)
        # else:
        #     if(len(self.seenAddress) != 4):
        #         for addressTemp in self.seenAddress:
        #             print("")
        #             print ("addressTemp", addressTemp)
        #             print("addr", addr)
        #             print("tempAddr", tempAddr)
        #             print("boolean1", (addressTemp != addr))
        #             print("boolean2", (addressTemp != tempAddr))
        #             if(addressTemp != addr) and (addressTemp != tempAddr):
        #                 tempPacket = "4" + tempAddr[0] + "," + str(tempAddr[1])
        #                 print("else temp ", tempPacket, "address", addressTemp)
        #                 self.q.put((tempPacket.encode('utf-8'), addressTemp))
        #         if tempAddr not in self.seenAddress:
        #             self.seenAddress.append(tempAddr)

        print("self seen Address", self.seenAddress)

class Transmitter (threading.Thread):
    def __init__(self, thread_id, name, _q, type, sock, address):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.q = _q
        self.type = type
        self.sock = sock
        self.address = address

    def run(self):
        # address = ('127.0.0.1', 5600)
        while True:
            # try:
            #     error = None
            #     result = None
            #     self.sock.sendto(temp[0], address)
            #     print
            #     "sent message..."
            #  except:
            if self.q.empty():
                time.sleep(5)
            if not self.q.empty():
                temp = self.q.get()
                print("transmit data and address", temp)
                self.sock.sendto(temp[0], temp[1])
            elif self.type == 'S':
                typeOfPacket = input('Choose a packet type: ')
                query = input('Choose a number: ')
                temp1 = typeOfPacket+query
                print("query stuff: ", query)
                temp = (temp1.encode('utf-8'), self.address)
                print("temp ", temp)
                self.sock.sendto(temp[0], self.address)


            # query = input('Choose a number: ')
            # query = "hello"


            # print
            # "Sending result..."



if __name__ == '__main__':

    if len(sys.argv) != 6:
        print("Wrong number of arguments")
        sys.exit(1)
    try:
        flag = sys.argv[1]
        if len(flag) != 1:
            print("Invalid flag number")
            sys.exit(1)
    except:
        print("Invalid flag number")
        sys.exit(1)
    try:
        local_port = int(sys.argv[2])
        if local_port > 65536:
            print("Invalid port number")
            sys.exit(1)
    except:
        print("Invalid port number")
        sys.exit(1)
    poc_host = sys.argv[3]
    try:
        poc_port = int(sys.argv[4])
        if poc_port > 65536:
            print("Invalid port number")
            sys.exit(1)
    except:
        print("Invalid port number")
        sys.exit(1)
    try:
        numberOfHosts = int(sys.argv[5])
    except:
        print("Invalid number of hosts")
        sys.exit(1)
    # cozmo thread
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (socket.gethostbyname(socket.gethostname()), local_port)
    #server_address = ('127.0.0.1', local_port)
    print("sever address ", server_address)

    address = (socket.gethostbyname(poc_host), poc_port)
    recev_thread = Reciever(1,'Receive', q, flag, sock, server_address, address)
    transmit_thread = Transmitter(1,'Transmitter', q, flag, sock, address)
    recev_thread.start()
    transmit_thread.start()

