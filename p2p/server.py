import socket
from threading import Thread
import sys
import math
import utils as ut


class Server:
    host = '0.0.0.0'
    port = 2680
    svr = None       # server socket
    clt_pool = []    # connected clients
    info_pool = []   # information of clients: (ip, port)
    num_peer = None  # expected number of peers

    def __init__(self, num_peer):
        """
        initialization of server
        """
        self.num_peer = num_peer
        self.info_pool = [None]*self.num_peer
        self.svr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.svr.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.svr.bind((self.host, self.port))
        self.svr.listen(12)
        print('Server started, waiting for client to connect...')
        sys.stdout.flush()

    def accept_client(self, file_name):
        """
        accept new connections
        """
        while True:
            clt, addr = self.svr.accept()
            idx_clt = len(self.clt_pool)  # index of this client
            self.clt_pool.append(clt)
            print('Got connection from (%s, %d) at index %d' % (addr[0], addr[1], idx_clt))
            sys.stdout.flush()
            send_thread = Thread(target=self.send_file, args=(clt, addr, idx_clt, file_name))
            send_thread.setDaemon(True)
            send_thread.start()

    def send_file(self, clt, addr, idx_clt, file_name):
        """
        send blocks of files
        """
        recv_buffer = ut.recvall(clt, ut.data_unit)                          # receive1-1: port of client
        clt_port = int(ut.decode_str(recv_buffer))
        self.info_pool[idx_clt] = (addr[0], clt_port)
        while True:
            if len(self.clt_pool) == self.num_peer and None not in self.info_pool:
                clt.send(ut.encode_str(str(idx_clt), ut.data_unit))          # send1-2: index of client
                clt.send(ut.encode_str(str(self.num_peer), ut.data_unit))    # send1-3: number of peers

                all_clt_info = ''
                for i in range(self.num_peer):
                    ip_i = self.info_pool[i][0]
                    port_i = self.info_pool[i][1]
                    all_clt_info = all_clt_info + ip_i + ';' + str(port_i) + '|'
                all_clt_info = all_clt_info[:-1]
                clt.send(ut.encode_str(all_clt_info, ut.data_unit))          # send1-4: information of all clients

                data_file = open(file_name, 'rb')
                file_len = len(data_file.read())
                clt.send(ut.encode_str(str(file_len), ut.data_unit))         # send1-5: file length

                if idx_clt == len(self.clt_pool) - 1:
                    block_len = file_len - math.ceil(file_len/self.num_peer) * idx_clt
                else:
                    block_len = math.ceil(file_len/self.num_peer)
                clt.send(ut.encode_str(str(block_len), ut.data_unit))        # send1-6: block length

                # send a block of file
                send_size = 0
                data_file.seek(idx_clt * math.ceil(file_len/self.num_peer), 0)
                while send_size != block_len:
                    if send_size + ut.data_unit <= block_len:
                        data_trans = data_file.read(ut.data_unit)
                        clt.send(data_trans)                                 # send1-7: file block
                        send_size += len(data_trans)
                        # print('send size', send_size)
                        # print('Transmission progress: %d:%d' % (send_size, block_len))
                    else:
                        data_trans = data_file.read(block_len - send_size)
                        clt.send(data_trans)                                 # send1-7: file block
                        send_size += len(data_trans)
                        # print('send size', send_size)
                        # print('Transmission progress: %d:%d' % (send_size, block_len))
                print('Transmission of block %d completed!\n' % idx_clt)
                sys.stdout.flush()
                data_file.close()
                clt.close()
                return


if __name__ == '__main__':
    file_name = sys.argv[1]
    num_peer = int(sys.argv[2])
    print(file_name, num_peer)
    sys.stdout.flush()
    server = Server(num_peer)
    server.accept_client(file_name)
    server.svr.close()
