# Wildlitics

**Dari data tabulasi menjadi aksi konservasi**

Wildlitics adalah aplikasi desktop Windows untuk membantu pengelolaan foto kamera trap, identifikasi satwa berbantuan AI, koreksi manusia, analisis biodiversitas, dan penyusunan laporan. Aplikasi dikembangkan oleh **Brian Martin** dengan memanfaatkan model dan pustaka pihak ketiga yang memperoleh kredit terpisah.

Dokumentasi ini menjelaskan prototipe **2.3.3 Activity Diagrams**, dengan model SpeciesNet dan BioCLIP 2. Materi Wildlitics di repositori ini berupa **dokumentasi saja**, bukan kode aplikasi, installer, bobot model, atau data penelitian. Mengunduh atau melakukan clone repositori ini tidak memasang aplikasi.

## Fitur utama

- Proyek terpisah dengan deskripsi, galeri, database, dan hasil sortiran masing-masing.
- Antrean unggah folder per kamera, dengan tombol penambahan kamera trap.
- Deteksi kotak satwa dan identifikasi berbantuan SpeciesNet serta BioCLIP 2.
- Galeri hingga 50 foto per halaman, konfirmasi batch, dan koreksi label.
- Salinan foto yang dikelompokkan menurut hasil identifikasi tanpa menghapus foto sumber.
- Referensi nama ilmiah dan status IUCN dari workbook lokal yang dipilih pengguna.
- Impor metadata kamera dan deployment dari Excel; impor titik kamera dan lapisan peta lokal dari KML.
- Peta offline, ringkasan kehadiran per spesies dan kamera, serta analisis aktivitas 24 jam.
- Pilihan kejadian independen dengan jeda 30 atau 60 menit.
- Ekspor tabel dan laporan PDF, disertai HTML interaktif offline.
- Ekspor data koreksi dan pelatihan head lokal opsional tanpa menimpa bobot model dasar.

## Model yang digunakan

