import matplotlib.pyplot as plt
import numpy as np


class Mod_8qam:
    def __init__(self):
        self.taxa_modulacao = 8
        self.taxa_transmissao = 24

    def modulacao_8qam(self, bits):
        while len(bits) % 3 != 0:
            bits = np.append(bits, 0)

        bits_simbolos = [tuple(bits[i:i + 3]) for i in range(0, len(bits), 3)]

        # Constelacao para o 8QAM
        mapa = {
            (0, 0, 0): complex(-1, -1),
            (0, 0, 1): complex(-1, 1),
            (0, 1, 0): complex(1, -1),
            (0, 1, 1): complex(1, 1),
            (1, 0, 0): complex(-1, -3),
            (1, 0, 1): complex(-1, 3),
            (1, 1, 0): complex(1, -3),
            (1, 1, 1): complex(1, 3)
        }

        simbolos_modulados = [mapa[bits] for bits in bits_simbolos]

        return simbolos_modulados

    def banda_base_8qam(self, simbolos_modulados):
        duracao_simbolo = 1 / self.taxa_modulacao

        num_simbolos = len(simbolos_modulados)
        tempo_simbolo = np.linspace(0, duracao_simbolo, 100)

        tempo_total = np.linspace(
            0, duracao_simbolo * num_simbolos, num_simbolos * 100)
        forma_onda = np.zeros(len(tempo_total), dtype=complex)

        for i, simbolo in enumerate(simbolos_modulados):
            forma_onda[i * 100: (i + 1) * 100] = simbolo * np.exp(1j *
                                                                  2 * np.pi * self.taxa_modulacao * tempo_simbolo)

        num_bauds = len(simbolos_modulados)
        baud_duracao = 1 / self.taxa_transmissao
        tempo_total = np.linspace(0, baud_duracao * num_bauds, num_bauds * 100)

        # cores = np.random.rand(num_bauds, 3)

        # plt.figure(figsize=(12, 6))

        # for i in range(num_bauds):
        #     plt.plot(tempo_total[i * 100: (i + 1) * 100],
        #              np.real(forma_onda[i * 100: (i + 1) * 100])
        #             )

        # plt.title('Sinais dos Bauds (8QAM) no Tempo')
        # plt.xlabel('Tempo')
        # plt.ylabel('Amplitude')
        # plt.legend()
        # plt.grid()
        # plt.tight_layout()
        # plt.show()

        return num_bauds, tempo_total, forma_onda

    def run(self, bits):
        simbolos_modulados = self.modulacao_8qam(bits)
        num_bauds, tempo, sinal_banda_base = self.banda_base_8qam(
            simbolos_modulados)

        return num_bauds, tempo, sinal_banda_base


if __name__ == '__main__':
    modulador = Mod_8qam()
    bits = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1,
            0, 1, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1]

    balds, tempo, sinal_banda_base = modulador.run(bits)
