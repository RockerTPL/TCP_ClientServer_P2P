import socket
import sys
import time
import utils as ut


class Client:
    host = '10.0.0.1'
    port = 2680
    soc = None

    def __init__(self):
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.soc.connect((self.host, self.port))

    def get_file(self, file_name):
        """
        download a file from the server
        """
        print('* Downloading file from the server:')

        recv_buffer = ut.recvall(self.soc, ut.data_unit)
        file_len = int(ut.decode_str(recv_buffer))            # receive1: file length
        print('Length of the file:', str(file_len))
        sys.stdout.flush()

        received_size = 0
        local_file = open(file_name, 'wb')
        while file_len != received_size:
            received_data = self.soc.recv(ut.data_unit)       # receive2: file
            local_file.write(received_data)
            received_size += len(received_data)
        local_file.close()
        print('Downloading finished!\n')
        sys.stdout.flush()
        self.soc.close()


if __name__ == '__main__':
    start = time.time()
    file_name = sys.argv[1]
    print('Download file as:', file_name)
    sys.stdout.flush()
    client = Client()
    client.get_file(file_name)
    print('* Running time:', time.time() - start)
    sys.stdout.flush()
