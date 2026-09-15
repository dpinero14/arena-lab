"""Reglas geológicas: qué polígonos del mapa 1:250.000 son blancos de arena de fractura.

La arena de fractura que sirve es cuarzosa, redonda y resistente. Eso lo dan,
sobre todo, las arenas eólicas (el viento redondea y selecciona), en menor
medida las fluviales, y algunas areniscas cuarzosas poco cementadas. Las
reglas de abajo leen el nombre, la descripción litológica, la génesis, la edad
y la morfología de cada unidad y devuelven una clase y un conjunto de banderas.
Son reglas explícitas, no un modelo: se pueden leer, discutir y corregir.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

import pandas as pd

CLASES = [
    "arena eólica cuaternaria",
    "arena fluvial cuaternaria",
    "arenisca antigua",
    "otra con arena",
    "sin interés",
]

# Palabras clave, sobre texto sin acentos y en minúsculas.
KW = {
    "arena": r"\barena[s]?\b|\barenoso[s]?\b|\barenosa[s]?\b",
    "arenisca": r"\barenisca[s]?\b",
    "eolico": r"\beolic[oa]s?\b|\bmedano[s]?\b|\bduna[s]?\b",
    "loess": r"\bloess\b|\bloessic[oa]s?\b|\bloessoide[s]?\b",
    "fluvial": r"\bfluvial(es)?\b|\baluvial(es)?\b|\bcauce[s]?\b|\bterraza[s]?\b|\bplanicie\b|\bfluvio",
    "cuarzo": r"\bcuarz(o|osa|osas|oso|osos|itica|iticas)\b|\bsilice[ao]s?\b",
    "finos": r"\blimo[s]?\b|\barcilla[s]?\b|\bfangolita[s]?\b|\bpelita[s]?\b|\blimolita[s]?\b|\barcillita[s]?\b|\blutita[s]?\b",
    "grava": r"\bgrava[s]?\b|\bconglomerado[s]?\b|\brodado[s]?\b|\bgravoso\b",
    "volcanico": r"\bvolcan|\btoba[s]?\b|\bbasalt|\bignimbrita|\blava[s]?\b|\bpiroclast|\bandesit|\briolit",
    "cuaternario": r"\bholoceno\b|\bpleistoceno\b|\bcuaternario\b|\breciente\b|\bactual(es)?\b",
    "evaporita": r"\byeso\b|\bhalita\b|\bevaporit",
    "carbonato": r"\bcaliza[s]?\b|\bcalcareo|\bcarbonat",
}


def normalize(text: object) -> str:
    """Minúsculas y sin acentos, para que las reglas no dependan de la ortografía de cada hoja."""
    s = "" if text is None or (isinstance(text, float) and pd.isna(text)) else str(text)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return s.lower()


@dataclass
class Target:
    clase: str
    banderas: dict = field(default_factory=dict)
    motivo: str = ""


def flags(nombre: object, descripcion: object, genesis: object, edad_inf: object, edad_sup: object, morfologia: object = "") -> dict:
    """Banderas booleanas por palabra clave, mirando cada campo donde corresponde."""
    todo = " ".join(normalize(x) for x in (nombre, descripcion, genesis, morfologia))
    lito = " ".join(normalize(x) for x in (nombre, descripcion))
    edad = " ".join(normalize(x) for x in (edad_inf, edad_sup))
    f = {k: bool(re.search(p, todo)) for k, p in KW.items() if k != "cuaternario"}
    # Edad: el campo de edad manda; si está vacío, "depositos ..." en el nombre y génesis sin roca consolidada se toma como cuaternario.
    f["cuaternario"] = bool(re.search(KW["cuaternario"], edad)) or (not edad.strip() and bool(re.search(r"\bdeposito[s]?\b", lito)) and not f["arenisca"])
    f["arena_o_arenisca"] = f["arena"] or f["arenisca"]
    if f["loess"]:
        f["finos"] = True   # el loess es limo eólico: aunque diga "arenoso", penaliza como finos
    return f


def classify(nombre: object, descripcion: object, genesis: object, edad_inf: object, edad_sup: object, morfologia: object = "") -> Target:
    """Clase de blanco para una unidad del mapa geológico, con el motivo en una línea."""
    f = flags(nombre, descripcion, genesis, edad_inf, edad_sup, morfologia)
    if f["volcanico"] and not f["eolico"]:
        return Target("sin interés", f, "litología volcánica: granos líticos, no cuarzo")
    if f["evaporita"] or f["carbonato"] and not f["arena_o_arenisca"]:
        return Target("sin interés", f, "evaporitas o carbonatos")
    if not f["arena_o_arenisca"] and not f["eolico"]:
        return Target("sin interés", f, "no menciona arena ni arenisca")
    if f["loess"] and not f["arena"]:
        return Target("sin interés", f, "loess: limo eólico, no arena")
    if f["eolico"] and f["cuaternario"]:
        return Target("arena eólica cuaternaria", f, "depósito eólico cuaternario: arena suelta, seleccionada y redondeada por el viento")
    if f["eolico"] and not f["cuaternario"]:
        return Target("arenisca antigua", f, "arenisca de origen eólico, consolidada: hay que moler")
    if f["fluvial"] and f["cuaternario"] and f["arena"]:
        return Target("arena fluvial cuaternaria", f, "depósito fluvial o aluvial cuaternario con arena")
    if f["arenisca"] and not f["cuaternario"]:
        return Target("arenisca antigua", f, "arenisca consolidada" + (" cuarzosa" if f["cuarzo"] else ""))
    return Target("otra con arena", f, "menciona arena sin génesis eólica ni fluvial clara")


def classify_frame(df: pd.DataFrame, cols: dict | None = None) -> pd.DataFrame:
    """Aplica `classify` fila por fila y agrega columnas `clase`, `motivo` y una por bandera."""
    c = {"nombre": "nombre", "descripcion": "descrip_litologica", "genesis": "genesis", "edad_inf": "edad_inf", "edad_sup": "edad_sup", "morfologia": "morfologia"}
    if cols:
        c.update(cols)
    out = df.copy()
    res = [classify(r.get(c["nombre"]), r.get(c["descripcion"]), r.get(c["genesis"]), r.get(c["edad_inf"]), r.get(c["edad_sup"]), r.get(c["morfologia"], "")) for _, r in df.iterrows()]
    out["clase"] = [t.clase for t in res]
    out["motivo"] = [t.motivo for t in res]
    for k in list(KW) + ["arena_o_arenisca"]:
        out[f"f_{k}"] = [bool(t.banderas.get(k, False)) for t in res]
    return out


__all__ = ["CLASES", "KW", "normalize", "flags", "classify", "classify_frame", "Target"]
