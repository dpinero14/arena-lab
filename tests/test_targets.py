import pandas as pd

from alab.targets import classify, classify_frame, flags, normalize


def test_normalize_quita_acentos_y_mayusculas():
    assert normalize("Depósitos EÓLICOS") == "depositos eolicos"
    assert normalize(None) == "" and normalize(float("nan")) == ""


def test_eolico_cuaternario():
    t = classify("Depósitos eólicos", "Arenas finas a medianas", "Continental eólico", "Holoceno", "Holoceno", "médanos")
    assert t.clase == "arena eólica cuaternaria" and t.banderas["eolico"] and t.banderas["cuaternario"]


def test_eolico_antiguo_es_arenisca():
    t = classify("Formación Agrio. Miembro Avilé", "Areniscas", "Fluvial, eólico", "Hauteriviano", "Hauteriviano")
    assert t.clase == "arenisca antigua"


def test_fluvial_cuaternario_con_arena():
    t = classify("Depósitos aluviales de cauces actuales", "Gravas y arenas", "Continental fluvial", "Holoceno", "", "")
    assert t.clase == "arena fluvial cuaternaria" and t.banderas["grava"]


def test_volcanico_queda_afuera_aunque_diga_arena():
    t = classify("Formación X", "Tobas y arenas tobáceas", "Ambiente volcánico", "Mioceno", "", "")
    assert t.clase == "sin interés"


def test_sin_arena_sin_interes():
    t = classify("Granito Y", "Granitos y granodioritas", "Igneo", "Pérmico", "", "")
    assert t.clase == "sin interés"


def test_deposito_sin_edad_se_toma_como_cuaternario():
    f = flags("Depósitos de bajos", "Arenas y limos", "Continental", "", "", "")
    assert f["cuaternario"] and f["finos"]


def test_classify_frame_agrega_columnas():
    df = pd.DataFrame({"nombre": ["Depósitos eólicos", "Basalto Z"], "descrip_litologica": ["Arenas", "Basaltos"], "genesis": ["eólico", "volcánico"], "edad_inf": ["Holoceno", "Plioceno"], "edad_sup": ["", ""], "morfologia": ["dunas", ""]})
    out = classify_frame(df)
    assert list(out["clase"]) == ["arena eólica cuaternaria", "sin interés"]
    assert "f_eolico" in out.columns and "motivo" in out.columns
