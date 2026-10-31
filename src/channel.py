import numpy as np
from typing import Tuple, Union

class RFChannel:
    """
    İHA ve Model Uydu Telemetri Hattı için RF Kanal ve Gürültü Simülasyon Modülü.
    BSC (İkili Simetrik Kanal) ve BPSK tabanlı AWGN (Toplamsal Beyaz Gauss Gürültüsü) 
    modellerini içerir.
    """

    def __init__(self, seed: int = None):
        """
        Tekrarlanabilir simülasyon sonuçları  için 
        rastgele sayı üreteci  başlatılır.
        """
        self.rng = np.random.default_rng(seed)

    def bsc(self, bits: np.ndarray, p_error: float) -> np.ndarray:
        """
        Binary Symmetric Channel (İkili Simetrik Kanal) Modeli.
        Gönderilen her biti 'p_error' olasılığıyla tersine çevirir (0 -> 1, 1 -> 0).

        Parametreler:
            bits (np.ndarray): İletilecek 0 ve 1'lerden oluşan bit dizisi.
            p_error (float): Bit hata olasılığı (Crossover probability), 0.0 <= p <= 1.0.

        Dönüş:
            np.ndarray: Kanaldan geçmiş (bozulmuş) bit dizisi.
        """
        if not (0.0 <= p_error <= 1.0):
            raise ValueError("Hata olasılığı (p_error) 0.0 ile 1.0 arasında olmalıdır.")

        # Her bit için [0, 1) aralığında rastgele sayı üret; p_error'dan küçükse 1 (hata), değilse 0
        error_mask = (self.rng.random(size=bits.shape) < p_error).astype(np.uint8)
        
        # XOR işlemi ile maskenin 1 olduğu indekslerdeki bitleri ters çevir
        corrupted_bits = np.bitwise_xor(bits.astype(np.uint8), error_mask)
        return corrupted_bits

    def awgn(
        self, 
        bits: np.ndarray, 
        eb_n0_db: float, 
        code_rate: float = 1.0, 
        return_soft: bool = False
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        BPSK Modülasyonlu AWGN (Additive White Gaussian Noise) Kanal Modeli.
        Bitleri BPSK sembollerine (-1, +1) dönüştürür, SNR (Eb/N0) değerine göre
        Gauss gürültüsü ekler ve alıcıda eşikleme (demodülasyon) yapar.

        Parametreler:
            bits (np.ndarray): İletilecek 0 ve 1'lerden oluşan bit dizisi.
            eb_n0_db (float): Bit enerjisinin gürültü güç spektral yoğunluğuna oranı (dB).
            code_rate (float): FEC kodlama oranı (R = k/n). Kodlamasız sistem için 1.0,
                               Hamming(7,4) için 4/7 (~0.571) girilmelidir.
            return_soft (bool): True ise gürültülü analog genlikleri de (Soft Decision için) döndürür.

        Dönüş:
            np.ndarray: Demodüle edilmiş bit dizisi (return_soft=True ise (bitler, analog_sinyal) tuple'ı).
        """
        if code_rate <= 0.0 or code_rate > 1.0:
            raise ValueError("Kodlama oranı (code_rate) (0, 1] aralığında olmalıdır.")

        # 1. BPSK Modülasyonu (0 -> -1.0V, 1 -> +1.0V)
        tx_symbols = 2.0 * bits.astype(np.float64) - 1.0

        # 2. Eb/N0 (dB) -> Es/N0 (Lineer) Dönüşümü ve Gürültü Standart Sapması (Sigma)
        eb_n0_linear = 10.0 ** (eb_n0_db / 10.0)
        es_n0_linear = eb_n0_linear * code_rate
        
        # Gerçek değerli (BPSK) sinyaller için iki yönlü gürültü gücü: N0 / 2
        noise_std = np.sqrt(1.0 / (2.0 * es_n0_linear))

        # 3. Gauss Dağılımlı Gürültü Üretimi N(0, sigma^2) ve Kanala Ekleme
        noise = self.rng.normal(loc=0.0, scale=noise_std, size=tx_symbols.shape)
        rx_symbols = tx_symbols + noise

        # 4. Hard Decision Demodülasyon (Karar Eşiği = 0.0)
        rx_bits = (rx_symbols >= 0.0).astype(np.uint8)

        if return_soft:
            return rx_bits, rx_symbols
        return rx_bits


# --- HIZLI DOĞRULAMA TESTİ (Dosya doğrudan çalıştırıldığında devreye girer) ---
if __name__ == "__main__":
    channel = RFChannel(seed=42)
    test_bits = np.random.randint(0, 2, size=100_000, dtype=np.uint8)

    print("=== 1. BSC (Binary Symmetric Channel) Testi ===")
    for p in [0.01, 0.05, 0.10]:
        rx_bsc = channel.bsc(test_bits, p_error=p)
        measured_ber = np.mean(test_bits != rx_bsc)
        print(f"Hedeflenen p: {p:.3f} | Ölçülen BER: {measured_ber:.5f}")

    print("\n=== 2. AWGN (BPSK) Kanal Testi (Uncoded, R=1.0) ===")
    for snr_db in [0, 2, 4, 6, 8]:
        rx_awgn = channel.awgn(test_bits, eb_n0_db=snr_db, code_rate=1.0)
        measured_ber = np.mean(test_bits != rx_awgn)
        print(f"Eb/N0: {snr_db:2d} dB | Ölçülen BER: {measured_ber:.5f}")