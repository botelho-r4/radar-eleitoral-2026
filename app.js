const DATA = {
  presidente: {
    label: "PRESIDENTE",
    cards: [
      [["Carlos Silva","PARTIDO A","38,4%","38.4"],["Mariana Santos","PARTIDO B","32,7%","32.7"],["Roberto Lima","PARTIDO C","18,6%","18.6"]],
      [["Ana Costa","PARTIDO B","42,1%","42.1"],["Paulo Mendes","PARTIDO A","28,9%","28.9"],["Fernanda Alves","PARTIDO D","15,3%","15.3"]],
      [["João Ribeiro","PARTIDO C","31,5%","31.5"],["Camila Duarte","PARTIDO A","27,8%","27.8"],["Eduardo Nunes","PARTIDO B","19,4%","19.4"]]
    ]
  },
  governador: {
    label: "GOVERNADOR",
    cards: [
      [["Ana Costa","PARTIDO B","42,1%","42.1"],["Paulo Mendes","PARTIDO A","28,9%","28.9"],["Fernanda Alves","PARTIDO D","15,3%","15.3"]],
      [["Mariana Costa","PARTIDO A","44,2%","44.2"],["Lucas Martins","PARTIDO C","30,1%","30.1"],["Rafael Souza","PARTIDO B","17,8%","17.8"]],
      [["Carlos Mendes","PARTIDO C","36,8%","36.8"],["Juliana Alves","PARTIDO A","29,4%","29.4"],["Pedro Lima","PARTIDO D","21,2%","21.2"]]
    ]
  },
  senador: {
    label: "SENADOR",
    cards: [
      [["João Ribeiro","PARTIDO C","31,5%","31.5"],["Camila Duarte","PARTIDO A","27,8%","27.8"],["Eduardo Nunes","PARTIDO B","19,4%","19.4"]],
      [["Renato Alves","PARTIDO B","35,4%","35.4"],["Marcos Silva","PARTIDO A","30,8%","30.8"],["Beatriz Costa","PARTIDO C","20,7%","20.7"]],
      [["Helena Martins","PARTIDO A","34,1%","34.1"],["Daniel Rocha","PARTIDO C","29,5%","29.5"],["Tiago Souza","PARTIDO B","18,2%","18.2"]]
    ]
  },
  "deputado-federal": {
    label: "DEPUTADO FEDERAL",
    cards: [
      [["Mariana Santos","PARTIDO B","18,9%","18.9"],["Roberto Lima","PARTIDO C","16,7%","16.7"],["Carlos Silva","PARTIDO A","13,2%","13.2"]],
      [["Ana Costa","PARTIDO B","17,5%","17.5"],["Paulo Mendes","PARTIDO A","15,9%","15.9"],["Fernanda Alves","PARTIDO D","12,8%","12.8"]],
      [["João Ribeiro","PARTIDO C","16,1%","16.1"],["Camila Duarte","PARTIDO A","14,6%","14.6"],["Eduardo Nunes","PARTIDO B","11,9%","11.9"]]
    ]
  },
  "deputado-estadual": {
    label: "DEPUTADO ESTADUAL/DISTRITAL",
    cards: [
      [["Lucas Martins","PARTIDO C","14,8%","14.8"],["Beatriz Costa","PARTIDO A","13,2%","13.2"],["Rafael Souza","PARTIDO B","11,7%","11.7"]],
      [["Juliana Alves","PARTIDO A","15,6%","15.6"],["Pedro Lima","PARTIDO D","12,9%","12.9"],["Helena Martins","PARTIDO C","10,8%","10.8"]],
      [["Daniel Rocha","PARTIDO C","13,8%","13.8"],["Tiago Souza","PARTIDO B","12,1%","12.1"],["Renato Alves","PARTIDO A","9,9%","9.9"]]
    ]
  }
};

