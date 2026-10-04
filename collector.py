#!/usr/bin/env python3
"""
Radar Eleitoral 2026 — Coletor V1

Consome a infraestrutura oficial do TSE.
Não depende de scraping da interface do Portal de Resultados.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CACHE = DATA / ".cache"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"

BASE_URL = os.getenv("TSE_BASE_URL", "https://resultados.tse.jus.br").rstrip("/")
ENV = os.getenv("TSE_ENV", "oficial")
TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))

CONFIG_URL = f"{BASE_URL}/{ENV}/comum/config/ele-c.json"

UFS = [
    "ac","al","ap","am","ba","ce","df","es","go","ma","mt","ms","mg",
    "pa","pb","pr","pe","pi","rj","rn","rs","ro","rr","sc","sp","se","to"
]

CARGOS = {
    "presidente": "0001",
    "governador": "0003",
    "senador": "0005",
    "deputado_federal": "0006",
    "deputado_estadual": "0007",
    "deputado_distrital": "0008",
}

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Radar-Eleitoral-2026/1.0 (+https://github.com/botelho-r4/radar-eleitoral-2026)"
})


def ensure_dirs() -> None:
    for p in (DATA, CACHE, RAW, PROCESSED):
        p.mkdir(parents=True, exist_ok=True)


def load_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    tmp.replace(path)


def fetch_json(url: str, cache_name: str | None = None) -> tuple[int, Any | None, dict]:
    """
    Busca JSON usando ETag/Last-Modified quando possível.
    Retorna (status, payload, headers).
    """
    headers = {}
    meta_path = CACHE / f"{cache_name}.meta.json" if cache_name else None

    if meta_path and meta_path.exists():
        meta = load_json_file(meta_path, {})
        if meta.get("etag"):
            headers["If-None-Match"] = meta["etag"]
        if meta.get("last_modified"):
            headers["If-Modified-Since"] = meta["last_modified"]

    response = SESSION.get(url, headers=headers, timeout=TIMEOUT)

    if response.status_code == 304:
        return 304, None, dict(response.headers)

    response.raise_for_status()

    if meta_path:
        save_json(meta_path, {
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
            "url": url,
            "saved_at": int(time.time())
        })

    return response.status_code, response.json(), dict(response.headers)


def get_config() -> dict:
    status, payload, _ = fetch_json(CONFIG_URL, "ele-c")
    if not payload:
        raise RuntimeError(f"Não foi possível obter ele-c.json: HTTP {status}")
    save_json(RAW / "ele-c.json", payload)
    return payload


def find_2026_elections(config: dict) -> list[dict]:
    elections = []
    for pleito in config.get("pl", []):
        if pleito.get("c") != "ele2026":
            continue
        for election in pleito.get("e", []):
            elections.append({
                "pleito": pleito.get("cd"),
                "pleito_nome": pleito.get("cdpr"),
                "eleicao": election.get("cd"),
                "eleicao_2_turno": election.get("cdt2"),
                "nome": election.get("nm"),
                "turno": election.get("t"),
                "tipo": election.get("tp"),
                "abrangencias": election.get("abr", [])
            })
    return elections


def choose_elections(config: dict, turno: str) -> list[dict]:
    elections = find_2026_elections(config)
    if turno == "auto":
        # A configuração oficial informa o 1º turno atual e, quando existente,
        # o código do eventual 2º turno em cdt2.
        return [e for e in elections if str(e["turno"]) == "1"]
    wanted = str(turno)
    return [e for e in elections if str(e["turno"]) == wanted]


def url_for(election_code: str, uf: str, filename: str) -> str:
    # ciclo oficial para as Eleições Gerais 2026
    return f"{BASE_URL}/{ENV}/ele2026/{election_code}/dados/{uf}/{filename}"


def collect_tracking(election_code: str, uf: str, kind: str) -> dict | None:
    filename = f"{uf}-e{int(election_code):06d}-{kind}.json"
    url = url_for(election_code, uf, filename)
    try:
        status, payload, _ = fetch_json(url, f"{uf}-e{election_code}-{kind}")
        if payload:
            save_json(RAW / "tracking" / filename, payload)
        return payload
    except requests.HTTPError as exc:
        # 404 pode significar que o arquivo ainda não foi gerado.
        if getattr(exc.response, "status_code", None) == 404:
            return None
        raise


def collect_ea20(election_code: str, uf: str, cargo_code: str) -> dict | None:
    filename = f"{uf}-c{cargo_code}-e{int(election_code):06d}-u.json"
    url = url_for(election_code, uf, filename)
    try:
        status, payload, _ = fetch_json(url, f"{uf}-c{cargo_code}-e{election_code}-u")
        if payload:
            save_json(RAW / "ea20" / filename, payload)
        return payload
    except requests.HTTPError as exc:
        if getattr(exc.response, "status_code", None) == 404:
            return None
        raise


def collect_ea10(election_code: str, abrangencia: str, cargo_code: str) -> dict | None:
    filename = f"{abrangencia}-c{cargo_code}-e{int(election_code):06d}-e.json"
    url = url_for(election_code, abrangencia, filename)
    try:
        status, payload, _ = fetch_json(url, f"ea10-{abrangencia}-c{cargo_code}-e{election_code}")
        if payload:
            save_json(RAW / "ea10" / filename, payload)
        return payload
    except requests.HTTPError as exc:
        if getattr(exc.response, "status_code", None) == 404:
            return None
        raise


def normalize_candidate(c: dict) -> dict:
    return {
        "numero": c.get("n"),
        "sequencial": c.get("sqcand"),
        "nome": c.get("nm"),
        "nome_urna": c.get("nmu"),
        "partido": c.get("sgp"),
        "coligacao": c.get("com"),
        "votos": c.get("vap"),
        "ordem": c.get("seq"),
        "suplentes_vice": [
            {
                "tipo": v.get("tp"),
                "sequencial": v.get("sqcand"),
                "nome": v.get("nm"),
                "nome_urna": v.get("nmu"),
                "partido": v.get("sgp")
            }
            for v in c.get("vs", [])
        ]
    }


def normalize_ea20(payload: dict, election_code: str, uf: str, cargo: str) -> dict:
    result = {
        "fonte": "TSE",
        "arquivo": "EA20",
        "eleicao": int(election_code),
        "abrangencia": uf,
        "cargo": cargo,
        "gerado_em": payload.get("dg"),
        "hora_geracao": payload.get("hg"),
        "id_geracao": payload.get("idg"),
        "turno": payload.get("t"),
        "fase": payload.get("f"),
        "dados": []
    }

    for abr in payload.get("abr", []):
        result["dados"].append({
            "tipo_abrangencia": abr.get("tpabr"),
            "codigo": abr.get("cdabr"),
            "nome": abr.get("nmabr"),
            "total_votos": abr.get("tvap"),
            "secoes": {
                "total": abr.get("s"),
                "totalizadas": abr.get("st"),
                "percentual": abr.get("pst")
            },
            "votos_brancos": abr.get("vb"),
            "votos_nulos": abr.get("vn"),
            "comparecimento": abr.get("cc"),
            "abstencoes": abr.get("a"),
            "candidatos": [normalize_candidate(c) for c in abr.get("cand", [])]
        })

    return result


def build_index(collected: list[dict]) -> dict:
    return {
        "projeto": "Radar Eleitoral 2026",
        "versao_coletor": "1.0.0",
        "fonte": "TSE",
        "base_url": BASE_URL,
        "atualizado_em_epoch": int(time.time()),
        "arquivos": collected
    }


def run(turno: str) -> int:
    ensure_dirs()
    config = get_config()
    elections = choose_elections(config, turno)

    if not elections:
        raise RuntimeError("Nenhuma eleição 2026 encontrada no ele-c.json.")

    collected = []

    for election in elections:
        election_code = str(election["eleicao"])
        # 6257 = Presidente; 6259 = cargos estaduais/federais.
        if election_code == "6257":
            cargo_list = [("presidente", CARGOS["presidente"])]
            abrangencias = ["br"]
        elif election_code == "6259":
            cargo_list = [
                ("governador", CARGOS["governador"]),
                ("senador", CARGOS["senador"]),
                ("deputado_federal", CARGOS["deputado_federal"]),
                ("deputado_estadual", CARGOS["deputado_estadual"]),
                ("deputado_distrital", CARGOS["deputado_distrital"]),
            ]
            abrangencias = UFS
        else:
            continue

        # Acompanhamento Brasil/UF
        for uf in abrangencias:
            collect_tracking(election_code, uf, "ab")

        # EA20
        for cargo, cargo_code in cargo_list:
            # Deputado distrital existe apenas no DF; deputado estadual não é cargo do DF.
            if cargo == "deputado_distrital":
                target_ufs = ["df"]
            elif cargo == "deputado_estadual":
                target_ufs = [u for u in UFS if u != "df"]
            else:
                target_ufs = abrangencias

            for uf in target_ufs:
                payload = collect_ea20(election_code, uf, cargo_code)
                if payload:
                    normalized = normalize_ea20(payload, election_code, uf, cargo)
                    out = PROCESSED / f"{uf}-{cargo}-turno{election.get('turno')}.json"
                    save_json(out, normalized)
                    collected.append({
                        "tipo": "EA20",
                        "cargo": cargo,
                        "uf": uf,
                        "arquivo": str(out.relative_to(ROOT))
                    })

        # EA10: somente cargos oficialmente previstos nesse arquivo.
        ea10_cargos = [
            ("governador", CARGOS["governador"]),
            ("senador", CARGOS["senador"]),
            ("deputado_federal", CARGOS["deputado_federal"]),
        ]
        for cargo, cargo_code in ea10_cargos:
            payload = collect_ea10(election_code, "br", cargo_code)
            if payload:
                save_json(
                    PROCESSED / f"eleitos-{cargo}-turno{election.get('turno')}.json",
                    payload
                )
                collected.append({
                    "tipo": "EA10",
                    "cargo": cargo,
                    "abrangencia": "br"
                })

    save_json(PROCESSED / "radar-index.json", build_index(collected))
    save_json(PROCESSED / "election-config.json", config)

    print(f"Coleta concluída. Arquivos processados: {len(collected)}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--turno",
        choices=["auto", "1", "2"],
        default="auto",
        help="Turno a coletar. 'auto' usa o 1º turno disponível na configuração."
    )
    args = parser.parse_args()

    try:
        raise SystemExit(run(args.turno))
    except KeyboardInterrupt:
        print("Interrompido.")
        raise SystemExit(130)
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)
