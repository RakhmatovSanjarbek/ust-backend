document.addEventListener('DOMContentLoaded', function() {
    const scannerBtn = document.getElementById('start-scanner');
    const readerDiv = document.getElementById('reader');
    const trackInput = document.getElementById('id_track_code');

    if (scannerBtn) {
        let html5QrCode;

        scannerBtn.addEventListener('click', () => {
            if (readerDiv.style.display === 'block') {
                if (html5QrCode) {
                    html5QrCode.stop();
                }
                readerDiv.style.display = 'none';
                scannerBtn.innerHTML = '📷 QR/Shtrix-kodni skanerlash';
                return;
            }
            readerDiv.style.display = 'block';
            scannerBtn.innerHTML = '❌ Skanerni to\'xtatish';

            html5QrCode = new Html5Qrcode("reader");
            html5QrCode.start(
                { facingMode: "environment" },
                {
                    fps: 15,
                    qrbox: { width: 250, height: 150 }
                },
                (decodedText) => {
                    trackInput.value = decodedText;
                    html5QrCode.stop();
                    readerDiv.style.display = 'none';
                    scannerBtn.innerHTML = '📷 QR/Shtrix-kodni skanerlash';
                    alert("Muvaffaqiyatli o'qildi: " + decodedText);
                },
                (errorMessage) => { /* Qidirish davom etmoqda... */ }
            ).catch((err) => {
                alert("Kameraga ruxsat berilmagan yoki xatolik yuz berdi.");
                console.error(err);
            });
        });
    }
});