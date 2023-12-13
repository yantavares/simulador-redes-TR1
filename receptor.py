import socket
import pickle
from transmissor import Transmissor
from threading import Thread


class Receiver:
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.running = True
        self.bits_array = []
        self.server_thread: Thread

    def __binary_2_text(self, bits):
        """ Converts binary to text """
        bits_str = ''.join(map(str, bits))  # convert list of bits to a string of bits
        bytes_list = [bits_str[i:i+8] for i in range(0, len(bits_str), 8)]  # divide the string of bits into bytes
        bytes_list = [int(byte, 2) for byte in bytes_list]  # convert bytes to integers
        bytes_array = bytearray(bytes_list)  # convert list of integers to bytearray
        text = bytes_array.decode('utf8')  # decode bytearray to string
        return text

    def start_server(self):
        self.server_thread = Thread(target=self._start_server)
        self.server_thread.daemon = True
        self.server_thread.start()

    def _start_server(self):
        socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_servidor.bind((self.host, self.port))
        socket_servidor.listen(1)
        print("Listening on port 65432")
        while True and self.running:
            conexao_socket, end = socket_servidor.accept()
            print(end, 'Connected!')

            dados = conexao_socket.recv(4096)  # receber ate 1024 bytes
            dados_list = pickle.loads(dados)
            self.bits_array = dados_list

            conexao_socket.send(pickle.dumps(self.bits_array))

            conexao_socket.close()


# Run methods start ---------------------------------------------------------------------------------------------------------------------

    def run(self, encoding_method, framing_method, error_correction_or_detection_method):

        match framing_method.lower():
            case "character_count":
                self.frames, self.padding_bits_list = self.character_count_deframing(self.bits_array)
            case "byte_insertion":
                self.frames, self.padding_bits_list  = self.bytes_insertion_deframing(self.bits_array)
            case "bits_insertion":
                if error_correction_or_detection_method == "crc":
                    self.frames, self.padding_bits_list  = self.bits_insertion_deframing(self.bits_array, crc32=True)
                else:
                    self.frames, self.padding_bits_list  = self.bits_insertion_deframing(self.bits_array, crc32=False)

        match error_correction_or_detection_method.lower():
            case "even_parity":
                self.bits_cleaned, self.list_error_detec = self.solve_even_parity(self.frames, self.padding_bits_list)
            case "crc":
                self.bits_cleaned, self.list_error_detec = self.solve_crc32(self.frames, self.padding_bits_list)
            case "hamming":
                self.bits_cleaned, self.list_error_detec = self.solve_hamming(self.frames, self.padding_bits_list)


        match encoding_method.lower():
            case "nrz":	# -1 -> 0; 1 -> 1
                pass
            case "bipolar":	# 0 -> 0; (-1,1) -> 1
                pass
            case "manchester":	# 0 -> 0; 1 -> 1
                bit_pairs = [self.bits_cleaned[i:i+2] for i in range(0, len(self.bits_cleaned), 2)]
                self.bits_cleaned = [0 if pair == [0, 1] else 1 for pair in bit_pairs]
                
        
        final_str = self.__binary_2_text(self.bits_cleaned)

        bits_cleaned_str = ''.join(map(str, self.bits_cleaned))

        return self.bits_array, bits_cleaned_str, final_str

# Run methods end ---------------------------------------------------------------------------------------------------------------------



