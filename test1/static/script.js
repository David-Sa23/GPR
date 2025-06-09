function iniciarCaptura() {
    fetch('/start')
        .then(() => {
            document.getElementById('status').innerText = "Captura iniciada...";
            atualizar();
        });
}

function atualizar() {
    fetch('/latest')
        .then(res => res.json())
        .then(data => {
            if (data && data.size) {
                const status = document.getElementById('status');
                const isAnomaly = data.prediction === 1;
                status.innerHTML = `
                    📦 Tamanho: ${data.size}<br>
                    📡 Protocolo: ${data.protocol}<br>
                    ⏱ Freq: ${data.frequency} pkt/s<br>
                    Resultado: <span class="${isAnomaly ? 'anomalo' : 'normal'}">
                        ${isAnomaly ? '🔴 Anómalo' : '🟢 Normal'}
                    </span>
                `;
            }
            setTimeout(atualizar, 1000);
        });
}
