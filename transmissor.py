import numpy as np
import socket
import pickle
from mod_8qam import Mod_8qam


class Transmissor:
    def __init__(self, received_text: str, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.received_text = received_text
        self.bit_array = self.__text_2_binary(received_text)


    def __text_2_binary(self, text):
        """ Converts text to binary """
        bits_str = ''
        for byte in text.encode('utf8'):
            byte = f'{byte:08b}' # convert byte to a byte string 
            bits_str += byte
        return [int(bit) for bit in bits_str] # returns a list of bits
    



# Run methods start ---------------------------------------------------------------------------------------------------------------------

    def run(self, encoding_method, framing_method, error_correction_or_detection_method,  modulation_method):
        self.encoded_bits = self.coder(encoding_method)

        

        match encoding_method.lower():
            case "nrz":	# -1 -> 0; 1 -> 1
                self.encoded_bits_cleaned = [0 if bits != 1 else 1 for bits in self.encoded_bits]
            case "bipolar":	# 0 -> 0; (-1,1) -> 1
                self.encoded_bits_cleaned = [0 if (bits == 0) else 1 for bits in self.encoded_bits]
            case "manchester":	# 0 -> 0; 1 -> 1
                self.encoded_bits_cleaned = self.encoded_bits



        match framing_method.lower():
            case "character_count":
                self.frames = self.character_count_framing(self.encoded_bits_cleaned, 8)
            case "byte_insertion":
                self.frames = self.bytes_insertion_framing(self.encoded_bits_cleaned, 8)
            case "bits_insertion":
                self.frames = self.bits_insertion_framing(self.encoded_bits_cleaned, 64) # 64 bits (8 bytes) per frame

        
        match error_correction_or_detection_method.lower():
            case "even_parity":
                self.frames_final = self.adjust_frames_even_parity(self.frames, framing_method)
            case "crc":
                self.frames_final = self.adjust_frames_crc(self.frames, framing_method)
            case "hamming":
                self.frames_final = self.adjust_frames_hamming(self.frames, framing_method)

        print(self.frames_final)
        bits_vector = [bit for frame in self.frames_final for bit in frame] # convert the frames matrix to a big bit vector
        match modulation_method.lower():
            case "ask":
                self.signal = self.ASK(1, 1, bits_vector)
            case "fsk":
                self.signal = self.FSK(1, 1, 2, bits_vector)
            case "8qam":
                self.signal = self.modulacao_8qam(bits_vector)
        

        bits_vector_str = ''.join(map(str, bits_vector))

        self.send_message(bits_vector_str)

        return self.bit_array, self.encoded_bits, self.signal

# Run methods end ---------------------------------------------------------------------------------------------------------------------





# Adjust frames methods start ---------------------------------------------------------------------------------------------------------------------

    def adjust_frames_even_parity(self, frames, framing_method):
        """ Add even parity bit to each frame """
        match framing_method.lower():
            case "character_count":
                new_frames = []
                for frame in frames:
                    unified_frame_array = [int(bit) for bit in ''.join(frame[1:])] # convert the frame to a bit array
                    frame_with_parity = self.add_even_parity_bit(unified_frame_array) # add parity bit to the frame

                    remainder = len(frame_with_parity) % 8 # calculate the remainder of the division by 8
                    padding_needed = 8 - remainder # calculate the number of padding bits needed to make the frame size a multiple of 8
                    padding_bits = padding_needed % 8 # if the remainder is 0 or 8, no padding is needed

                    padded_frame = frame_with_parity + [0] * padding_bits

                    padding_header = [int(bit) for bit in f"{padding_bits:08b}"] # creates a header to indicate how many padding bits were added

                    byte_count = len(padded_frame) // 8 # calculate the number of bytes in the frame
                    frame_header = [int(bit) for bit in f"{byte_count+2:08b}"] # update the byte count header

                    new_frame = frame_header + padding_header + padded_frame # remove the first byte (byte count header) and combine everything in a new frame
                    new_frames.append(new_frame)

                return new_frames # returns a list of a frame list of int(bits)
            

            case "byte_insertion":
                new_frames = []

                for frame in frames:
                    flag_init = [int(bit) for bit in frame[0]]
                    flag_end = [int(bit) for bit in frame[-1]]

                    unified_frame_array = [int(bit) for bit in ''.join(frame[1:-1])]
                    frame_with_parity = self.add_even_parity_bit(unified_frame_array)

                    remainder = len(frame_with_parity) % 8
                    padding_needed = 8 - remainder
                    padding_bits = padding_needed % 8

                    padded_frame = frame_with_parity + [0] * padding_bits

                    padding_header = [int(bit) for bit in f"{padding_bits:08b}"]

                    new_frame = flag_init + padding_header + padded_frame + flag_end
                    new_frames.append(new_frame)

                return new_frames # returns a list of a frame list of int(bits)
            

            case "bits_insertion":
                new_frames = []

                for frame in frames:
                    flag_init = [int(bit) for bit in frame[:8]]
                    flag_end = [int(bit) for bit in frame[-8:]]

                    unified_frame_array = [int(bit) for bit in ''.join(frame[8:-8])]
                    frame_with_parity = self.add_even_parity_bit(unified_frame_array)

                    new_frame = flag_init + frame_with_parity  + flag_end
                    new_frames.append(new_frame)
                
                return new_frames # returns a list of a frame list of int(bits)



    def adjust_frames_crc(self, frames, framing_method):

        match framing_method.lower():
            case "character_count":
                new_frames = []
                for frame in frames:
                    unified_frame_array = [int(bit) for bit in ''.join(frame[1:])]
                    frame_with_crc, inserted_bits_len = self.crc32(unified_frame_array)

                padding_header = [int(bit) for bit in f"{inserted_bits_len:08b}"] # creates a header to indicate how many padding bits were added

                byte_count = len(frame_with_crc) // 8 # calculate the number of bytes in the frame
                frame_header = [int(bit) for bit in f"{byte_count+2:08b}"] # update the byte count header, +1 to count the header

                new_frame = frame_header + padding_header + frame_with_crc # remove the first byte (byte count header) and combine everything in a new frame
                new_frames.append(new_frame)

                return new_frames # returns a list of a frame list of int(bits)
            

            case "byte_insertion":
                new_frames = []

                for frame in frames:
                    flag_init = [int(bit) for bit in frame[0]]
                    flag_end = [int(bit) for bit in frame[-1]]

                    unified_frame_array = [int(bit) for bit in ''.join(frame[1:-1])]
                    frame_with_crc, inserted_bits_len = self.crc32(unified_frame_array)

                    padding_header = [int(bit) for bit in f"{inserted_bits_len:08b}"]

                    new_frame = flag_init + padding_header + frame_with_crc + flag_end
                    new_frames.append(new_frame)

                return new_frames # returns a list of a frame list of int(bits)
            

            case "bits_insertion":
                new_frames = []

                for frame in frames:
                    flag_init = [int(bit) for bit in frame[:8]]
                    flag_end = [int(bit) for bit in frame[-8:]]

                    unified_frame_array = [int(bit) for bit in ''.join(frame[8:-8])]
                    frame_with_crc, inserted_bits_len = self.crc32(unified_frame_array)

                    padding_header = [int(bit) for bit in f"{inserted_bits_len:08b}"]

                    new_frame = flag_init + padding_header + frame_with_crc + flag_end
                    new_frames.append(new_frame)

                return new_frames # returns a list of a frame list of int(bits)
            


    def adjust_frames_hamming(self, frames, framing_method):

        match framing_method.lower():
            case "character_count":
                new_frames = []
                for frame in frames:
                    unified_frame_array = [int(bit) for bit in ''.join(frame[1:])]
                    frame_with_hamming = self.apply_hamming_code(unified_frame_array)

                    remainder = len(frame_with_hamming) % 8
                    padding_needed = 8 - remainder
                    padding_bits = padding_needed % 8

                    padded_frame = frame_with_hamming + [0] * padding_bits

                    padding_header = [int(bit) for bit in f"{padding_bits:08b}"] # creates a header to indicate how many padding bits were added

                    byte_count = len(padded_frame) // 8 # calculate the number of bytes in the frame
                    frame_header = [int(bit) for bit in f"{byte_count+2:08b}"] # update the byte count header

                    new_frame = frame_header + padding_header + padded_frame # remove the first byte (byte count header) and combine everything in a new frame
                    new_frames.append(new_frame)

                return new_frames # returns a list of a frame list of int(bits)
            

            case "byte_insertion":
                new_frames = []

                for frame in frames:
                    flag_init = [int(bit) for bit in frame[0]]
                    flag_end = [int(bit) for bit in frame[-1]]

                    unified_frame_array = [int(bit) for bit in ''.join(frame[1:-1])]
                    frame_with_hamming = self.apply_hamming_code(unified_frame_array)

                    remainder = len(frame_with_hamming) % 8
                    padding_needed = 8 - remainder
                    padding_bits = padding_needed % 8

                    padded_frame = frame_with_hamming + [0] * padding_bits

                    new_frame = flag_init + padded_frame + flag_end
                    new_frames.append(new_frame)

                return new_frames # returns a list of a frame list of int(bits)
            

            case "bits_insertion":
                new_frames = []

                for frame in frames:
                    flag_init = [int(bit) for bit in frame[:8]]
                    flag_end = [int(bit) for bit in frame[-8:]]

                    unified_frame_array = [int(bit) for bit in ''.join(frame[8:-8])]
                    frame_with_hamming = self.apply_hamming_code(unified_frame_array)

                    new_frame = flag_init + frame_with_hamming + flag_end
                    new_frames.append(new_frame)

                return new_frames # returns a list of a frame list of int(bits)

# Adjust frames methods end ---------------------------------------------------------------------------------------------------------------------



# Enconding methods start ---------------------------------------------------------------------------------------------------------------------

    def coder(self, encoding_method):
        match encoding_method.lower():
            case "nrz":
                return self.polar_nrz_coder(self.bit_array)
            case "manchester":
                print("bits_cleanded transmissor", self.bit_array)
                print()
                print()
                return self.manchester_coder(self.bit_array)
            case "bipolar":
                return self.bipolar_coder(self.bit_array)
        

    def polar_nrz_coder(self, bit_array):
        output = [bit if bit == 1 else -1 for bit in bit_array]
        return output

    
    def manchester_coder(self, bit_array): 
        output = [[0, 1] if bit == 0 else [1, 0] for bit in bit_array]
        output = [bit for two_bit_list in output for bit in two_bit_list]
        return output
    

    def bipolar_coder(self, bit_array):
        output = bit_array.copy()
        flip = False
        for i, bit in enumerate(output):
            if bit == 1 and not flip:
                output[i] = 1
                flip = not flip
            elif bit == 1 and flip:
                output[i] = -1
                flip = not flip
        return output

# Enconding methods end ---------------------------------------------------------------------------------------------------------------------
    


# Framing methods start ---------------------------------------------------------------------------------------------------------------------

    def character_count_framing(self, bits_array, max_frame_size): # limit of max_frame_size is 256
        """Return a matrix of frames, each frame is a list of strings of 8 bits"""
        frames_matrix = []
        bytes_list = [''.join(map(str, bits_array[i:i+8])) for i in range(0, len(bits_array), 8)] # bytes list is a array of strings of 8 bits

        while bytes_list:
            frame_size = min(len(bytes_list), max_frame_size - 1) 
            frame = [f"{frame_size+1:08b}"] + bytes_list[:frame_size] # +1 for the header, because the header matter in the frame size
            frames_matrix.append(frame)
            bytes_list = bytes_list[frame_size:]

        return frames_matrix
    

    def bytes_insertion_framing(self, bits_array, max_frame_size): # max_frame_size is the number of ****bytes**** in a frame
        """Return a matrix of frames, each frame is a list of strings of 8 bits"""
        frames_matrix = []
        bytes_list = [''.join(map(str, bits_array[i:i+8])) for i in range(0, len(bits_array), 8)] # Bytes list is a array of strings of 8 bits
        byte_flag = "01111110"

        while bytes_list:
            frame_size = min(len(bytes_list), max_frame_size-2)  # -2 for the flags
            frame = [byte_flag] + bytes_list[:frame_size] + [byte_flag]
            frames_matrix.append(frame)
            bytes_list = bytes_list[frame_size:]
            
        return frames_matrix 
    

    def bits_insertion_framing(self, bits_array, max_frame_size): # max_frame_size is the number of ****bits**** in a frame
        """Return a list of frames, each frame is a string of bits"""
        frames_list = []
        flag = "01111110"

        for i in range(0, len(bits_array), max_frame_size):
            frame = ''.join(map(str, bits_array[i:i+max_frame_size]))
            frames_list.append(flag + frame + flag)

        return frames_list
    

# Framing methods end ---------------------------------------------------------------------------------------------------------------------
    



# Error correction or detection methods start ---------------------------------------------------------------------------------------------------------------------

    def add_even_parity_bit(self, bits_array):
        count_ones = sum(bits_array)
        parity_bit = 0

        if count_ones % 2 != 0:
            parity_bit = 1

        return bits_array + [parity_bit]
    


    def crc32(self, bit_array):
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

        def gen_0_1_sequence(len_array): # generate a sequence of 0's and 1's
            array = []
            for i in range(len_array):
                if i % 2 == 0: # if the index is even, the bit is 0
                    array.append(0)
                else: # if the index is odd, the bit is 1
                    array.append(1)
            return array

        if len(bit_array) < 64: # if the bit array is less than 64 bits, complete with 0's and 1's (to avoid large sequences of 0's)
            inserted_int_bits = gen_0_1_sequence(64 - len(bit_array)) # 0's and 1's to complete the 64 bits
            bit_array = bit_array + inserted_int_bits
            inserted_bits_len = len(inserted_int_bits)

        bit_str = ''.join(map(str, bit_array)) # convert the bit array to a bit string
        bit_str_initial = bit_str

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

        return list(bit_str_initial + bit_str_to_xor), inserted_bits_len



    def apply_hamming_code(self, bit_array): # Apply the Hamming Code to the provided bit array.
        def find_len_redundant_bits(len_bits): 
            """Find the number of redundant bits required for a message of length len_bits."""
            for i in range(len_bits):
                if(2**i >= len_bits + i + 1):
                    return i			
                
        def insert_zeros_parity_position(bit_array): 
            """Insert zeros in the parity positions."""
            len_redudant_bits = find_len_redundant_bits(len(bit_array))

            for i in range(len_redudant_bits):
                bit_array.insert((2**i)-1, 0)

            return bit_array		

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

            parity = list_of_bits[1] # The first bit is the parity bit itself
            list_of_bits = list_of_bits[2:] # Remove the first bit because it is the 0 that was included

            for bit in list_of_bits:
                parity ^= bit

            return parity				

        def insert_parity_bits(bit_array):
            """Return the bit array with the parity bits."""
            len_redudant_bits = find_len_redundant_bits(len(bit_array))
            bit_array = insert_zeros_parity_position(bit_array)

            for i in range(len_redudant_bits):
                position = (2**i)
                bit_array[position-1] = calculate_parity_bit(bit_array, position) # position-1 because the list starts with index 0

            return bit_array
        
        return insert_parity_bits(bit_array)

# Error correction or detection methods end ---------------------------------------------------------------------------------------------------------------------



# Modulation methods start ---------------------------------------------------------------------------------------------------------------------

    def ASK(self, A, f, bit_array):
        tam_sinal = len(bit_array)
        sinal = np.zeros(tam_sinal*100, dtype=float)

        for i in range(tam_sinal):
            if self.bits_codificados_binario[i] == 1:
                for j in range(100):
                    sinal[i*100 + j] = A * np.sin(2*np.pi*f*j/100)
            else:
                for j in range(100):
                    sinal[i*100 + j] = 0

        return sinal

    
    def FSK(self, A, f1, f2, bit_array):
        """ Modular a frequência do sinal """
        tam_sinal = len(bit_array)
        sinal = np.zeros(tam_sinal*100, dtype=float)

        for i in range(tam_sinal):
            if bit_array[i] == 1:
                for j in range(100):
                    sinal[i*100 + j] = A * np.sin(2*np.pi*f1*j/100)
            else:
                for j in range(100):
                    sinal[i*100 + j] = A * np.sin(2*np.pi*f2*j/100)

        return sinal




    def ASK(self, A, f, bit_array): # Amplitude Shift Keying
        len_signal = len(bit_array)
        signal = np.zeros(len_signal*100, dtype=float)

        for i in range(len_signal):
            if bit_array[i] == 1:
                for j in range(100):
                    signal[i*100 + j] = A * np.sin(2*np.pi*f*j/100)
            else:
                for j in range(100):
                    signal[i*100 + j] = 0

        return signal


    def FSK(self, A, f1, f2, bit_array): # Frequency Shift Keying
        len_signal = len(bit_array)
        signal = np.zeros(len_signal*100, dtype=float)

        for i in range(len_signal):
            if bit_array[i] == 1:
                for j in range(100):
                    signal[i*100 + j] = A * np.sin(2*np.pi*f1*j/100)
            else:
                for j in range(100):
                    signal[i*100 + j] = A * np.sin(2*np.pi*f2*j/100)

        return signal

    def modulacao_8qam(self, bits):
        mod_8qam = Mod_8qam()
        bauds, tempo, sinal_banda_base = mod_8qam.run(bits)
        return [bauds, tempo, sinal_banda_base]

# Modulation methods end ---------------------------------------------------------------------------------------------------------------------

    # Send digitally encoded message to receiver through socket
    def send_message(self, bits_vector_str):

        socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_client.connect((self.host, self.port))

        dados = pickle.dumps(bits_vector_str)
        socket_client.send(dados)

        received_data = socket_client.recv(4096)

        socket_client.close()

        return received_data


if __name__ == "__main__":
    transmissor = Transmissor("yan")
    result = transmissor.run("manchester", "bits_insertion", "even_parity", "ask")

    print(result)