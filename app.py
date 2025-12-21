import os
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
import pandas as pd
import math # Diperlukan untuk abs() jika tidak menggunakan builtin abs()

# --- Konfigurasi Aplikasi ---
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Hanya izinkan file Excel (.xlsx)
ALLOWED_EXTENSIONS = {'xlsx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Fungsi Parsing S-box dari XLSX ---
def parse_sbox(filepath):
    """
    Membaca S-box dari file XLSX menggunakan pandas.
    Diasumsikan S-box 8x8 (256 nilai) ada di sheet pertama.
    """
    try:
        # Baca file Excel tanpa header
        df = pd.read_excel(filepath, header=None)
        
        # Flatten the dataframe (mengubah data menjadi satu dimensi list)
        s_box = df.values.flatten().tolist()
        
        # Bersihkan nilai non-numerik (NaN) dan konversi ke integer
        s_box_clean = []
        for x in s_box:
            # Mengabaikan nilai NaN (Not a Number)
            if pd.isna(x):
                continue
            
            # Mengonversi float ke integer (misal 10.0 menjadi 10)
            try:
                s_box_clean.append(int(x))
            except ValueError:
                # Menangani jika ada teks atau karakter aneh yang tersisa
                pass 
        
        s_box = s_box_clean
        
        # Validasi Ukuran
        if len(s_box) != 256:
            return None, f"Gagal: S-box harus memiliki 256 nilai (8x8), ditemukan {len(s_box)}."
            
        # Validasi Rentang Nilai
        if not all(0 <= x <= 255 for x in s_box):
            return None, "Gagal: Nilai S-box harus dalam rentang 0 hingga 255."
            
        return s_box, "Sukses"
    except Exception as e:
        return None, f"Gagal memparsing file Excel: {e}"

# --- Fungsi Pengujian S-box (Implementasi Dummy dengan Analisis Kualitas) ---
def calculate_sbox_properties(s_box):
    """
    Fungsi DUMMY untuk menghitung properti S-box. Ganti dengan implementasi RIIL.
    """
    
    # KRITERIA IDEAL S-BOX 8x8 (n=8, m=8)
    IDEAL = {
        "NL": 112,       # Non-Linearity: Setinggi mungkin
        "SAC": 0.5,      # Strict Avalanche Criterion: Ideal 0.5
        "BIC_NL": 112,   # BIC-NL: Setinggi mungkin
        "BIC_SAC": 0.5,  # BIC-SAC: Ideal 0.5
        "LAP": 0.0625,   # Linear Approx. Prob.: Serendah mungkin (16/256)
        "DU": 4,         # Differential Uniformity: Serendah mungkin (min 4 untuk 8x8)
        "AD": 7,         # Algebraic Degree: Setinggi mungkin
        "TO": 7,         # Transparency Order: Setinggi mungkin
        "CI": 7,         # Correlation Immunity: Setinggi mungkin
        "DAP": 4,        # Differential Approx. Prob.: Serendah mungkin
    }

    # HASIL UJI DUMMY DARI S-BOX (GANTIKAN INI DENGAN PERHITUNGAN NYATA)
    results = {
        "NL": 108,
        "SAC": 0.505,
        "BIC_NL": 104,
        "BIC_SAC": 0.51,
        "LAP": 0.075,
        "DAP": 8,
        "DU": 8,
        "AD": 7,
        "TO": 7,
        "CI": 6,
    }
    
    analyzed_results = {}
    
    for key, value in results.items():
        ideal_value = IDEAL.get(key, '-')
        status = "Tidak Diketahui"

        if key in IDEAL:
            ideal = IDEAL[key]
            
            # --- Properti yang harus MAKSIMAL (NL, BIC_NL, AD, TO, CI) ---
            if key in ["NL", "BIC_NL", "AD", "TO", "CI"]: 
                deviation = ideal - value
                if deviation == 0:
                    status = "SANGAT BAIK (Ideal)"
                elif deviation <= 4: # Toleransi 4 dari Max
                    status = "Baik"
                else:
                    status = "Kurang Baik"
                    
            # --- Properti yang harus mendekati IDEAL 0.5 (SAC, BIC_SAC) ---
            elif key in ["SAC", "BIC_SAC"]:
                deviation = abs(ideal - value)
                if deviation <= 0.005: # Toleransi 0.005
                    status = "SANGAT BAIK (Ideal)"
                elif deviation <= 0.02: # Toleransi 0.02
                    status = "Baik"
                else:
                    status = "Kurang Baik"
            
            # --- Properti yang harus MINIMAL (LAP, DU, DAP) ---
            elif key in ["LAP", "DU", "DAP"]:
                deviation = value - ideal
                if deviation == 0:
                    status = "SANGAT BAIK (Ideal)"
                elif deviation <= 4: # Toleransi 4 dari Min
                    status = "Baik"
                else:
                    status = "Kurang Baik"


        analyzed_results[key] = {
            "value": value,
            "ideal": ideal_value,
            "status": status,
            # Jika Anda ingin menampilkan deviasi di frontend, uncomment baris di bawah ini
            # "deviation": deviation
        }
        
    return analyzed_results

# --- Routing Flask ---

@app.route('/', methods=['GET'])
def index():
    # Pastikan file index.html berada di folder 'templates'
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    # 1. Pastikan file diunggah
    if 'sbox_file' not in request.files:
        return jsonify({'success': False, 'message': 'Tidak ada bagian file'}), 400
    
    file = request.files['sbox_file']
    
    # 2. Pastikan nama file valid dan tipe diizinkan
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Tidak ada file terpilih'}), 400
        
    if not allowed_file(file.filename):
        # Pesan error yang sudah diubah
        return jsonify({'success': False, 'message': 'Tipe file tidak diizinkan. Gunakan XLSX.'}), 400

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Simpan file yang diunggah
        file.save(filepath)
        
        # 3. Parsing S-box
        s_box_data, message = parse_sbox(filepath)
        
        # Hapus file setelah diproses
        os.remove(filepath)

        if s_box_data is None:
            return jsonify({'success': False, 'message': message}), 400
            
        # 4. Hitung dan Analisis Properti
        analyzed_properties = calculate_sbox_properties(s_box_data)
        
        return jsonify({
            'success': True,
            'message': 'Analisis S-box berhasil diselesaikan!',
            'sbox_properties': analyzed_properties,
            'sbox_size': f"{len(s_box_data)} (8x8)"
        })

if __name__ == '__main__':
    app.run(debug=True)