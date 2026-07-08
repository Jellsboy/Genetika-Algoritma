"""
============================================================
  ALGORITMA GENETIKA - PENCARIAN KATA DALAM KAMUS
  Bahasa Daerah: Bahasa Makassar (Basa Mangkasara')
============================================================
Program konsol dengan menu:
  1. Tampilkan Kamus
  2. Cari Kata
  3. Jalankan Algoritma Genetika
  4. Tampilkan Populasi
  5. Hasil Fitness
  6. Seleksi Roulette
  7. Cross Over
  8. Mutasi
  9. Generasi Baru
  10. Keluar

"""
import os
import random
import string

import openpyxl  # butuh: pip install openpyxl

NAMA_FILE_EXCEL = "Kamus_Bahasa Makassar.xlsx"


def muat_kamus(nama_file=NAMA_FILE_EXCEL):
    """Membaca kamus dari file Excel dan mengembalikannya sebagai list dict."""
    lokasi = os.path.join(os.path.dirname(os.path.abspath(__file__)), nama_file)
    if not os.path.exists(lokasi):
        lokasi = nama_file
    workbook = openpyxl.load_workbook(lokasi)
    sheet = workbook.active
    data = []
    for baris in sheet.iter_rows(min_row=2, values_only=True):
        if baris[0] is None:
            continue
        kata = str(baris[1]).strip().lower()
        arti = str(baris[2]).strip()
        data.append({"kata": kata, "arti": arti})
    return data


try:
    KAMUS = muat_kamus()
    print(f"[OK] Kamus dimuat dari '{NAMA_FILE_EXCEL}' ({len(KAMUS)} kata).")
except FileNotFoundError:
    print(f"[!] File '{NAMA_FILE_EXCEL}' tidak ditemukan. "
          f"Letakkan file Excel di folder yang sama dengan program ini.")
    raise SystemExit(1)

# Parameter GA
UKURAN_POPULASI = 50
LAJU_MUTASI = 0.08
MAKS_GENERASI = 300

# ---------------------------------------------------------------
# STATE GLOBAL (dipakai bersama antar menu)
# ---------------------------------------------------------------
state = {
    "target": None,      # kata yang dicari GA
    "charset": "",       # kumpulan karakter yang mungkin
    "populasi": [],      # daftar kromosom generasi saat ini
    "generasi": 0,       # nomor generasi saat ini
}


# ===============================================================
# FUNGSI-FUNGSI ALGORITMA GENETIKA
# ===============================================================
def buat_charset(target):
    """Charset = huruf a-z + karakter unik pada target (mis. apostrof)."""
    return "".join(sorted(set(string.ascii_lowercase) | set(target)))


def kromosom_acak(panjang, charset):
    return "".join(random.choice(charset) for _ in range(panjang))


def hitung_fitness(kromosom, target):
    """Fitness = jumlah karakter yang cocok pada posisi yang sama."""
    return sum(1 for a, b in zip(kromosom, target) if a == b)


def buat_populasi_awal():
    target = state["target"]
    charset = state["charset"]
    state["populasi"] = [
        kromosom_acak(len(target), charset) for _ in range(UKURAN_POPULASI)
    ]
    state["generasi"] = 1


def tabel_fitness():
    """Kembalikan daftar (index, kromosom, fitness, prob, kumulatif)."""
    target = state["target"]
    nilai = [hitung_fitness(k, target) for k in state["populasi"]]
    total = sum(nilai)
    n = len(state["populasi"])
    hasil = []
    kum = 0.0
    for i, k in enumerate(state["populasi"]):
        prob = nilai[i] / total if total > 0 else 1 / n
        kum += prob
        hasil.append(
            {"index": i, "kromosom": k, "fitness": nilai[i],
             "prob": prob, "kumulatif": kum}
        )
    return hasil, total


