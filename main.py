import os
import numpy as np
import matplotlib.pyplot as plt
from src.channel import RFChannel
from src.encoder import FECEncoder
from src.decoder import FECDecoder
from src.telemetry import TelemetryData, TelemetryPacket


def calculate_ber(tx_bits: np.ndarray, rx_bits: np.ndarray) -> float:
    """Gönderilen ve alınan bit dizileri arasındaki Bit Hata Oranını (BER) hesaplar."""
    return float(np.mean(tx_bits != rx_bits))


def demo_single_packet(channel: RFChannel, encoder: FECEncoder, decoder: FECDecoder):
    """
    Tek bir İHA/Model Uydu telemetri paketinin gürültülü kanalda (%2.5 Bit Hata Olasılıklı BSC)
    Kodlamasız, Hamming(7,4) ve Reed-Solomon ile iletimini karşılaştırır.
    """
    print("=" * 68)
    print("  1. CANLI TELEMETRİ PAKETİ İLETİM TESTİ (BSC Kanal, p_error = %2.5)")
    print("=" * 68)

    tx_data = TelemetryData(packet_id=101, altitude=750.25, pressure=92450.0, voltage=12.15)
    tx_bits = TelemetryPacket.pack_to_bits(tx_data)
    n_bits = len(tx_bits)

    print(f"[VERİCİ - GÖNDERİLEN] : {tx_data} ({n_bits} Bit)\n")

    p_err = 0.025  # Kanaldaki bitlerin %2.5'i gürültüyle ters döner

    # A) Kodlamasız (Uncoded) İletim
    rx_uncoded_bits = channel.bsc(tx_bits, p_error=p_err)
    rx_uncoded_data = TelemetryPacket.unpack_from_bits(rx_uncoded_bits)
    uncoded_errors = int(np.sum(tx_bits != rx_uncoded_bits))

    # B) Hamming(7,4) Kodlamalı İletim
    enc_ham = encoder.encode_hamming(tx_bits)
    rx_ham_ch = channel.bsc(enc_ham, p_error=p_err)
    dec_ham_bits = decoder.decode_hamming(rx_ham_ch, original_bit_len=n_bits)
    rx_ham_data = TelemetryPacket.unpack_from_bits(dec_ham_bits)
    ham_errors = int(np.sum(tx_bits != dec_ham_bits))

    # C) Reed-Solomon (24, 14) Kodlamalı İletim
    enc_rs = encoder.encode_rs(tx_bits)
    rx_rs_ch = channel.bsc(enc_rs, p_error=p_err)
    dec_rs_bits = decoder.decode_rs(rx_rs_ch, original_bit_len=n_bits)
    rx_rs_data = TelemetryPacket.unpack_from_bits(dec_rs_bits)
    rs_errors = int(np.sum(tx_bits != dec_rs_bits))

    print(f"[ALICI - KODLAMASIZ]  : {rx_uncoded_data} | Bozuk Bit: {uncoded_errors}")
    print(f"[ALICI - HAMMING(7,4)]: {rx_ham_data} | Bozuk Bit: {ham_errors}")
    print(f"[ALICI - REED-SOLOMON]: {rx_rs_data} | Bozuk Bit: {rs_errors}")
    print("=" * 68 + "\n")


