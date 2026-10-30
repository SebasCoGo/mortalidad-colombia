"""Agregaciones compartidas por el dashboard, las descargas y las pruebas."""
from functools import lru_cache
from pathlib import Path
import json
import pandas as pd
from .constants import AGE_MAP, AGE_LABELS, SEXES

DATA = Path(__file__).resolve().parents[1] / 'data'


@lru_cache(maxsize=1)
def load_data():
    df = pd.read_csv(DATA / 'mortalidad.csv.gz', dtype={
        'COD_DANE': 'string', 'MES': 'int8', 'SEXO': 'int8',
        'GRUPO_EDAD1': 'int8', 'COD_MUERTE': 'string', 'casos': 'int32'})
    df['COD_DEPARTAMENTO'] = df.COD_DANE.str[:2].astype('category')
    df['edad'] = df.GRUPO_EDAD1.map(AGE_MAP).astype('category')
    df['COD_DANE'] = df.COD_DANE.astype('category')
    df['COD_MUERTE'] = df.COD_MUERTE.astype('category')
    muni = pd.read_csv(DATA / 'municipios.csv', dtype=str)
    causes = pd.read_csv(DATA / 'causas.csv', dtype={'codigo': str})
    geo = json.loads((DATA / 'departamentos.geojson').read_text())
    return df, muni, causes, geo


def filter_data(department='ALL', month='ALL', sex='ALL'):
    df = load_data()[0]
    mask = pd.Series(True, index=df.index)
    if department != 'ALL':
        mask &= df.COD_DEPARTAMENTO.eq(str(department))
    if month != 'ALL':
        mask &= df.MES.eq(int(month))
    if sex != 'ALL':
        mask &= df.SEXO.eq(int(sex))
    return df.loc[mask]


def total_by(df, columns):
    return df.groupby(columns, observed=True, as_index=False).casos.sum()


def municipality_totals(df):
    counts = total_by(df, ['COD_DANE'])
    return counts.merge(load_data()[1], on='COD_DANE', how='left', validate='one_to_one')


def ranking(df, smallest=False):
    counts = municipality_totals(df)
    # Sólo municipios con al menos un registro; ceros no forman porciones circulares.
    return counts[counts.casos.gt(0)].sort_values(
        ['casos', 'COD_DANE'], ascending=[smallest, True]).head(10 if smallest else 5)


def cause_totals(df, level=4):
    temp = df[['COD_MUERTE', 'casos']].copy()
    temp['codigo'] = temp.COD_MUERTE.astype('string').str[:3] if int(level) == 3 else temp.COD_MUERTE.astype('string')
    counts = total_by(temp, ['codigo'])
    catalog = load_data()[2]
    exact = catalog[catalog.nivel.eq(4)].set_index('codigo').nombre.to_dict()
    general = catalog[catalog.nivel.eq(3)].set_index('codigo').nombre.to_dict()
    def name(code):
        if int(level) == 3 or len(code) == 3:
            return general.get(code, 'Sin descripción en el catálogo')
        return exact.get(code, general.get(code[:3], 'Sin descripción en el catálogo') + ' (categoría general)')
    counts['nombre'] = counts.codigo.map(name)
    return counts.sort_values(['casos', 'codigo'], ascending=[False, True])[['codigo', 'nombre', 'casos']].reset_index(drop=True)


def summarize(df, level=4):
    _, muni, _, _ = load_data()
    departments = muni[['COD_DEPARTAMENTO', 'DEPARTAMENTO']].drop_duplicates()
    dep = total_by(df, ['COD_DEPARTAMENTO']).merge(departments, on='COD_DEPARTAMENTO', validate='one_to_one')
    monthly = df.groupby('MES', observed=True).casos.sum().reindex(range(1, 13), fill_value=0)
    x95 = df[df.COD_MUERTE.astype('string').str.startswith('X95')]
    age = df.groupby('edad', observed=True).casos.sum().reindex(AGE_LABELS, fill_value=0)
    sex = total_by(df, ['COD_DEPARTAMENTO', 'SEXO']).merge(departments, on='COD_DEPARTAMENTO')
    sex['sexo'] = sex.SEXO.map(SEXES)
    return dict(total=int(df.casos.sum()), departments=dep, monthly=monthly,
                violent=ranking(x95), x95=int(x95.casos.sum()),
                smallest=ranking(df, smallest=True), causes=cause_totals(df, level),
                ages=age, sexes=sex, municipalities=municipality_totals(df))