const updates = [
  ["18:42","SP","72,3%"],["18:40","MG","69,1%"],["18:37","PR","66,4%"],
  ["18:35","BA","58,7%"],["18:33","RJ","71,2%"],["18:31","RS","64,9%"],
  ["18:28","GO","61,5%"],["18:25","PE","55,4%"]
];

const icons = {
  presidente:"▥", governador:"♣", senador:"♟",
  "deputado-federal":"▥", "deputado-estadual":"▥"
};

let selectedCargo = "presidente";
let selectedUF = "Todas as UFs";
let selectedMunicipio = "Todos os municípios";
const municipioCache = {};

const UF_CODES = {
  AC: 12, AL: 27, AP: 16, AM: 13, BA: 29, CE: 23, DF: 53,
  ES: 32, GO: 52, MA: 21, MT: 51, MS: 50, MG: 31, PA: 15,
  PB: 25, PR: 41, PE: 26, PI: 22, RJ: 33, RN: 24, RS: 43,
  RO: 11, RR: 14, SC: 42, SP: 35, SE: 28, TO: 17
};

function setLocationCaption(local) {
  document.querySelector(".progress-caption").textContent =
    `312.845 de 456.789 seções • ${local}`;
}

function populateMunicipiosPlaceholder(text) {
  const select = document.getElementById("municipio");
  select.innerHTML = "";
  const option = document.createElement("option");
  option.textContent = text;
  option.value = text;
  option.selected = true;
  select.appendChild(option);
}

async function carregarMunicipios(uf, municipioParaSelecionar = "Todos os municípios") {
  const select = document.getElementById("municipio");

  if (!uf || uf === "Todas as UFs") {
    selectedMunicipio = "Todos os municípios";
    populateMunicipiosPlaceholder("Todos os municípios");
    setLocationCaption("Brasil");
    return;
  }

  populateMunicipiosPlaceholder("Carregando municípios...");
  select.disabled = true;

  try {
    let municipios = municipioCache[uf];

    if (!municipios) {
      const ufCode = UF_CODES[uf];
      if (!ufCode) throw new Error(`UF não mapeada: ${uf}`);

      const url = `https://servicodados.ibge.gov.br/api/v1/localidades/estados/${ufCode}/municipios?orderBy=nome`;
      const response = await fetch(url, { cache: "no-store" });
      if (!response.ok) throw new Error(`IBGE retornou HTTP ${response.status}`);

      const data = await response.json();
      municipios = data
        .map(item => ({ id: item.id, nome: item.nome }))
        .sort((a,b) => a.nome.localeCompare(b.nome, "pt-BR"));

      municipioCache[uf] = municipios;
    }

    select.innerHTML = "";

    const allOption = document.createElement("option");
    allOption.value = "Todos os municípios";
    allOption.textContent = "Todos os municípios";
    select.appendChild(allOption);

    municipios.forEach(m => {
      const option = document.createElement("option");
      option.value = m.nome;
      option.textContent = m.nome;
      option.dataset.ibge = m.id;
      select.appendChild(option);
    });

    const exists = municipios.some(m => m.nome === municipioParaSelecionar);
    selectedMunicipio = exists ? municipioParaSelecionar : "Todos os municípios";
    select.value = selectedMunicipio;

    setLocationCaption(
      selectedMunicipio === "Todos os municípios"
        ? uf
        : `${selectedMunicipio}/${uf}`
    );

  } catch (error) {
    console.error("Erro ao carregar municípios do IBGE:", error);
    populateMunicipiosPlaceholder("Não foi possível carregar municípios");
    selectedMunicipio = "Todos os municípios";
    setLocationCaption(uf);
    showToast("Não foi possível carregar os municípios agora");
  } finally {
    select.disabled = false;
  }
}