def run_ber_simulation():
    """
    0 dB ile 10 dB arasındaki Eb/N0 değerleri için Monte Carlo simülasyonu yapar
    ve BER (Bit Hata Oranı) performans grafiğini 'assets/ber_curve.png' olarak kaydeder.
    """
    channel = RFChannel(seed=42)
    encoder = FECEncoder(rs_nsym=10)  # 14 Byte veri + 10 Byte Parity = RS(24,14)
    decoder = FECDecoder(rs_nsym=10)

    # Önce tek paketlik canlı demoyu çalıştır
    demo_single_packet(channel, encoder, decoder)

    print("=" * 68)
    print("  2. MONTE CARLO BER SİMÜLASYONU BAŞLIYOR (0 dB -> 10 dB)")
    print("=" * 68)

    snr_db_range = np.arange(0, 11, 1)
    num_packets_per_snr = 800  # Her SNR noktasında 800 paket (89.600 bit) test edilir

    ber_uncoded = []
    ber_hamming = []
    ber_rs = []

    # Örnek sabit telemetri paketi şablonu
    sample_data = TelemetryData(packet_id=1, altitude=500.0, pressure=101325.0, voltage=11.8)
    base_tx_bits = TelemetryPacket.pack_to_bits(sample_data)
    n_bits = len(base_tx_bits)

    # Kodu hızlandırmak için kodlanmış dizileri döngü dışında bir kez hazırla
    enc_ham_bits = encoder.encode_hamming(base_tx_bits)
    enc_rs_bits = encoder.encode_rs(base_tx_bits)

    rate_hamming = 4.0 / 7.0
    rate_rs = 14.0 / 24.0

    for snr_db in snr_db_range:
        err_u, err_h, err_r = 0.0, 0.0, 0.0

        for _ in range(num_packets_per_snr):
            # 1. Kodlamasız (Uncoded BPSK)
            rx_u = channel.awgn(base_tx_bits, eb_n0_db=snr_db, code_rate=1.0)
            err_u += calculate_ber(base_tx_bits, rx_u)

            # 2. Hamming(7,4)
            rx_h = channel.awgn(enc_ham_bits, eb_n0_db=snr_db, code_rate=rate_hamming)
            dec_h = decoder.decode_hamming(rx_h, original_bit_len=n_bits)
            err_h += calculate_ber(base_tx_bits, dec_h)

            # 3. Reed-Solomon(24,14)
            rx_r = channel.awgn(enc_rs_bits, eb_n0_db=snr_db, code_rate=rate_rs)
            dec_r = decoder.decode_rs(rx_r, original_bit_len=n_bits)
            err_r += calculate_ber(base_tx_bits, dec_r)

        avg_u = err_u / num_packets_per_snr
        avg_h = err_h / num_packets_per_snr
        avg_r = err_r / num_packets_per_snr

        ber_uncoded.append(avg_u)
        ber_hamming.append(avg_h)
        ber_rs.append(avg_r)

        print(f"Eb/N0: {snr_db:2d} dB | Uncoded BER: {avg_u:.6f} | Hamming BER: {avg_h:.6f} | RS BER: {avg_r:.6f}")

    # Logaritmik grafikte 0.0 değerlerinin çizilebilmesi için alt sınır (1e-7)
    ber_uncoded_plot = np.maximum(ber_uncoded, 1e-7)
    ber_hamming_plot = np.maximum(ber_hamming, 1e-7)
    ber_rs_plot = np.maximum(ber_rs, 1e-7)

    # Grafiği Oluştur ve Kaydet
    os.makedirs("assets", exist_ok=True)
    plt.figure(figsize=(10, 6))
    plt.semilogy(snr_db_range, ber_uncoded_plot, 'r-o', linewidth=2, label='Kodlamasız (Uncoded BPSK)')
    plt.semilogy(snr_db_range, ber_hamming_plot, 'b-s', linewidth=2, label='Hamming (7,4) [R = 4/7]')
    plt.semilogy(snr_db_range, ber_rs_plot, 'g-^', linewidth=2, label='Reed-Solomon (24,14) [R = 14/24]')

    plt.title('İHA ve Model Uydu Telemetri Hattı - FEC BER Başarım Analizi', fontsize=13, fontweight='bold')
    plt.xlabel('$E_b / N_0$ (dB)', fontsize=12)
    plt.ylabel('Bit Hata Oranı (BER)', fontsize=12)
    plt.ylim(1e-6, 1.0)
    plt.grid(True, which="both", linestyle="--", alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()

    output_path = os.path.join("assets", "ber_curve.png")
    plt.savefig(output_path, dpi=300)
    print(f"\n[BAŞARILI] Başarım grafiği '{output_path}' konumuna kaydedildi!")


if __name__ == "__main__":
    run_ber_simulation()