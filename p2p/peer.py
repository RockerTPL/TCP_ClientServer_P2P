import socket
from threading import Thread
import sys
import utils as ut
import os
import time


class Peer:
    server_ip = None        # ip of server
    server_port = None      # port of server
    soc = None              # socket for receiving a block
    idx_clt = None          # index of client
    num_peer = None         # number of peers
    info_pool = []          # information of all peers

    downfile_name = None    # name of download file
    downfile_folder = None  # folder of download file
    file_len = None         # length of download file
    block_name = None       # name of block
    block_len = None        # length of block

    p_ip = None             # ip of peer
    p_port = None           # port of peer
    p_svr = None            # server socket of peer
    has_received = []       # whether all blocks are received

    def __init__(self, server_ip, server_port, ip, port, downfile_name):
        self.server_ip = server_ip
        self.server_port = server_port
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.soc.connect((self.server_ip, self.server_port))
        self.downfile_name = downfile_name
        file_paths = downfile_name.split('/')
        self.downfile_folder = downfile_name[:-len(file_paths[-1]) - 1]
        self.p_ip = ip
        self.p_port = port

    def get_block(self):
        """
        download a file block from the server
        """
        print('* Getting a block from the server:')
        self.soc.send(ut.encode_str(str(self.p_port), ut.data_unit))  # send1-1: port of client

        recv_buffer = ut.recvall(self.soc, ut.data_unit)
        self.idx_clt = int(ut.decode_str(recv_buffer))                # receive1-2: index of client
        print('Index of current peer:', self.idx_clt)

        recv_buffer = ut.recvall(self.soc, ut.data_unit)
        self.num_peer = int(ut.decode_str(recv_buffer))               # receive1-3: number of peers
        print('Number of peers:', self.num_peer)

        self.info_pool = [None] * self.num_peer
        recv_buffer = ut.recvall(self.soc, ut.data_unit)              # receive1-4: information of all peers
        info_clts = ut.decode_str(recv_buffer).split('|')
        for i in range(self.num_peer):
            info_clt = info_clts[i].split(';')    # (ip, port)
            self.info_pool[i] = (info_clt[0], int(info_clt[1]))
        print('Information of peers:', self.info_pool)

        recv_buffer = ut.recvall(self.soc, ut.data_unit)
        self.file_len = int(ut.decode_str(recv_buffer))               # receive1-5: file length
        print('Length of the file:', self.file_len)

        self.block_name = self.downfile_folder + '/' + str(self.idx_clt)
        print('Name of the block:', self.block_name)

        recv_buffer = ut.recvall(self.soc, ut.data_unit)
        self.block_len = int(ut.decode_str(recv_buffer))              # receive1-6: block length
        print('Length of the block:', self.block_len)
        sys.stdout.flush()

        # receive a block of file
        received_size = 0
        local_file = open(self.block_name, 'wb')
        while received_size != self.block_len:
            received_data = self.soc.recv(ut.data_unit)               # receive1-7: file block
            # print('received:', len(received_data))
            local_file.write(received_data)
            received_size += len(received_data)
        local_file.close()
        print('Downloading of block finished!\n')
        sys.stdout.flush()
        self.has_received = [False] * self.num_peer
        self.has_received[self.idx_clt] = True

    def start_p_server(self):
        """
        current peer as server of others
        """
        self.p_svr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.p_svr.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.p_svr.bind((self.p_ip, self.p_port))
        self.p_svr.listen(12)
        print('* Peer started, waiting for other peers to connect...')
        sys.stdout.flush()
        while True:
            clt, addr = self.p_svr.accept()
            print('Got connection from', addr)
            send_thread = Thread(target=self.send_block, args=(clt,))
            send_thread.setDaemon(True)
            send_thread.start()
            sys.stdout.flush()

    def send_block(self, clt):
        """
        send file block to other peers
        """
        clt.send(ut.encode_str(str(self.block_len), ut.data_unit))  # send2-1: block length

        # send the block of file
        data_block = open(self.block_name, 'rb')
        send_size = 0
        data_block.seek(0)
        while send_size != self.block_len:
            data_trans = data_block.read(ut.data_unit)
            clt.send(data_trans)                                    # send2-2: file block
            send_size += len(data_trans)
        print('Transmission of block %d to another peer completed!\n' % self.idx_clt)
        sys.stdout.flush()
        data_block.close()
        clt.close()

    def start_p_client(self):
        """
        current peer as client of others
        """
        print('* Asking other peers for blocks...')
        sys.stdout.flush()
        for idx in range(self.num_peer):
            if idx != self.idx_clt:
                print('Asking peer at index %d for a block' % idx)
                sys.stdout.flush()
                require_block_thread = Thread(target=self.get_other_block, args=(idx,))
                require_block_thread.setDaemon(True)
                require_block_thread.start()

    def get_other_block(self, idx):
        """
        require a block from another peer
        """
        p_server_ip = self.info_pool[idx][0]
        p_server_port = self.info_pool[idx][1]
        p_clt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        p_clt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        p_clt.connect((p_server_ip, p_server_port))
        recv_buffer = ut.recvall(p_clt, ut.data_unit)
        p_block_len = int(ut.decode_str(recv_buffer))       # receive2-1: block length
        received_size = 0
        local_file = open(self.downfile_folder+'/'+str(idx), 'wb')
        while received_size != p_block_len:
            received_data = p_clt.recv(ut.data_unit)        # receive2-2: file block
            local_file.write(received_data)
            received_size += len(received_data)
        local_file.close()
        print('Downloading of block %d finished!\n' % idx)
        sys.stdout.flush()
        p_clt.close()
        self.has_received[idx] = True

    def comb_blocks(self):
        """
        combine all blocks to get the file
        """
        while True:
            if False not in self.has_received:
                print('* Combining the blocks to get the file')
                sys.stdout.flush()
                os.system('touch %s' % self.downfile_name)
                os.system('cat /dev/null > %s' % self.downfile_name)
                for i in range(self.num_peer):
                    block_name = self.downfile_folder + '/' + str(i)
                    os.system('cat %s >> %s' % (block_name, self.downfile_name))
                    os.system('rm %s' % block_name)
                return


if __name__ == '__main__':
    start = time.time()
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    downfile_name = sys.argv[3]
    p_ip = sys.argv[4]
    p_port = int(sys.argv[5])
    print('Download file as:', downfile_name, '\nPeer ip:', p_ip, '\nPeer port:', p_port, '\n')
    sys.stdout.flush()

    peer = Peer(server_ip, server_port, p_ip, p_port, downfile_name)

    # thread for peer as server of others
    server_thread = Thread(target=peer.start_p_server)
    server_thread.setDaemon(True)
    server_thread.start()

    # download a block o file from server
    peer.get_block()

    # thread for peer as client of others
    client_thread = Thread(target=peer.start_p_client)
    client_thread.setDaemon(True)
    client_thread.start()

    # combine all blocks to get the file
    peer.comb_blocks()
    print('* Run time:', time.time() - start)
    sys.stdout.flush()

    server_thread.join()
    server_thread.join()