function renderPanel(id, title, rows) {
  document.getElementById(id).innerHTML = `
    <div class="section-title">
      <span>${icons[selectedCargo] || "▥"}</span>
      <span class="title-label">${title}</span>
      <em class="demo">DADOS DE DEMONSTRAÇÃO</em>
      <button class="panel-arrow" type="button" aria-label="Abrir detalhes">›</button>
    </div>
    ${rows.map((r,i) => `
      <div class="candidate">
        <span class="rank">${i+1}º</span>
        <span class="avatar">${r[0][0]}</span>
        <div>
          <div class="candidate-name">${r[0]}</div>
          <div class="party">${r[1]}</div>
        </div>
        <div>
          <div class="pct">${r[2]}</div>
          <div class="bar"><span style="width:${Math.min(parseFloat(r[3])*2,100)}%"></span></div>
        </div>
      </div>`).join("")}
    <button class="ranking" type="button" data-ranking="${title}">
      Ver ranking completo →
    </button>`;
}

function render() {
  const d = DATA[selectedCargo];

  const labels = selectedCargo === "presidente"
    ? ["PRESIDENTE","GOVERNADOR","SENADOR"]
    : [d.label,"DESTAQUES NACIONAIS","RANKING POR UF"];

  renderPanel("presidente-panel", labels[0], d.cards[0]);
  renderPanel("governador-panel", labels[1], d.cards[1]);
  renderPanel("senador-panel", labels[2], d.cards[2]);

  document.querySelectorAll(".nav-tabs button[data-cargo]").forEach(btn => {
    btn.classList.toggle("tab-active", btn.dataset.cargo === selectedCargo);
  });

  document.getElementById("uf").value = selectedUF;
}

function openRanking(title) {
  const modal = document.getElementById("ranking-modal");
  document.getElementById("modal-title").textContent = title;

  const all = [
    ...DATA[selectedCargo].cards[0],
    ...DATA[selectedCargo].cards[1],
    ...DATA[selectedCargo].cards[2]
  ]
  .sort((a,b) => parseFloat(b[3]) - parseFloat(a[3]))
  .slice(0,10);

  document.getElementById("modal-list").innerHTML = all.map((r,i) => `
    <div class="modal-row">
      <b>${i+1}º</b>
      <span class="avatar small">${r[0][0]}</span>
      <span><strong>${r[0]}</strong><small>${r[1]}</small></span>
      <b class="modal-pct">${r[2]}</b>
    </div>`).join("");

  modal.classList.add("open");
}

function showToast(message) {
  const t = document.querySelector(".toast");
  t.textContent = message;
  t.classList.add("show");
  clearTimeout(window.__toast);
  window.__toast = setTimeout(() => t.classList.remove("show"), 1800);
}

const modal = document.createElement("div");
modal.id = "ranking-modal";
modal.className = "modal";
modal.innerHTML = `
  <div class="modal-box">
    <button id="modal-close" class="modal-close" type="button">×</button>
    <h2 id="modal-title">Ranking</h2>
    <p>Dados de demonstração — serão substituídos pelos dados oficiais do TSE.</p>
    <div id="modal-list"></div>
  </div>`;
document.body.appendChild(modal);

const toast = document.createElement("div");
toast.className = "toast";
document.body.appendChild(toast);

document.querySelectorAll(".nav-tabs button[data-cargo]").forEach(btn => {
  btn.addEventListener("click", () => {
    selectedCargo = btn.dataset.cargo;
    render();
    document.querySelector(".container").scrollIntoView({ behavior:"smooth", block:"start" });
  });
});

document.querySelector(".home").addEventListener("click", async () => {
  selectedCargo = "presidente";
  selectedUF = "Todas as UFs";
  selectedMunicipio = "Todos os municípios";
  document.getElementById("uf").value = selectedUF;
  document.getElementById("municipio").value = selectedMunicipio;
  render();
  await carregarMunicipios(selectedUF);
  showToast("Visão nacional restaurada");
});

document.getElementById("uf").addEventListener("change", async e => {
  selectedUF = e.target.value;
  selectedMunicipio = "Todos os municípios";
  render();
  await carregarMunicipios(selectedUF);
  showToast(
    selectedUF === "Todas as UFs"
      ? "Todas as UFs selecionadas"
      : `Municípios de ${selectedUF} carregados`
  );
});

