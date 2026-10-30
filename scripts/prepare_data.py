"""Reconstruye datos compactos a partir de los tres Excel entregados.

Ejecutar desde la raíz: python scripts/prepare_data.py
No elimina registros repetidos: no hay identificador único de defunción.
"""
from pathlib import Path
import hashlib
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
RAW = DATA / 'raw'


def normalize(series, width=None):
    out = series.astype('string').str.strip().str.replace(r'\.0$', '', regex=True)
    return out.str.zfill(width) if width else out.str.upper().str.replace('.', '', regex=False)


def main():
    names = ['Anexo1.NoFetal2019_CE_15-03-23.xlsx',
             'Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx', 'Divipola_CE_.xlsx']
    deaths = pd.read_excel(RAW / names[0], sheet_name='No_Fetales_2019',
                           dtype={'COD_DANE': str, 'COD_DEPARTAMENTO': str, 'COD_MUNICIPIO': str})
    assert deaths['AÑO'].eq(2019).all(), 'Hay registros fuera de 2019'
    assert deaths.MES.between(1, 12).all()
    assert deaths.SEXO.isin([1, 2, 3]).all()
    assert deaths.GRUPO_EDAD1.between(0, 29).all()
    deaths['COD_DANE'] = normalize(deaths.COD_DANE, 5)
    deaths['COD_DEPARTAMENTO'] = normalize(deaths.COD_DEPARTAMENTO, 2)
    deaths['COD_MUNICIPIO'] = normalize(deaths.COD_MUNICIPIO, 3)
    assert deaths.COD_DANE.eq(deaths.COD_DEPARTAMENTO + deaths.COD_MUNICIPIO).all()
    deaths['COD_MUERTE'] = normalize(deaths.COD_MUERTE)
    muni = pd.read_excel(RAW / names[2], sheet_name='Hoja1', dtype=str)
    muni = muni[['COD_DANE', 'COD_DEPARTAMENTO', 'DEPARTAMENTO', 'MUNICIPIO']].copy()
    muni['COD_DANE'] = normalize(muni.COD_DANE, 5)
    muni['COD_DEPARTAMENTO'] = normalize(muni.COD_DEPARTAMENTO, 2)
    assert not muni.COD_DANE.duplicated().any()
    assert deaths.COD_DANE.isin(muni.COD_DANE).all(), 'Hay municipios sin correspondencia'
    muni.to_csv(DATA / 'municipios.csv', index=False)
    causes = pd.read_excel(RAW / names[1], sheet_name='Final', header=8)
    catalogs = []
    for code_index, text_index, level in [(2, 3, 3), (4, 5, 4)]:
        cat = causes.iloc[:, [code_index, text_index]].copy()
        cat.columns = ['codigo', 'nombre']
        cat = cat.dropna()
        cat['codigo'] = normalize(cat.codigo)
        cat['nombre'] = cat.nombre.str.strip()
        # El catálogo tiene dos variantes editoriales (T81 y X16).
        # Se conserva la descripción más frecuente para cada categoría;
        # las variantes se dejan registradas, sin multiplicar defunciones.
        conflicts = cat.groupby('codigo').nombre.nunique()
        variants = cat[cat.codigo.isin(conflicts[conflicts.gt(1)].index)]
        if len(variants):
            variants.drop_duplicates().to_csv(DATA / f'variantes_catalogo_{level}.csv', index=False)
        cat = cat.groupby(['codigo', 'nombre']).size().reset_index(name='frecuencia')
        cat = cat.sort_values(['codigo', 'frecuencia', 'nombre'], ascending=[True, False, True])
        cat = cat.drop_duplicates('codigo').drop(columns='frecuencia')
        cat['nivel'] = level
        catalogs.append(cat)
    catalog = pd.concat(catalogs, ignore_index=True)
    catalog.to_csv(DATA / 'causas.csv', index=False)
    dims = ['COD_DANE', 'MES', 'SEXO', 'GRUPO_EDAD1', 'COD_MUERTE']
    cube = deaths.groupby(dims, dropna=False).size().reset_index(name='casos')
    assert cube.casos.sum() == len(deaths)
    cube.to_csv(DATA / 'mortalidad.csv.gz', index=False, compression={'method': 'gzip', 'mtime': 0})
    exact = set(catalog[catalog.nivel.eq(4)].codigo)
    general = set(catalog[catalog.nivel.eq(3)].codigo)
    missing = deaths.loc[~deaths.COD_MUERTE.isin(exact) & ~deaths.COD_MUERTE.str[:3].isin(general), 'COD_MUERTE']
    audit = {
        'year': 2019, 'total_rows': len(deaths), 'cube_rows': len(cube),
        'departments': int(deaths.COD_DEPARTAMENTO.nunique()),
        'municipalities_observed': int(deaths.COD_DANE.nunique()),
        'municipalities_catalog': len(muni),
        'sex_counts': {str(k): int(v) for k, v in deaths.SEXO.value_counts().items()},
        'month_counts': {str(k): int(v) for k, v in deaths.MES.value_counts().sort_index().items()},
        'age_counts': {str(k): int(v) for k, v in deaths.GRUPO_EDAD1.value_counts().sort_index().items()},
        'x95_count': int(deaths.COD_MUERTE.str.startswith('X95').sum()),
        'all_homicides': int(deaths.MANERA_MUERTE.eq('Homicidio').sum()),
        'unmapped_cause_records': int(len(missing)),
        'unmapped_cause_codes': sorted(missing.unique().tolist()),
        'source_sha256': {name: hashlib.sha256((RAW / name).read_bytes()).hexdigest() for name in names},
    }
    (DATA / 'auditoria.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
