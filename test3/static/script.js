let intervalId = null;
let chart = null;

function iniciarCaptura() {
    fetch('/start')
        .then(() => {
            if (intervalId) clearInterval(intervalId);
            intervalId = setInterval(atualizar, 1000);
        });
}

function pararCaptura() {
    fetch('/stop')
        .then(() => {
            if (intervalId) clearInterval(intervalId);
        });
}

function atualizar() {
    fetch('/latest')
        .then(res => res.json())
        .then(data => {
            const lista = document.getElementById('packetList');
            lista.innerHTML = '';

            if (data.length === 0) {
                lista.innerHTML = '<p><em>Nenhum pacote ainda...</em></p>';
                return;
            }

            data.slice().reverse().forEach(pacote => {
                const div = document.createElement('div');
                div.className = 'packet';
                div.innerHTML = `
                    📥 <strong>${pacote.src}</strong> → <strong>${pacote.dst}</strong><br>
                    📦 Tamanho: ${pacote.size} bytes | Protocolo: ${pacote.protocol} | Freq: ${pacote.frequency} pkt/s<br>
                    Resultado: <span class="${pacote.prediction === 1 ? 'anomalo' : 'normal'}">
                        ${pacote.prediction === 1 ? '🔴 Anómalo' : '🟢 Normal'}
                    </span>
                `;
                lista.appendChild(div);
            });

            // Atualizar gráfico, se visível
            if (chart) {
                const ultimos = data.slice(-20);
                const labels = ultimos.map((_, i) => `${i + 1}`);
                const tamanhos = ultimos.map(p => p.size);
                const freq = ultimos.map(p => p.frequency);
                const percent_anom = ultimos.map((_, i) => {
                    const slice = ultimos.slice(Math.max(0, i - 9), i + 1);
                    const anom = slice.filter(p => p.prediction === 1).length;
                    return Math.round((anom / slice.length) * 100);
                });

                chart.data.labels = labels;
                chart.data.datasets[0].data = tamanhos;
                chart.data.datasets[1].data = freq;
                chart.data.datasets[2].data = percent_anom;
                chart.update();
            }
        });
}

function carregarMetricas() {
    fetch('/metrics')
        .then(res => res.json())
        .then(data => {
            document.getElementById('acc').innerText = data.accuracy;
            document.getElementById('prec').innerText = data.precision;
            document.getElementById('rec').innerText = data.recall;
            document.getElementById('f1').innerText = data.f1;
        });
}

function mostrarGrafico() {
    const canvas = document.getElementById('graficoPacotes');
    canvas.style.display = 'block';
    if (!chart) criarGrafico();
}

function criarGrafico() {
    const ctx = document.getElementById('graficoPacotes').getContext('2d');
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Tamanho (bytes)',
                    data: [],
                    borderColor: 'blue',
                    fill: false,
                    tension: 0.3,
                },
                {
                    label: 'Frequência (pkt/s)',
                    data: [],
                    borderColor: 'orange',
                    fill: false,
                    tension: 0.3,
                },
                {
                    label: '% Anómalos (últimos 10)',
                    data: [],
                    borderColor: 'red',
                    fill: false,
                    tension: 0.3,
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Tempo (últimos 100 pacotes)'
                    }
                },
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

window.onload = () => {
    carregarMetricas();
}