document.getElementById("municipio").addEventListener("change", e => {
  selectedMunicipio = e.target.value;
  const local = selectedMunicipio === "Todos os municípios"
    ? (selectedUF === "Todas as UFs" ? "Brasil" : selectedUF)
    : `${selectedMunicipio}/${selectedUF}`;

  setLocationCaption(local);
  showToast(`Filtro: ${local}`);
});

document.addEventListener("click", e => {
  const ranking = e.target.closest("[data-ranking]");
  if (ranking) openRanking(ranking.dataset.ranking);

  const arrow = e.target.closest(".panel-arrow");
  if (arrow) openRanking(arrow.parentElement.querySelector(".title-label").textContent);

  const state = e.target.closest(".state");
  if (state) {
    const uf = state.textContent.trim();
    if (UF_CODES[uf]) {
      selectedUF = uf;
      selectedMunicipio = "Todos os municípios";
      document.getElementById("uf").value = selectedUF;
      render();
      carregarMunicipios(selectedUF);
      showToast(`Carregando municípios de ${selectedUF}`);
    }
  }

  if (e.target.id === "modal-close" || e.target === modal) modal.classList.remove("open");
});

document.querySelector(".updates .section-title a").addEventListener("click", e => {
  e.preventDefault();
  showToast("Histórico de atualizações — módulo demonstrativo");
});

document.querySelectorAll("footer a").forEach(a => {
  a.addEventListener("click", e => {
    e.preventDefault();
    showToast(a.textContent + " — módulo demonstrativo");
  });
});

document.getElementById("updates").innerHTML = updates.map(u => `
  <div class="update">
    <span class="time">${u[0]}</span>
    <span class="uf-name">⌖ ${u[1]}</span>
    <span><b class="up">↑</b> Seções totalizadas ${u[2]}</span>
  </div>`).join("");

const style = document.createElement("style");
style.textContent = `
  .candidate-panel .section-title:after{display:none}
  .panel-arrow{margin-left:auto;border:0;background:none;color:#214e93;font-size:28px;line-height:1;cursor:pointer}
  .ranking{border:0;background:none;cursor:pointer;font-family:inherit}
  #municipio:disabled{opacity:.65;cursor:wait}
  .modal{position:fixed;inset:0;background:rgba(4,18,43,.58);display:none;align-items:center;justify-content:center;padding:20px;z-index:50}
  .modal.open{display:flex}
  .modal-box{width:min(560px,100%);max-height:80vh;overflow:auto;background:#fff;border-radius:14px;padding:24px;box-shadow:0 25px 70px rgba(0,0,0,.25);position:relative}
  .modal-box h2{margin:0;color:#12335f}.modal-box p{color:#68768d;font-size:12px}
  .modal-close{position:absolute;right:14px;top:10px;border:0;background:none;font-size:30px;color:#5c6b82;cursor:pointer}
  .modal-row{display:grid;grid-template-columns:38px 40px 1fr auto;gap:10px;align-items:center;padding:10px 0;border-bottom:1px solid #e7edf5}
  .avatar.small{width:34px;height:34px}.modal-row span:not(.avatar){display:flex;flex-direction:column}.modal-row small{color:#718099;margin-top:2px}.modal-pct{color:#0d4f9e}
  .toast{position:fixed;left:50%;bottom:24px;transform:translate(-50%,20px);background:#071d43;color:#fff;padding:11px 18px;border-radius:9px;box-shadow:0 8px 30px rgba(0,0,0,.2);opacity:0;pointer-events:none;transition:.2s;z-index:60;font-size:13px}
  .toast.show{opacity:1;transform:translate(-50%,0)}
  .nav-tabs button:focus-visible,.nav-tabs select:focus-visible,.ranking:focus-visible,.panel-arrow:focus-visible{outline:3px solid rgba(20,105,215,.25);outline-offset:2px}
`;
document.head.appendChild(style);

render();
carregarMunicipios(selectedUF);