# Framing methods start ---------------------------------------------------------------------------------------------------------------------

    def character_count_deframing(self, bits_array):
        """Return a matrix of frames without headers"""
        original_frames_matrix = []
        padding_bits_list = []
        bytes_list = [''.join(map(str, bits_array[i:i+8])) for i in range(0, len(bits_array), 8)] # bytes_list is a array of strings of 8 bits

        while bytes_list:
            # Convert the header to integer
            frame_size = int(bytes_list[0], 2)

            padding_bits = int(bytes_list[1], 2)
            # Remove the header and add the frame to the matrix
            original_frames_matrix.append(bytes_list[2:frame_size])
            padding_bits_list.append(padding_bits)
            # Move to the next frame
            bytes_list = bytes_list[frame_size:]

        list_str_frames = [''.join(frame) for frame in original_frames_matrix]

        return list_str_frames, padding_bits_list
    

    def bytes_insertion_deframing(self, bits_array):
        """Return a matrix of frames without flags"""
        original_frames_matrix = []
        frame = []
        padding_bits_list = []
        bytes_list = [''.join(map(str, bits_array[i:i+8])) for i in range(0, len(bits_array), 8)] # bytes_list is a array of strings of 8 bits
        flag = '01111110'

        while bytes_list:
            byte = bytes_list.pop(0)
            if byte == flag:
                if frame:  # if frame is not empty
                    original_frames_matrix.append(frame[1:])
                    padding_bits = int(frame[0], 2)
                    padding_bits_list.append(padding_bits)
                    frame = []
            else:
                frame.append(byte)

        list_str_frames = [''.join(frame) for frame in original_frames_matrix]

        return list_str_frames, padding_bits_list

    
    def bits_insertion_deframing(self, bits_array, crc32=False): 
        """Return a list of frames(str) without flags"""
        original_frames_list = []
        frame = []
        padding_bits_list = []
        bits_string = ''.join(map(str, bits_array)) # bits_string is a string of bits
        flag = '01111110'

        while bits_string:
            if bits_string.startswith(flag):
                bits_string = bits_string[len(flag):]  # remove the flag
                if crc32 and not frame:
                    padding_bits = int(bits_string[:8], 2)
                    bits_string = bits_string[8:]
                    padding_bits_list.append(padding_bits)
                elif not crc32 and not frame:
                    padding_bits_list.append(0)

                if frame:  # if frame is not empty
                    original_frames_list.append("".join(frame))
                    frame = []
            else:
                frame.append(bits_string[0])
                bits_string = bits_string[1:]

        return original_frames_list, padding_bits_list

# Framing methods end ---------------------------------------------------------------------------------------------------------------------
    



