const API_URL = "carbon-footprint-production-9c64.up.railway.app";

let hasilCarbon = null;
let namaUser = null;
let riwayatChat = [];

async function hitungCarbon() {
    const nama = document.getElementById("nama").value;
    const listrik = document.getElementById("listrik").value;
    const air = document.getElementById("air").value;
    const transportasi = document.getElementById("transportasi").value;
    const sampah = document.getElementById("sampah").value;

    if (!nama || !listrik || !air || !transportasi || !sampah) {
        alert("Semua field harus diisi ya! 😊");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/hitung`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                nama: nama,
                listrik_kwh: parseFloat(listrik),
                air_liter: parseFloat(air),
                transportasi_km: parseFloat(transportasi),
                sampah_kg: parseFloat(sampah)
            })
        });

        const data = await response.json();
        localStorage.setItem("hasilCarbon", JSON.stringify(data));
        window.location.href = "/frontend/result.html";

    } catch (error) {
        alert("Gagal konek ke server. Pastikan backend sudah jalan! 🔧");
    }
}

function tampilkanHasil() {
    const data = JSON.parse(localStorage.getItem("hasilCarbon"));
    if (!data) return;

    hasilCarbon = data.hasil;
    namaUser = data.nama;

    document.getElementById("salam-nama").textContent = `Hai, ${data.nama}! 👋`;
    document.getElementById("total-co2").textContent = data.hasil.total.toFixed(1);

    const levelBadge = document.getElementById("level-badge");
    const levelText = {
        "rendah": "✅ Level Rendah — Keren banget!",
        "sedang": "⚠️ Level Sedang — Masih bisa lebih baik!",
        "tinggi": "🔴 Level Tinggi — Yuk kita kurangi!"
    };
    levelBadge.textContent = levelText[data.level];
    levelBadge.className = `level-badge level-${data.level}`;

    document.getElementById("jumlah-pohon").textContent = `${data.metafora.pohon} pohon`;
    document.getElementById("biaya-rupiah").textContent = `Rp${data.metafora.rupiah.toLocaleString()}`;

    buatGrafikPie(data.hasil);
    buatGrafikBar(data.hasil);

    if (data.level === "tinggi" && data.saran) {
        document.getElementById("saran-card").style.display = "block";
        document.getElementById("saran-content").textContent = data.saran;
    }

    document.getElementById("chatbot-card").style.display = "block";

    const chatMessages = document.getElementById("chat-messages");
    const welcomeBubble = document.createElement("div");
    welcomeBubble.className = "bubble bot";
    welcomeBubble.textContent = `Halo ${data.nama}! Aku EcoBot 🌿 Ada yang mau kamu tanyakan soal carbon footprint kamu?`;
    chatMessages.appendChild(welcomeBubble);
}

function buatGrafikPie(hasil) {
    const ctx = document.getElementById("chart-pie").getContext("2d");
    const labels = ["⚡ Listrik", "💧 Air", "🚗 Transportasi", "🗑️ Sampah"];
    const values = [
        hasil.listrik.toFixed(1),
        hasil.air.toFixed(1),
        hasil.transportasi.toFixed(1),
        hasil.sampah.toFixed(1)
    ];
    const colors = ["#ff9800", "#2196f3", "#9c27b0", "#e53935"];

    new Chart(ctx, {
        type: "pie",
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: false,
            plugins: { legend: { display: false } }
        }
    });

    const legend = document.getElementById("pie-legend");
    labels.forEach((label, i) => {
        const item = document.createElement("div");
        item.className = "pie-item";
        item.innerHTML = `
            <div class="pie-dot" style="background:${colors[i]}"></div>
            <span class="pie-name">${label}</span>
            <span class="pie-val">${values[i]} kg</span>
        `;
        legend.appendChild(item);
    });
}

function buatGrafikBar(hasil) {
    const ctx = document.getElementById("chart-bar").getContext("2d");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["⚡ Listrik", "💧 Air", "🚗 Transportasi", "🗑️ Sampah"],
            datasets: [
                {
                    label: "Kamu (kg CO₂)",
                    data: [
                        hasil.listrik.toFixed(1),
                        hasil.air.toFixed(1),
                        hasil.transportasi.toFixed(1),
                        hasil.sampah.toFixed(1)
                    ],
                    backgroundColor: "rgba(100, 190, 140, 0.8)",
                    borderRadius: 6
                },
                {
                    label: "Rata-rata Indonesia (kg CO₂)",
                    data: [87, 3, 63, 12.5],
                    backgroundColor: "rgba(150, 150, 150, 0.35)",
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: { color: "#88aa99", font: { size: 11 } }
                }
            },
            scales: {
                x: { ticks: { color: "#88aa99" }, grid: { color: "rgba(120,180,140,0.08)" } },
                y: { ticks: { color: "#88aa99" }, grid: { color: "rgba(120,180,140,0.08)" } }
            }
        }
    });
}

async function kirimChat() {
    const input = document.getElementById("chat-input");
    const pesan = input.value.trim();
    if (!pesan) return;

    tambahBubble(pesan, "user");
    input.value = "";
    riwayatChat.push({ role: "user", content: pesan });

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                nama: namaUser,
                hasil_carbon: hasilCarbon,
                riwayat_chat: riwayatChat
            })
        });

        const data = await response.json();
        tambahBubble(data.balasan, "bot");
        riwayatChat.push({ role: "assistant", content: data.balasan });

    } catch (error) {
        tambahBubble("Maaf, ada error nih! 😅", "bot");
    }
}

function tambahBubble(pesan, role) {
    const container = document.getElementById("chat-messages");
    const bubble = document.createElement("div");
    bubble.className = `bubble ${role}`;
    bubble.textContent = pesan;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
}

const chatInput = document.getElementById("chat-input");
if (chatInput) {
    chatInput.addEventListener("keypress", function(e) {
        if (e.key === "Enter") kirimChat();
    });
}

if (document.getElementById("total-co2")) {
    tampilkanHasil();
}