def seleksi_roulette(tabel):
    """Putar roda roulette sebanyak ukuran populasi -> induk terpilih."""
    hasil = []
    for putaran in range(len(tabel)):
        r = random.random()
        terpilih = next((row for row in tabel if r <= row["kumulatif"]), tabel[-1])
        hasil.append({"putaran": putaran + 1, "r": r,
                      "index": terpilih["index"],
                      "kromosom": terpilih["kromosom"]})
    return hasil


def crossover(induk):
    """Crossover satu titik untuk tiap pasangan induk."""
    detail, anak = [], []
    for i in range(0, len(induk) - 1, 2):
        a, b = induk[i], induk[i + 1]
        titik = random.randint(1, len(a) - 1)
        anak1 = a[:titik] + b[titik:]
        anak2 = b[:titik] + a[titik:]
        detail.append({"pasangan": i // 2 + 1, "induk1": a, "induk2": b,
                       "titik": titik, "anak1": anak1, "anak2": anak2})
        anak.extend([anak1, anak2])
    if len(induk) % 2 == 1:
        anak.append(induk[-1])
    return detail, anak


def mutasi(populasi):
    """Tiap gen berpeluang berubah sesuai LAJU_MUTASI."""
    charset = state["charset"]
    detail, hasil = [], []
    for i, kromosom in enumerate(populasi):
        gen = list(kromosom)
        perubahan = []
        for pos in range(len(gen)):
            if random.random() < LAJU_MUTASI:
                lama = gen[pos]
                baru = random.choice(charset)
                while baru == lama and len(charset) > 1:
                    baru = random.choice(charset)
                gen[pos] = baru
                perubahan.append((pos, lama, baru))
        sesudah = "".join(gen)
        detail.append({"index": i, "sebelum": kromosom,
                       "sesudah": sesudah, "perubahan": perubahan})
        hasil.append(sesudah)
    return detail, hasil


def bentuk_generasi_baru():
    """Satu siklus GA penuh -> populasi generasi berikutnya (dengan elitisme)."""
    target = state["target"]
    tabel, _ = tabel_fitness()
    roulette = seleksi_roulette(tabel)
    induk = [row["kromosom"] for row in roulette]
    _, anak = crossover(induk)
    _, anak = mutasi(anak)
    # Elitisme: pastikan individu terbaik tidak hilang
    terbaik = max(state["populasi"], key=lambda k: hitung_fitness(k, target))
    fit_terbaik = hitung_fitness(terbaik, target)
    if not any(hitung_fitness(k, target) >= fit_terbaik for k in anak):
        anak[0] = terbaik
    state["populasi"] = anak
    state["generasi"] += 1


def kromosom_terbaik():
    target = state["target"]
    best = max(state["populasi"], key=lambda k: hitung_fitness(k, target))
    return best, hitung_fitness(best, target)


# ===============================================================
# MENU (tampilan)
# ===============================================================
def butuh_target():
    if state["target"] is None:
        print("\n[!] Belum ada target. Pilih menu 3 (Jalankan Algoritma "
              "Genetika) terlebih dahulu.")
        return False
    return True


def menu_tampilkan_kamus():
    print("\n--- KAMUS BAHASA MAKASSAR ---")
    print(f"{'No':<4}{'Kata':<12}{'Arti'}")
    print("-" * 40)
    for i, e in enumerate(KAMUS, 1):
        print(f"{i:<4}{e['kata']:<12}{e['arti']}")


def menu_cari_kata():
    q = input("\nMasukkan kata / arti yang dicari: ").strip().lower()
    cocok = [e for e in KAMUS
             if e["kata"].lower() == q or q in e["arti"].lower()]
    if cocok:
        for e in cocok:
            print(f"  Ditemukan: '{e['kata']}' berarti '{e['arti']}'.")
    else:
        print(f"  Kata '{q}' TIDAK ditemukan di dalam kamus.")


