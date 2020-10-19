import socket
from threading import Thread
import sys
import utils as ut


class Server:
    host = '0.0.0.0'
    port = 2680
    svr = None
    con_pool = []

    def __init__(self):
        """
        initialization of server
        """
        self.svr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.svr.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.svr.bind((self.host, self.port))
        self.svr.listen(12)
        print('* Server started, waiting for client to connect...')
        sys.stdout.flush()

    def accept_client(self, file_name):
        """
        accept new connections
        """
        while True:
            clt, addr = self.svr.accept()
            print('Got connection from', addr)
            sys.stdout.flush()
            self.con_pool.append(clt)
            accept_thread = Thread(target=self.send_file, args=(clt, addr, file_name))
            accept_thread.setDaemon(True)
            accept_thread.start()

    def send_file(self, clt, addr, file_name):
        """
        send files
        """
        data_file = open(file_name, 'rb')
        file_len = len(data_file.read())
        clt.send(ut.encode_str(str(file_len), ut.data_unit))  # send1: file length
        send_size = 0
        data_file.seek(0)
        while file_len != send_size:
            data_trans = data_file.read(ut.data_unit)
            clt.send(data_trans)                               # send2: file
            send_size += len(data_trans)
            # print('Transmission progress: %s:%s' % (send_size, file_len))
        print('Transmission completed!\n')
        sys.stdout.flush()
        data_file.close()
        clt.close()


if __name__ == '__main__':
    file_name = sys.argv[1]
    print(file_name)
    sys.stdout.flush()
    server = Server()
    server.accept_client(file_name)
    server.svr.close()
