import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import re


def escape_special_chars(key):
    return re.escape(key)

def ekstrak_nilai(pesan):
    # Pemisahan pesan menjadi bagian-bagian
    bagian = pesan.split('\n')

    # Memastikan bahwa ada cukup bagian dalam pesan
    if len(bagian) < 6:
        # Tangani kasus di mana tidak ada bagian yang cukup
        return None

    # Inisialisasi struktur data untuk menyimpan nilai
    hasil = {}

    # Memastikan bahwa ada cukup bagian dalam pesan untuk ekstraksi nilai
    if "Pendaftaran Rawat Jalan Pasien Umum" in pesan:
        # Ekstraksi nilai #5, #6, #8
        hasil['jenis_pesan'] = 'pendaftaran'
        for key in [
        'Nama', 'NIK', 'Tanggal Lahir', 'Tempat Lahir', 'No HP', 'ALamat Lengkap','Poli Tujuan','Jadwal Kedatangan'
    ]:
            if key in pesan:
                escaped_key = escape_special_chars(key)
                key_match = re.search(fr'{escaped_key}\s*:\s*(.+)', pesan)
                hasil[key] = key_match.group(1).strip() if key_match else None
    elif "Konfirmasi data pendaftar" in pesan:
        hasil['jenis_pesan'] = 'konfirmasi'
        for key in [
        'id', 'status',
    ]:
            if key in pesan:
                escaped_key = escape_special_chars(key)
                key_match = re.search(fr'{escaped_key}\s*:\s*(.+)', pesan)
                hasil[key] = key_match.group(1).strip() if key_match else None
    
    return hasil

# def storedata(nama,nik,tanggal_lahir,tempat_lahir,nope,alamat,poli_tujuan,jadwal_kedatangan):
def storedata(datasimpan):
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open("Pendaftaran Rawat Jalan").worksheet("pendaftaran")
    list_of_hashes = sheet.get_all_records()
    # row = [nama,nik,tanggal_lahir,tempat_lahir,nope,alamat,poli_tujuan,jadwal_kedatangan]
    row = datasimpan
    sheet.insert_row(row,len(list_of_hashes)+2)

def getmessage():
    getupdate = "https://api.telegram.org/bot6761742311:AAHcGMoF-j_eXN1VU1aoRA8zWkCZx_qIWEA/getUpdates"
    getupdate_response = requests.get(getupdate).json()
    return getupdate_response['result'][len(getupdate_response['result']) - 1]['message']['chat']['id'],getupdate_response['result'][len(getupdate_response['result']) - 1]['message']['text'], getupdate_response['result'][len(getupdate_response['result']) - 1]['update_id']
   

# senmessage = "https://api.telegram.org/bot6761742311:AAHcGMoF-j_eXN1VU1aoRA8zWkCZx_qIWEA/sendMessage?chat_id=6144709186&text=Send Message Bot"
# senmessage_response = requests.get(senmessage).json()
# print(senmessage_response)
idchat_tmp,pesan_tmp, updateid_temp = getmessage()
while True:
    idchat,pesan,updateid = getmessage()
    if(updateid != updateid_temp):
        print(idchat,pesan)
        ekstrak_pesan = ekstrak_nilai(pesan)
        print(ekstrak_pesan)
        if ekstrak_pesan['jenis_pesan'] == 'pendaftaran':
            del ekstrak_pesan['jenis_pesan']
            array_simpan = []
            for kunci, nilai in ekstrak_pesan.items():
                array_simpan.append(nilai)
                # print(f"{nilai}")
            # print(ekstrak_pesan)
            array_simpan.append(idchat)
            storedata(array_simpan)
            senmessage = "https://api.telegram.org/bot6761742311:AAHcGMoF-j_eXN1VU1aoRA8zWkCZx_qIWEA/sendMessage"
            param_pendaftar = {
                "chat_id" : idchat,
                "text": "Terima Kasih,permintaan registrasi anda sedang diproses oleh petugas kami maksimal 1x24 jam hari kerja. Mohon menunggu, Anda akan diberitahu melalui bot ini jika registrasi diterima"
            }
            senmessage_response_admin = requests.get(senmessage,params=param_pendaftar).json()
            param_admin = {
                "chat_id" : 1150781194,
                "text": "Halo aa/teteh ada yang mau daftar rawat jalan nih, mohon cek data yang dikirimkan oleh pasien dengan id :"+str(idchat)+" . Jika data sudah diverifikasi notifikasi akan dikirimkan oleh sistem ke pasien"
            }
            senmessage_response_admin = requests.get(senmessage,params=param_admin).json()
            newary = {"jenis_pesan":"pendaftaran"}
            ekstrak_pesan.update(newary)
        if ekstrak_pesan['jenis_pesan'] == 'konfirmasi':
            senmessage = "https://api.telegram.org/bot6761742311:AAHcGMoF-j_eXN1VU1aoRA8zWkCZx_qIWEA/sendMessage"
            if(ekstrak_pesan['status'] == 'diterima'):
                param_konfirm = {
                    "chat_id" : ekstrak_pesan['id'],
                    "text": "Data sudah diverifikasi oleh admin. Mohon tunjukkan bukti chat ini ke petugas pendaftaran puskesmas sesuai jadwal dengan membawa kartu identitas diri yang berlaku"
                }
            if(ekstrak_pesan['status'] == 'ditolak'):
                param_konfirm = {
                    "chat_id" : ekstrak_pesan['id'],
                    "text": "Pendaftaran kamu ditolak, silahkan hubungi admin"
                }
            senmessage_response_konfirm = requests.get(senmessage,params=param_konfirm).json()
            print('admin balas')
    else:
        print("belum ada pesan baru")
    idchat_tmp = idchat
    pesan_tmp = pesan
    updateid_temp = updateid
    time.sleep(1)