# Error correction or detection methods start ---------------------------------------------------------------------------------------------------------------------
    
    def solve_even_parity(self, frames, padding_bits_list):
        list_detection_error = []
        list_bits_cleaned = []

        for frame, padding_bits in zip(frames, padding_bits_list):
            if padding_bits != 0:
                frame = frame[:-padding_bits] # remove the padding bits

            bits_array = [int(bit) for bit in frame] # convert the frame to a list of integers
            count_ones = sum(bits_array[:-1])
            parity_bit = bits_array[-1]

            if (count_ones + parity_bit) % 2 == 0:
                list_detection_error.append(False)
            else:
                list_detection_error.append(True)	

            list_bits_cleaned.extend(bits_array[:-1])		

        return list_bits_cleaned, list_detection_error



    def solve_crc32(self, frames, padding_bits_list):
        def verify_crc32(bit_array):
            inserted_bits_len = 0
            crc32_polynomial = 0x104C11DB7 # polynomial used by CRC32 IEEE 802 (0x04C11DB7 without the occlusion of the first bit)
            crc32_polynomial_str = f"{crc32_polynomial:033b}" # 32 0's to complete the 96 bits

            def xor(bit_str_a, bit_str_b): # xor between two bit strings
                bit_str_result = ''
                for i in range(len(bit_str_a)):
                    if bit_str_a[i] == bit_str_b[i]: # if the bits are equal, the result is 0
                        bit_str_result += '0'
                    else: # if the bits are different, the result is 1
                        bit_str_result += '1'
                return bit_str_result

            bit_str = ''.join(map(str, bit_array)) # convert the bit array to a bit string

            bit_str = bit_str + '0'*32 # 32 0's to complete the 96 bits     
            bit_str_to_xor = ''
            for i in range(len(bit_str)): # for each bit in the bit string
                if i <= 32: # if the bit is in the first 32 bits
                    bit_str_to_xor += bit_str[i]
                else: # if the bit is in the last 64 bits
                    if bit_str_to_xor[0] == '1':
                        bit_str_to_xor = xor(bit_str_to_xor, crc32_polynomial_str) # xor with the polynomial
                        bit_str_to_xor = bit_str_to_xor[1:] + bit_str[i] # exclude the first bit (0) and include the next bit
                    else:
                        bit_str_to_xor = bit_str_to_xor[1:] + bit_str[i] # exclude the first bit (0) and include the next bit

                if i == len(bit_str) - 1: # if it is the last bit
                    if bit_str_to_xor[0] == '1': # if the first bit is 1, xor with the polynomial
                        bit_str_to_xor = xor(bit_str_to_xor, crc32_polynomial_str)
                        bit_str_to_xor = bit_str_to_xor[1:] # exclude the first bit (0)

                    else: # if the first bit is 0, xor with 33 0's
                        bit_str_to_xor = bit_str_to_xor[1:] # exclude the first bit (0)

            if bit_str_to_xor == '0'*32: # if the result is 32 0's, don't have errors
                return True
            else: # if the result is not 32 0's, have errors
                return False

        list_detection_error = []
        list_bits_cleaned = []
        for frame, padding_bits in zip(frames, padding_bits_list):
            bits_array = [int(bit) for bit in frame] # convert the frame to a list of integers
            if verify_crc32(bits_array):
                list_detection_error.append(False)
            else:
                list_detection_error.append(True)
            
            if padding_bits != 0:
                list_bits_cleaned.extend(bits_array[:-padding_bits-32]) # remove the padding bits
            else:
                list_bits_cleaned.extend(bits_array[:-32]) 

        return list_bits_cleaned, list_detection_error
    
    def solve_hamming(self, frames, padding_bits_list): # Apply the Hamming Code to the provided bit array.
        def find_len_redundant_bits(bit_array): 
            """"""
            len_bit_array = len(bit_array)
            i = 0
            while ((2**i) <= len_bit_array):
                i += 1
            return i

        def calculate_parity_bit(bit_array, position): # position must be one of the power of 2 (1, 2, 4, 8, 16, ...)
            """Calculate the parity bit for the given position."""
            temp_bit_array = bit_array[position-1:]
            list_of_bits = []
            jump = False # jump must be started with False to collect the first bits of the bit_array according to the position
            for i in range(0, len(bit_array), position):
                if jump:
                    jump = False
                    continue

                list_of_bits.extend(temp_bit_array[i:i+position]) # if i+position is greater than the length of the temp_bit_array, it will not be a problem because the slice will be until the end of the list
                jump = True        

            parity = list_of_bits[0] # The first bit is the parity bit itself
            list_of_bits = list_of_bits[1:] 

            for bit in list_of_bits:
                parity ^= bit

            return parity
                
        def make_correction(bit_array):
            """Make the correction of the bit array."""
            len_redudant_bits = find_len_redundant_bits(bit_array)
            error_position = 0
            str_bin_correction = ""

            for i in range(len_redudant_bits):
                position = (2**i)
                parity = calculate_parity_bit(bit_array, position)
                str_bin_correction += str(parity)

            str_bin_correction = str_bin_correction[::-1] # Reverse the string

            print("str_bin_correction",str_bin_correction)
            error_position = int(str_bin_correction, 2) # Convert the binary string to decimal

            if error_position == 0:
                print("No error detected")

            else:
                print(f"Error detected at position {error_position}")
                error_position -= 1  # Adjusting for 0-based index

                if bit_array[error_position] == 0:
                    bit_array[error_position] = 1
                else:
                    bit_array[error_position] = 0
            
            bit_array_corrected_cleaned = []
            for i in range(len(bit_array)):
                if (i+1) not in [2**i for i in range(len_redudant_bits)]:
                    bit_array_corrected_cleaned.append(bit_array[i])

            return bit_array_corrected_cleaned
        

        list_detection_error = []
        list_bits_cleaned = []
        for frame, padding_bits in zip(frames, padding_bits_list):
            if padding_bits != 0:
                frame = frame[:-padding_bits] # remove the padding bits

            bits_array = [int(bit) for bit in frame] # convert the frame to a list of integers
            bits_array_corrected = make_correction(bits_array)

            list_bits_cleaned.extend(bits_array_corrected)	
            

        return list_bits_cleaned, list_detection_error

# Error correction or detection methods end ---------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    transmissor = Transmissor("yan fahfa")
    result = transmissor.run("nrz", "bits_insertion", "hamming", "ask")[0]
    print("result", result)
    receiver = Receiver(result)
    print("string_recebida", receiver.run("nrz", "bits_insertion", "hamming"))



# [0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0]
# [0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0]


# [0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0]



# [0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1]