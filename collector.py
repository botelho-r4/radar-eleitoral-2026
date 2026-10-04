#!/usr/bin/env python3
"""
Radar Eleitoral 2026 - Coletor V3

Coleta dados públicos do TSE a partir do ele-c.json oficial.
Os códigos de eleição e o ciclo são descobertos dinamicamente.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import requests


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BRASILIA = timezone(timedelta(hours=-3))

DATAS_INICIO_DIVULGACAO = {
    (2026, 10, 4),
    (2026, 10, 25),
}


def divulgacao_liberada() -> bool:
    """
    Impede consultas aos arquivos de resultados antes das 17h
    nas datas oficiais de divulgação dos resultados.
    """

    agora = datetime.now(BRASILIA)

    if (agora.year, agora.month, agora.day) in DATAS_INICIO_DIVULGACAO:

        if agora.hour < 17:

            print(
                "[INFO] Divulgação dos resultados ainda não começou. "
                f"Horário de Brasília: {agora:%d/%m/%Y %H:%M:%S}. "
                "Próxima liberação: 17:00."
            )

            return False

    return True


BASE_URL = os.getenv(
    "TSE_BASE_URL",
    "https://resultados.tse.jus.br"
).rstrip("/")

ENV = os.getenv(
    "TSE_ENV",
    "oficial"
)

CONFIG_URL = (
    f"{BASE_URL}/{ENV}/comum/config/ele-c.json"
)

ROOT = Path(__file__).resolve().parent

LOCAL_CONFIG = (
    ROOT / "config" / "settings.json"
)

OUTPUT_DIR = (
    ROOT / "data" / "processed"
)


UFS = [
    "ac", "al", "ap", "am", "ba", "ce", "df",
    "es", "go", "ma", "mt", "ms", "mg", "pa",
    "pb", "pr", "pe", "pi", "rj", "rn", "rs",
    "ro", "rr", "sc", "sp", "se", "to"
]


CARGOS = {
    "1": "presidente",
    "3": "governador",
    "5": "senador",
    "6": "deputado_federal",
    "7": "deputado_estadual",
    "8": "deputado_distrital"
}


# Evita consultas de arquivos que não existem.
UF_POR_CARGO = {
    "3": UFS,
    "5": UFS,
    "6": UFS,
    "7": [
        uf for uf in UFS
        if uf != "df"
    ],
    "8": ["df"]
}


# ============================================================
# SESSÃO HTTP
# ============================================================

SESSION = requests.Session()

SESSION.headers.update({
    "User-Agent": (
        "Radar-Eleitoral-2026/3.0 "
        "(consumo de dados publicos do TSE)"
    ),
    "Accept": "application/json"
})


# ============================================================
# FUNÇÕES BÁSICAS
# ============================================================

def carregar_config_local() -> dict[str, Any]:
    """Carrega settings.json, se existir."""

    if not LOCAL_CONFIG.exists():
        return {}

    try:

        return json.loads(
            LOCAL_CONFIG.read_text(
                encoding="utf-8"
            )
        )

    except Exception as exc:

        print(
            f"[AVISO] Não foi possível ler "
            f"{LOCAL_CONFIG}: {exc}"
        )

        return {}


def obter_json(
    url: str,
    tentativas: int = 3
) -> Any | None:
    """
    Consulta um JSON do TSE com tratamento de erros.

    404 não gera nova tentativa, pois o TSE alerta que múltiplos
    404 podem provocar bloqueio temporário.
    """

    for tentativa in range(
        1,
        tentativas + 1
    ):

        try:

            resposta = SESSION.get(
                url,
                timeout=20
            )

            if resposta.status_code == 200:

                return resposta.json()

            if resposta.status_code == 404:

                print(
                    f"[404] {url}"
                )

                return None

            if resposta.status_code in (
                429,
                500,
                502,
                503,
                504
            ):

                espera = min(
                    10,
                    tentativa * 2
                )

                print(
                    f"[HTTP {resposta.status_code}] "
                    f"tentativa {tentativa}/{tentativas} "
                    f"- aguardando {espera}s"
                )

                time.sleep(espera)

                continue

            print(
                f"[HTTP {resposta.status_code}] "
                f"{url}"
            )

            return None

        except requests.RequestException as exc:

            if tentativa == tentativas:

                print(
                    f"[ERRO] Falha ao acessar "
                    f"{url}: {exc}"
                )

                return None

            time.sleep(tentativa)

    return None


# ============================================================
# CONFIGURAÇÃO OFICIAL DO TSE
# ============================================================

def obter_config_tse() -> dict[str, Any]:

    print(
        "[INFO] Consultando configuração oficial:\n"
        f"{CONFIG_URL}"
    )

    config = obter_json(
        CONFIG_URL
    )

    if not isinstance(
        config,
        dict
    ):

        raise RuntimeError(
            "Não foi possível obter "
            "o ele-c.json oficial."
        )

    return config


def localizar_ele2026(
    config: dict[str, Any]
) -> dict[str, Any]:

    for pleito in config.get(
        "pl",
        []
    ):

        if pleito.get("c") == "ele2026":

            return pleito

    raise RuntimeError(
        "O ele-c.json não contém "
        "o ciclo ele2026."
    )


# ============================================================
# ELEIÇÃO / TURNO
# ============================================================

def selecionar_eleicoes(
    pleito: dict[str, Any],
    turno: str
) -> list[dict[str, Any]]:

    eleicoes = pleito.get(
        "e",
        []
    )

    if not eleicoes:

        raise RuntimeError(
            "Nenhuma eleição foi encontrada."
        )

    if turno == "auto":

        # Enquanto somente o 1º turno existir,
        # será selecionado o 1º turno.
        #
        # Quando o TSE publicar o 2º turno no ele-c.json,
        # ele será automaticamente selecionado.

        maior_turno = max(
            int(e.get("t", 1))
            for e in eleicoes
        )

        selecionadas = [
            e
            for e in eleicoes
            if int(e.get("t", 1))
            == maior_turno
        ]

    else:

        turno_numero = int(
            turno
        )

        selecionadas = [
            e
            for e in eleicoes
            if int(e.get("t", 1))
            == turno_numero
        ]

    # O código 6261 corresponde ao Conselho Distrital
    # de Fernando de Noronha e não faz parte da coleta
    # principal do Radar Eleitoral 2026.

    selecionadas = [
        e
        for e in selecionadas
        if str(e.get("cd")) != "6261"
    ]

    if not selecionadas:

        raise RuntimeError(
            f"Não existe eleição publicada "
            f"para o turno {turno}."
        )

    return selecionadas


# ============================================================
# URLS
# ============================================================

def montar_url(
    pleito: dict[str, Any],
    eleicao: dict[str, Any],
    uf: str,
    arquivo: str
) -> str:

    ciclo = pleito.get(
        "c",
        "ele2026"
    )

    # IMPORTANTE:
    # O código da eleição no diretório NÃO recebe
    # preenchimento com zeros.
    #
    # Exemplo:
    # /ele2026/6257/dados/
    #
    # O preenchimento com zeros é usado somente
    # no nome dos arquivos.

    codigo_eleicao = str(
        eleicao["cd"]
    )

    return (
        f"{BASE_URL}/"
        f"{ENV}/"
        f"{ciclo}/"
        f"{codigo_eleicao}/"
        f"dados/"
        f"{uf}/"
        f"{arquivo}"
    )


def arquivo_acompanhamento(
    eleicao: dict[str, Any],
    uf: str
) -> str:

    codigo = str(
        eleicao["cd"]
    ).zfill(6)

    return (
        f"{uf}-e{codigo}-ab.json"
    )


def arquivo_ea20(
    eleicao: dict[str, Any],
    uf: str,
    cargo: str
) -> str:

    codigo_eleicao = str(
        eleicao["cd"]
    ).zfill(6)

    codigo_cargo = str(
        cargo
    ).zfill(4)

    return (
        f"{uf}-c{codigo_cargo}-"
        f"e{codigo_eleicao}-u.json"
    )


# ============================================================
# CARGOS DISPONÍVEIS
# ============================================================

def obter_cargos(
    eleicao: dict[str, Any]
) -> dict[str, str]:

    cargos = {}

    for abrangencia in eleicao.get(
        "abr",
        []
    ):

        for cargo in abrangencia.get(
            "cp",
            []
        ):

            codigo = str(
                cargo.get("cd")
            )

            if codigo in CARGOS:

                cargos[codigo] = (
                    CARGOS[codigo]
                )

    return cargos


# ============================================================
# ABRANGÊNCIAS
# ============================================================

def obter_abrangencias(
    codigo_cargo: str
) -> list[str]:

    # Presidente:
    # somente resultado nacional.

    if codigo_cargo == "1":

        return ["br"]

    # Cargos estaduais:
    # resultado por UF.

    if codigo_cargo in UF_POR_CARGO:

        return UF_POR_CARGO[
            codigo_cargo
        ]

    return []


# ============================================================
# EA14 / EA15
# ============================================================

def coletar_acompanhamento(
    pleito: dict[str, Any],
    eleicao: dict[str, Any]
) -> dict[str, Any]:

    resultado = {}

    # EA14 = Brasil
    # EA15 = UFs

    abrangencias = [
        "br"
    ] + UFS

    for uf in abrangencias:

        arquivo = (
            arquivo_acompanhamento(
                eleicao,
                uf
            )
        )

        url = montar_url(
            pleito,
            eleicao,
            uf,
            arquivo
        )

        dados = obter_json(
            url
        )

        if dados is not None:

            resultado[uf] = {
                "arquivo": arquivo,
                "url": url,
                "dados": dados
            }

        # Pequena pausa para não gerar rajada.

        time.sleep(
            0.05
        )

    return resultado


# ============================================================
# EA20
# ============================================================

def coletar_ea20(
    pleito: dict[str, Any],
    eleicao: dict[str, Any]
) -> dict[str, Any]:

    resultado = {}

    cargos = obter_cargos(
        eleicao
    )

    for codigo_cargo, nome_cargo in cargos.items():

        abrangencias = (
            obter_abrangencias(
                codigo_cargo
            )
        )

        for uf in abrangencias:

            arquivo = arquivo_ea20(
                eleicao,
                uf,
                codigo_cargo
            )

            url = montar_url(
                pleito,
                eleicao,
                uf,
                arquivo
            )

            dados = obter_json(
                url
            )

            if dados is not None:

                chave = (
                    f"{nome_cargo}:{uf}"
                )

                resultado[chave] = {
                    "cargo_codigo": codigo_cargo,
                    "cargo": nome_cargo,
                    "uf": uf,
                    "arquivo": arquivo,
                    "url": url,
                    "dados": dados
                }

            time.sleep(
                0.05
            )

    return resultado


# ============================================================
# SAÍDA PROCESSADA
# ============================================================

def salvar_resultado(
    pleito: dict[str, Any],
    eleicoes: list[dict[str, Any]],
    acompanhamento: dict[str, Any],
    resultados: dict[str, Any]
) -> None:

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    agora = datetime.now(
        timezone.utc
    ).isoformat()

    dados = {
        "projeto": "Radar Eleitoral 2026",
        "versao_coletor": "V3",
        "fonte": "TSE",
        "gerado_em_utc": agora,

        "configuracao": {
            "base_url": BASE_URL,
            "ambiente": ENV,
            "ciclo": pleito.get("c"),
            "pleito": pleito.get("cd"),
            "pleito_pai": pleito.get("cdpr"),
            "data": pleito.get("dt")
        },

        "eleicoes": [
            {
                "codigo": e.get("cd"),
                "codigo_2_turno": e.get("cdt2"),
                "turno": e.get("t"),
                "nome": e.get("nm"),
                "tipo": e.get("tp"),
                "cargos": obter_cargos(e)
            }
            for e in eleicoes
        ],

        "acompanhamento": acompanhamento,

        "resultados_ea20": resultados
    }

    arquivo_latest = (
        OUTPUT_DIR / "latest.json"
    )

    arquivo_latest.write_text(
        json.dumps(
            dados,
            ensure_ascii=False,
            separators=(",", ":")
        ),
        encoding="utf-8"
    )

    status = {
        "projeto": "Radar Eleitoral 2026",
        "versao_coletor": "V3",
        "gerado_em_utc": agora,
        "fonte": "TSE",

        "eleicoes": [
            e.get("cd")
            for e in eleicoes
        ],

        "arquivos_acompanhamento": sum(
            len(v)
            for v in acompanhamento.values()
        ),

        "arquivos_ea20": sum(
            len(v)
            for v in resultados.values()
        )
    }

    (
        OUTPUT_DIR / "status.json"
    ).write_text(
        json.dumps(
            status,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        f"[OK] Resultado salvo em "
        f"{arquivo_latest}"
    )


# ============================================================
# EXECUÇÃO
# ============================================================

def executar(
    turno: str
) -> int:

    carregar_config_local()

    config = obter_config_tse()

    pleito = localizar_ele2026(
        config
    )

    # Impede qualquer consulta aos arquivos de
    # resultados antes do início oficial da divulgação.

    if not divulgacao_liberada():

        print(
            "[INFO] Coleta encerrada antes "
            "do início da divulgação."
        )

        return 0

    eleicoes = selecionar_eleicoes(
        pleito,
        turno
    )

    print()

    print(
        f"[OK] Pleito: "
        f"{pleito.get('cd')}"
    )

    print(
        f"[OK] Ciclo: "
        f"{pleito.get('c')}"
    )

    print(
        f"[OK] Turno selecionado: "
        f"{[e.get('t') for e in eleicoes]}"
    )

    acompanhamento = {}

    resultados = {}

    for eleicao in eleicoes:

        codigo = str(
            eleicao.get("cd")
        )

        nome = eleicao.get(
            "nm"
        )

        print()

        print(
            "=" * 60
        )

        print(
            f"[INFO] ELEIÇÃO {codigo}"
        )

        print(
            f"[INFO] {nome}"
        )

        print(
            f"[INFO] Cargos: "
            f"{obter_cargos(eleicao)}"
        )

        print(
            "[INFO] Coletando EA14/EA15..."
        )

        acompanhamento[codigo] = (
            coletar_acompanhamento(
                pleito,
                eleicao
            )
        )

        print(
            "[INFO] Coletando EA20..."
        )

        resultados[codigo] = (
            coletar_ea20(
                pleito,
                eleicao
            )
        )

        print(
            f"[OK] Eleição {codigo}: "
            f"{len(acompanhamento[codigo])} "
            f"acompanhamentos | "
            f"{len(resultados[codigo])} "
            f"EA20"
        )

    salvar_resultado(
        pleito,
        eleicoes,
        acompanhamento,
        resultados
    )

    print()

    print(
        "=" * 60
    )

    print(
        "[SUCESSO] Coleta concluída."
    )

    return 0


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Coletor oficial do TSE "
            "- Radar Eleitoral 2026"
        )
    )

    parser.add_argument(
        "--turno",
        choices=[
            "auto",
            "1",
            "2"
        ],
        default="auto",
        help=(
            "Turno da eleição. "
            "auto seleciona o maior turno publicado."
        )
    )

    args = parser.parse_args()

    try:

        return executar(
            args.turno
        )

    except KeyboardInterrupt:

        print(
            "\n[INFO] Execução interrompida."
        )

        return 130

    except Exception as exc:

        print(
            f"\n[FALHA] {exc}"
        )

        return 1


if __name__ == "__main__":

    sys.exit(
        main()
    )