def menu_jalankan_ga():
    q = input("\nMasukkan kata target (kosongkan untuk pilih dari kamus): ").strip().lower()
    if not q:
        menu_tampilkan_kamus()
        try:
            no = int(input("Pilih nomor kata: "))
            q = KAMUS[no - 1]["kata"].lower()
        except (ValueError, IndexError):
            print("  Pilihan tidak valid.")
            return

    state["target"] = q
    state["charset"] = buat_charset(q)
    buat_populasi_awal()
    print(f"\n  Target        : {q}")
    print(f"  Charset       : {state['charset']} ({len(state['charset'])} karakter)")
    print(f"  Ukuran pop.   : {UKURAN_POPULASI}")
    print(f"  Laju mutasi   : {LAJU_MUTASI*100:.0f}%")
    print(f"  Maks generasi : {MAKS_GENERASI}")
    print(f"  Populasi generasi ke-1 dibuat secara acak.")

    auto = input("\nJalankan otomatis sampai ketemu? (y/n): ").strip().lower()
    if auto == "y":
        while state["generasi"] < MAKS_GENERASI:
            best, fit = kromosom_terbaik()
            print(f"  Generasi {state['generasi']:>3} | terbaik: {best} "
                  f"| fitness: {fit}/{len(q)}")
            if fit >= len(q):
                print(f"\n  >> SOLUSI DITEMUKAN pada generasi ke-{state['generasi']}: {best}")
                return
            bentuk_generasi_baru()
        best, fit = kromosom_terbaik()
        print(f"\n  Selesai. Terbaik: {best} (fitness {fit}/{len(q)})")
    else:
        print("  Gunakan menu 4-9 untuk melihat proses per langkah, "
              "dan menu 9 untuk membentuk generasi baru.")

def menu_hasil_fitness():
    if not butuh_target():
        return
    target = state["target"]
    tabel, total = tabel_fitness()
    maks = len(target)
    print(f"\n--- HASIL FITNESS (Generasi ke-{state['generasi']}) ---")
    print(f"  CARA KERJA: Fitness = jumlah huruf yang COCOK posisinya")
    print(f"             dengan target '{target}'. (maksimum = {maks})")
    print("-" * 52)
    for row in tabel:
        k = row["kromosom"]
        rincian = " ".join(
            f"{k[i]}={target[i]}(1)" if k[i] == target[i]
            else f"{k[i]}!={target[i]}(0)"
            for i in range(maks)
        )
        persen = row["fitness"] / maks * 100
        print(f"  [{row['index']:>2}] {k:<12} -> {rincian}")
        print(f"        = fitness {row['fitness']}/{maks} ({persen:.0f}%)")
    print(f"\n  Total fitness populasi = {total}")

def menu_seleksi_roulette():
    if not butuh_target():
        return
    tabel, total = tabel_fitness()
    print(f"\n--- SELEKSI ROULETTE (Generasi ke-{state['generasi']}) ---")
    print(f"  CARA KERJA: Probabilitas = fitness / total fitness ({total}).")
    print(f"             Kumulatif = penjumlahan berjalan dari probabilitas.")
    print("-" * 52)
    print(f"  {'Idx':<5}{'Kromosom':<14}{'Prob (f/tot)':<16}{'Kumulatif'}")
    for row in tabel:
        print(f"  {row['index']:<5}{row['kromosom']:<14}"
              f"{str(row['fitness']) + '/' + str(total) + '=' + format(row['prob'], '.3f'):<16}"
              f"{row['kumulatif']:.3f}")
    print("\n  Putar roda sebanyak ukuran populasi. Tiap putaran ambil")
    print("  angka acak r, pilih kromosom pertama dengan kumulatif >= r:")
    print(f"  {'Putaran':<9}{'Angka acak':<13}{'Terpilih idx':<14}{'Kromosom'}")
    for r in seleksi_roulette(tabel):
        print(f"  {r['putaran']:<9}{r['r']:<13.3f}{r['index']:<14}{r['kromosom']}")