| Komponen | Peran dalam aplikasi | Sumber resmi |
| --- | --- | --- |
| MegaDetector MDV6-yolov10-c | Menemukan kotak satwa, manusia, dan kendaraan | [Microsoft AI for Good dan kontributor](https://microsoft.github.io/Biodiversity/model_zoo/megadetector/) |
| SpeciesNet classifier 4.0.3a, paket 5.0.5 | Memberi kandidat identifikasi taksonomi pada kotak satwa | [Google dan kontributor](https://github.com/google/cameratrapai) |
| BioCLIP 2 | Membandingkan crop satwa dengan kandidat nama dalam checklist lokal | [Imageomics Institute dan kontributor](https://huggingface.co/imageomics/bioclip-2) |
| OpenCLIP 3.3.0 | Menjalankan komponen model citra dan teks | [ML Foundations dan kontributor](https://github.com/mlfoundations/open_clip) |

Penggabungan SpeciesNet dan BioCLIP 2 bersifat bersyarat, bukan dijalankan identik pada semua foto. Hasil yang masih berupa takson luas, konflik, atau jenis di luar checklist memerlukan review; daftar lokal tidak boleh digunakan untuk memaksakan identitas spesies.

Training dari koreksi pengguna membuat head lokal terpisah pada fitur BioCLIP yang dibekukan. Fitur ini tidak melatih ulang seluruh model dasar, tidak otomatis mengaktifkan hasil training, dan tidak menjamin peningkatan akurasi.

## Alur penggunaan

1. Buat proyek dan isi deskripsi survei.
2. Daftarkan ID kamera beserta folder foto masing-masing.
3. Jalankan analisis AI dan periksa hasilnya.
4. Konfirmasi atau koreksi foto yang sudah ditinjau manusia.
5. Lengkapi lokasi serta periode pemasangan kamera.
6. Pilih spesies, kamera, status verifikasi, dan aturan kejadian independen.
7. Periksa tabel, peta, grafik, lalu ekspor laporan.

Petunjuk pemasangan berlaku untuk pengguna yang telah menerima paket aplikasi dari pengembang. Paket distribusi tidak tersedia di repositori dokumentasi ini.

## Analisis dan laporan

Wildlitics merangkum kekayaan jenis, komposisi deteksi, kejadian independen, kehadiran per kamera, status IUCN, dan waktu deteksi per spesies. Interpretasi bergantung pada kelengkapan foto, mutu verifikasi, waktu kamera, dan metadata survei.

- **N kejadian independen:** spesies dan kamera yang sama dikelompokkan dengan jeda 30 atau 60 menit dari foto sebelumnya.
- **Aktivitas 24 jam:** satu panel per spesies pada laporan; KDE sirkular memakai bandwidth tetap satu jam. Sampel kurang dari lima kejadian memakai histogram, sedangkan waktu yang tidak layak ditandai belum tersedia.
- **Kehadiran per kamera:** deteksi, nondeteksi yang memenuhi prasyarat sampling, dan data tidak tersedia dibedakan. Kamera tanpa rekaman tidak otomatis dianggap tidak memiliki satwa.
- **Status IUCN:** mengikuti referensi Excel lokal, bukan penilaian AI atau pembaruan daring otomatis. Nama yang tidak cocok tidak diberi status tebakan.
- **Peta offline:** mengikuti koordinat dan lapisan proyek. Batas peta tidak membatasi wilayah kerja ke Kalimantan Timur, tetapi kesesuaian checklist model harus tetap diperiksa.
- **Ekspor:** PDF berisi grafik, tabel, dan foto representatif; HTML pendamping menyediakan interaksi offline. Crop foto digunakan bila kaitan spesies dengan kotak AI dapat dipastikan.

Kurva aktivitas menggambarkan pola deteksi teramati, bukan lama satwa benar-benar aktif. Foto representatif dengan skor tinggi bukan pengukuran akurasi spesies.

## Batas penggunaan ilmiah

Angka confidence **0–99% bukan akurasi yang sudah terukur** atau jaminan bahwa jenis benar. Label sampai genus atau tingkat lebih tinggi memerlukan koreksi sebelum dipakai sebagai identifikasi spesies.

Jumlah kejadian independen bukan jumlah individu atau ukuran populasi. Rentang EXIF bukan jaminan kamera selalu beroperasi. Tidak ada deteksi tidak otomatis berarti spesies tidak hadir.

Prototipe ini belum memiliki estimasi akurasi independen yang dapat dinyatakan dari audit yang tersedia. Gunakan AI sebagai alat bantu dengan verifikasi manusia dan rancangan survei yang sesuai; jangan menjadikannya satu-satunya dasar keputusan konservasi. Keunggulan ensemble dibandingkan masing-masing model belum ditetapkan melalui uji lokal yang berpasangan dan independen.

Uji akurasi perlu menggunakan label acuan ahli yang independen, memisahkan burst dan lokasi antara data pengembangan dan pengujian, serta mencatat prediksi salah, tak teridentifikasi, kosong, dan error. Laporkan precision, recall, F1, confusion matrix, cakupan keputusan, dan ketidakpastiannya. Metrik evaluasi bawaan masih memerlukan peninjauan; kelulusan tes perangkat lunak tidak membuktikan kualitas identifikasi di lapangan.

## Privasi data

Dokumentasi Wildlitics tidak menyertakan foto kamera trap, database penelitian, koordinat sensitif, workbook pengguna, atau model hasil training pribadi. Inferensi aplikasi berlangsung lokal setelah komponen tersedia; pemasangan dependensi atau pengunduhan model dapat membutuhkan internet.

Periksa foto manusia, metadata EXIF, lokasi spesies sensitif, dan lampiran sebelum membagikan hasil. Salinan hasil sortiran tidak menggantikan kebutuhan mencadangkan foto asli. Proses lokal tidak mencegah unggahan atau sinkronisasi yang dilakukan pengguna melalui layanan lain.

## Kredit dan hak penggunaan

**Aplikasi Wildlitics: Brian Martin.** Model dasar dan pustaka tetap merupakan karya pengembang masing-masing, dengan sumber resmi tercantum pada tabel model. Kredit aplikasi tidak menyiratkan bahwa Brian Martin menciptakan seluruh model dasar atau memperoleh dukungan resmi pengembang model.

Repositori publik tidak berarti seluruh aplikasi, foto, logo, checklist, atau bobot model diberi lisensi sumber terbuka. Lisensi distribusi karya Wildlitics belum ditetapkan dalam repositori ini; tidak ada lisensi MIT, Apache, atau lisensi lain yang otomatis diberikan untuk seluruh aplikasi.

Sebelum mendistribusikan kode, bobot, atau executable, periksa lisensi setiap komponen dan versinya. Pencantuman kredit saja tidak menggantikan kewajiban lisensi, dan lisensi perangkat lunak tidak memberikan hak atas foto atau logo pengguna.

## Referensi metode

- Harris, Thompson, Childs, dan Sanderson (2010). *Automatic Storage and Analysis of Camera Trap Data*. [DOI](https://doi.org/10.1890/0012-9623-91.3.352).
- Ridout dan Linkie (2009). *Estimating overlap of daily activity patterns from camera trap data*. [DOI](https://doi.org/10.1198/jabes.2009.08038).
- [Camera Trap Data Package](https://camtrap-dp.tdwg.org/data/), acuan struktur data deployment, media, dan observasi.

Wildlitics bukan distribusi CameraSweet dan tidak mengklaim mereplikasi seluruh metodenya. Diagram aktivitas memakai implementasi deskriptif sederhana, bukan seluruh prosedur estimasi overlap atau pengujian statistik pada referensi.

Dokumentasi versi 2.3.3, diperbarui **6 Oktober 2026**.
