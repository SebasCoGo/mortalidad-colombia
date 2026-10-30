import json
from pathlib import Path
import sys
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.analysis import load_data, filter_data, summarize, ranking, cause_totals
from src.constants import AGE_MAP, AGES
from app import app, update_dashboard, download_causes


def test_totals_match_source_audit():
    df = load_data()[0]
    audit = json.loads((Path(__file__).resolve().parents[1] / 'data/auditoria.json').read_text())
    assert df.casos.sum() == audit['total_rows'] == 244355
    assert df.groupby('MES', observed=True).casos.sum().to_dict() == {int(k): v for k, v in audit['month_counts'].items()}
    assert df.groupby('SEXO', observed=True).casos.sum().to_dict() == {1: 134573, 2: 109689, 3: 93}
    assert df.groupby('GRUPO_EDAD1', observed=True).casos.sum().to_dict() == {int(k): v for k, v in audit['age_counts'].items()}


def test_age_categories_exhaustive_and_disjoint():
    codes = [code for _, lo, hi, _ in AGES for code in range(lo, hi + 1)]
    assert sorted(codes) == list(range(30))
    assert len(codes) == len(set(codes))
    assert AGE_MAP[4] == 'Mortalidad neonatal'
    assert AGE_MAP[5] == 'Mortalidad infantil'
    assert AGE_MAP[24] == 'Vejez'
    assert AGE_MAP[25] == 'Longevidad / Centenarios'
    assert AGE_MAP[29] == 'Edad desconocida'


def test_map_and_joins_cover_all_records():
    df, muni, _, geo = load_data()
    assert df.COD_DANE.astype(str).str.len().eq(5).all()
    assert not muni.COD_DANE.duplicated().any()
    assert df.COD_DANE.isin(muni.COD_DANE).all()
    assert set(df.COD_DEPARTAMENTO) == {x['properties']['DPTO_CCDGO'] for x in geo['features']}


def test_x95_includes_subcodes_but_not_other_homicides():
    s = summarize(filter_data())
    assert s['x95'] == 9273
    assert s['x95'] < 13077
    assert s['violent'].casos.is_monotonic_decreasing


@pytest.mark.parametrize('department,month,sex', [('ALL','ALL','ALL'), ('15','ALL','ALL'), ('11',12,2), ('97',2,3), ('88',1,1)])
def test_filtered_charts_reconcile(department, month, sex):
    df = filter_data(department, month, sex)
    s = summarize(df)
    assert s['total'] == s['departments'].casos.sum() == s['monthly'].sum() == s['ages'].sum() == s['sexes'].casos.sum()
    assert s['total'] == s['causes'].casos.sum() == s['municipalities'].casos.sum()
    assert s['smallest'].casos.gt(0).all()
    assert s['smallest'].casos.is_monotonic_increasing
    assert len(s['smallest']) <= 10
    if department != 'ALL':
        assert df.COD_DEPARTAMENTO.eq(department).all()
    if month != 'ALL':
        assert df.MES.eq(month).all()
    if sex != 'ALL':
        assert df.SEXO.eq(sex).all()
    result = update_dashboard(department, month, sex, 4)
    assert len(result) == 19
    for figure in result[:6]:
        assert json.loads(figure.to_json()) is not None


def test_cause_levels_do_not_lose_records():
    df = filter_data()
    for level in [3, 4]:
        c = cause_totals(df, level)
        assert c.casos.sum() == 244355
        assert not c.codigo.duplicated().any()
        assert c.casos.is_monotonic_decreasing


def test_ranking_ties_use_full_municipality_code():
    df = pd.DataFrame({'COD_DANE': ['05001', '15001', '11001'], 'casos': [2, 2, 1]})
    assert ranking(df, smallest=True).COD_DANE.tolist() == ['11001', '05001', '15001']


def test_http_layout_assets_and_callback():
    client = app.server.test_client()
    for path in ['/', '/healthz', '/_dash-layout', '/_dash-dependencies', '/assets/style.css']:
        assert client.get(path).status_code == 200
    callback_key = next(k for k in app.callback_map if 'map.figure' in k)
    meta = app.callback_map[callback_key]
    payload = {'output': callback_key,
               'outputs': [{'id': o.component_id, 'property': o.component_property} for o in meta['output']],
               'inputs': [{'id': i, 'property': 'value', 'value': v} for i, v in
                          [('department', 'ALL'), ('month', 'ALL'), ('sex', 'ALL'), ('cause-level', 4)]],
               'state': [], 'changedPropIds': ['department.value']}
    result = client.post('/_dash-update-component', json=payload)
    assert result.status_code == 200, result.data[:1000]
    assert result.json['response']['kpi-total']['children'] == '244.355'


def test_csv_download_uses_current_selection():
    result = download_causes(1, '15', 1, 2, 4)
    assert result['filename'].endswith('.csv')
    assert 'codigo,nombre,casos' in result['content']
    csv_sum = pd.read_csv(__import__('io').StringIO(result['content'])).casos.sum()
    assert csv_sum == filter_data('15', 1, 2).casos.sum()