def menu_crossover():
    if not butuh_target():
        return
    tabel, _ = tabel_fitness()
    induk = [row["kromosom"] for row in seleksi_roulette(tabel)]
    detail, _ = crossover(induk)
    print(f"\n--- CROSS OVER (Generasi ke-{state['generasi']}) ---")
    print(f"  CARA KERJA: dari 1 titik potong, Anak1 = (kiri Induk1)+(kanan")
    print(f"             Induk2), Anak2 = (kiri Induk2)+(kanan Induk1).")
    print("-" * 52)
    for d in detail:
        t = d["titik"]
        i1, i2 = d["induk1"], d["induk2"]
        print(f"  Pasangan {d['pasangan']} | titik potong = {t}")
        print(f"    Induk1 = {i1[:t]}|{i1[t:]}")
        print(f"    Induk2 = {i2[:t]}|{i2[t:]}")
        print(f"    Anak1  = {i1[:t]}+{i2[t:]} = {d['anak1']}")
        print(f"    Anak2  = {i2[:t]}+{i1[t:]} = {d['anak2']}")

def menu_mutasi():
    if not butuh_target():
        return
    detail, _ = mutasi(state["populasi"])
    print(f"\n--- MUTASI (Generasi ke-{state['generasi']}) ---")
    print(f"  CARA KERJA: tiap huruf berpeluang {LAJU_MUTASI * 100:.0f}% berubah")
    print(f"             menjadi huruf acak (menjaga keragaman).")
    print("-" * 52)
    print(f"  {'Idx':<5}{'Sebelum':<14}{'Sesudah':<14}{'Gen berubah'}")
    for d in detail:
        perub = ", ".join(f"pos{p}:{l}->{b}" for p, l, b in d["perubahan"]) or "-"
        print(f"  {d['index']:<5}{d['sebelum']:<14}{d['sesudah']:<14}{perub}")

def menu_tampilkan_populasi():
    if not butuh_target():
        return
    print(f"\n--- POPULASI (Generasi ke-{state['generasi']}) ---")
    for i, k in enumerate(state["populasi"]):
        print(f"  [{i:>2}] {k}")




def menu_generasi_baru():
    if not butuh_target():
        return
    lama = state["generasi"]
    bentuk_generasi_baru()
    best, fit = kromosom_terbaik()
    print(f"\n--- GENERASI BARU: {lama} -> {state['generasi']} ---")
    print(f"  Terbaik sekarang: {best} (fitness {fit}/{len(state['target'])})")
    for i, k in enumerate(state["populasi"]):
        print(f"  [{i:>2}] {k}  (fitness {hitung_fitness(k, state['target'])})")
    if fit >= len(state["target"]):
        print(f"\n  >> SOLUSI DITEMUKAN: {best}")


def main():
    menu = {
        "1": ("Tampilkan Kamus", menu_tampilkan_kamus),
        "2": ("Cari Kata", menu_cari_kata),
        "3": ("Jalankan Algoritma Genetika", menu_jalankan_ga),
        "4": ("Tampilkan Populasi", menu_tampilkan_populasi),
        "5": ("Hasil Fitness", menu_hasil_fitness),
        "6": ("Seleksi Roulette", menu_seleksi_roulette),
        "7": ("Cross Over", menu_crossover),
        "8": ("Mutasi", menu_mutasi),
        "9": ("Generasi Baru", menu_generasi_baru),
    }
    while True:
        print("\n" + "=" * 44)
        print("   KAMUS BAHASA MAKASSAR - ALGORITMA GENETIKA")
        print("=" * 44)
        for k, (label, _) in menu.items():
            print(f"  {k}. {label}")
        print("  10. Keluar")
        pilih = input("Pilih menu: ").strip()
        if pilih == "10":
            print("\nTerima kasih. Program selesai.")
            break
        aksi = menu.get(pilih)
        if aksi:
            aksi[1]()
        else:
            print("  Pilihan tidak valid.")


if __name__ == "__main__":
    main()