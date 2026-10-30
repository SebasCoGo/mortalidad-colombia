"""Actividad 4 · Aplicaciones I · Mortalidad en Colombia, 2019."""
import os
from dash import Dash, Input, Output, State, dcc, html, dash_table, no_update
from src.analysis import load_data, filter_data, summarize
from src.charts import figures
from src.constants import MONTHS, SEXES, AGES, number

app = Dash(__name__, title='Mortalidad en Colombia | 2019', update_title='Actualizando…')
server = app.server
_, municipalities, _, geo = load_data()
departments = municipalities[['COD_DEPARTAMENTO', 'DEPARTAMENTO']].drop_duplicates().sort_values('DEPARTAMENTO')
CONFIG = {'displaylogo': False, 'responsive': True,
          'toImageButtonOptions': {'format': 'png', 'scale': 2, 'filename': 'mortalidad_colombia_2019'}}


def graph_card(number_, title, subtitle, graph_id, note_id, wide=False):
    return html.Section([
        html.Div([html.Span(number_, className='section-number'), html.H2(title)], className='card-heading'),
        html.P(subtitle, className='subtitle'),
        dcc.Graph(id=graph_id, config=CONFIG),
        html.P(id=note_id, className='finding'),
    ], className='card' + (' full-width' if wide else ''))


app.layout = html.Div([
    html.Header([
        html.A([html.Span('CO', className='brand-mark'), html.Span('Mortalidad en Colombia')], href='#', className='brand'),
        html.Div([html.Span('APLICACIONES I'), html.Span('UNIDAD 2 · ACTIVIDAD 4', className='muted')], className='course'),
    ], className='topbar'),
    html.Main([
        html.Section([
            html.Div([
                html.Div('ESTADÍSTICAS VITALES / 2019', className='eyebrow'),
                html.H1(['Una mirada a la', html.Br(), html.Span('mortalidad en Colombia.')]),
                html.P('Exploramos las defunciones no fetales de 2019 para reconocer diferencias entre territorios, meses y grupos de población.', className='intro'),
            ]),
            html.Div([html.Span('2019', className='year'), html.Span('ENERO — DICIEMBRE'), html.Span('Fuente: archivos DANE de la actividad', className='hero-source')], className='year-panel'),
        ], className='hero'),
        html.Section([
            html.Div([html.Label('Departamento', htmlFor='department'), dcc.Dropdown(id='department',
                options=[{'label': 'Colombia · todos los departamentos', 'value': 'ALL'}] +
                [{'label': r.DEPARTAMENTO, 'value': r.COD_DEPARTAMENTO} for r in departments.itertuples()],
                value='ALL', clearable=False)], className='filter department-filter'),
            html.Div([html.Label('Mes', htmlFor='month'), dcc.Dropdown(id='month',
                options=[{'label': 'Todo el año', 'value': 'ALL'}] + [{'label': m, 'value': i} for i, m in enumerate(MONTHS, 1)],
                value='ALL', clearable=False)], className='filter'),
            html.Div([html.Label('Sexo registrado', htmlFor='sex'), dcc.Dropdown(id='sex',
                options=[{'label': 'Todos', 'value': 'ALL'}] + [{'label': s, 'value': i} for i, s in SEXES.items()],
                value='ALL', clearable=False)], className='filter'),
            html.Button('Restablecer filtros', id='reset', n_clicks=0, className='button secondary'),
        ], className='filters'),
        html.Div(id='scope', className='scope', role='status'),
        dcc.Loading(type='circle', color='#137c78', children=html.Div([
            html.Section([
                html.Div([html.Span('DEFUNCIONES REGISTRADAS'), html.Strong(id='kpi-total'), html.Small('Total de la selección')], className='kpi'),
                html.Div([html.Span('HOMICIDIOS CON CÓDIGO X95'), html.Strong(id='kpi-x95'), html.Small('Agresión con arma de fuego')], className='kpi'),
                html.Div([html.Span('DEPARTAMENTOS Y BOGOTÁ D. C.'), html.Strong(id='kpi-dep'), html.Small('Con al menos un registro')], className='kpi'),
                html.Div([html.Span('MUNICIPIOS REGISTRADOS'), html.Strong(id='kpi-mun'), html.Small('Con al menos una defunción')], className='kpi'),
            ], className='kpis'),
            html.Div([
                graph_card('01', 'Distribución por departamento', 'Total de muertes según el código territorial del archivo. Pasa el cursor sobre el mapa.', 'map', 'map-note'),
                graph_card('02', 'Muertes a lo largo del año', 'Comparación mensual del número de defunciones registradas en 2019.', 'line', 'line-note'),
                graph_card('03', 'Municipios con más homicidios X95', 'Los cinco mayores conteos de agresiones con disparo de otras armas de fuego y las no especificadas.', 'violent', 'violent-note'),
                graph_card('04', 'Municipios con menos defunciones', 'Los diez menores conteos positivos. La proporción se calcula sólo entre estos municipios.', 'pie', 'pie-note'),
                html.Section([
                    html.Div([html.Span('05', className='section-number'), html.H2('Las principales causas de muerte')], className='card-heading'),
                    html.P('Las diez causas más frecuentes, ordenadas de mayor a menor número de casos.', className='subtitle'),
                    dcc.RadioItems(id='cause-level', options=[{'label': 'Código original', 'value': 4}, {'label': 'Agrupar por categoría CIE-10 (3 caracteres)', 'value': 3}], value=4, inline=True, className='radio'),
                    dash_table.DataTable(id='causes-table', columns=[{'name': 'Código CIE-10', 'id': 'codigo'},
                        {'name': 'Causa de muerte', 'id': 'nombre'}, {'name': 'Total de casos', 'id': 'casos', 'type': 'numeric', 'format': {'specifier': ',.0f', 'locale': {'group': '.', 'decimal': ','}}}],
                        style_table={'overflowX': 'auto'},
                        style_cell={'fontFamily': 'Arial, sans-serif', 'fontSize': 13, 'padding': '13px 15px', 'textAlign': 'left', 'whiteSpace': 'normal', 'height': 'auto', 'border': 'none', 'borderBottom': '1px solid #edf1f3', 'color': '#344b58'},
                        style_header={'backgroundColor': '#edf5f2', 'fontWeight': 'bold', 'color': '#205e58'},
                        style_cell_conditional=[{'if': {'column_id': 'casos'}, 'textAlign': 'right', 'width': '130px'}, {'if': {'column_id': 'codigo'}, 'width': '120px'}]),
                    html.P(id='causes-note', className='finding'),
                    html.Button('Descargar causas de la selección · CSV', id='export', n_clicks=0, className='button secondary'),
                ], className='card full-width'),
                graph_card('06', 'Muertes por sexo y departamento', 'Las barras apiladas conservan los casos de sexo indeterminado.', 'stacked', 'stacked-note', True),
                graph_card('07', 'Mortalidad por etapa de vida', 'Histograma de frecuencias agrupadas a partir de GRUPO_EDAD1, con los rangos de la actividad.', 'hist', 'hist-note', True),
            ], className='chart-grid'),
        ])),
        html.Details([
            html.Summary('Cómo se prepararon e interpretaron los datos'),
            html.P('Cada fila del archivo de mortalidad se contó como una defunción. Se conservaron los ceros iniciales de los códigos DANE y se cruzaron los nombres de municipios y causas con los catálogos entregados. Los datos compactos conservan las frecuencias de todas las combinaciones utilizadas en el análisis.'),
            html.P('Los gráficos muestran cantidades, no tasas por habitante. Un mayor conteo no demuestra mayor riesgo individual: también influyen el tamaño de la población y el territorio donde se registra la defunción. Se utilizan COD_DEPARTAMENTO y COD_DANE del archivo; no se hace una comparación por residencia habitual.'),
            html.P('X95 es un subconjunto de los homicidios: incluye sus subcódigos, por ejemplo X950 y X959. No incluye los demás mecanismos ni las demás categorías de armas de fuego. Los rankings consideran municipios del catálogo Divipola; la palabra ciudad se interpreta en ese nivel territorial.'),
            html.P('En el gráfico circular se excluyen los municipios sin registros en la selección. Si hay empates, se ordenan por código DANE ascendente. Un conteo bajo no permite concluir que un municipio sea más seguro o tenga mejores condiciones de salud.'),
            html.P('Las etapas de vida son categorías excluyentes de la tabla de la actividad. La categoría “mortalidad infantil” aquí comprende sólo los códigos 5–6, sin sumar neonatal. No se calculan tasas de mortalidad infantil o neonatal. Los rangos son aproximados y no se asignan edades exactas a los registros.'),
            html.Table([html.Thead(html.Tr([html.Th('Categoría'), html.Th('Códigos GRUPO_EDAD1'), html.Th('Rango aproximado')])),
                        html.Tbody([html.Tr([html.Td(label), html.Td(f'{lo}–{hi}' if lo != hi else str(lo)), html.Td(age)]) for label, lo, hi, age in AGES])]),
            html.P('Fuentes: No_Fetales_2019 del archivo Anexo1; hoja Final, encabezado en fila 9, de Anexo2; y hoja Hoja1 de Divipola. La cartografía simplificada MGN 2018 se incluye en el proyecto y proviene del repositorio caticoa3/colombia_mapa, elaborado a partir del DANE.'),
        ], className='methodology'),
        html.Footer('Aplicaciones I · Actividad 4 · Análisis de mortalidad en Colombia, 2019'),
        dcc.Download(id='download'),
    ], className='container'),
])


@app.callback(Output('department', 'value'), Output('month', 'value'), Output('sex', 'value'), Input('reset', 'n_clicks'), prevent_initial_call=True)
def reset_filters(clicks):
    return 'ALL', 'ALL', 'ALL'


@app.callback(
    [Output(x, 'figure') for x in ['map', 'line', 'violent', 'pie', 'stacked', 'hist']] +
    [Output('causes-table', 'data')] +
    [Output(x, 'children') for x in ['kpi-total', 'kpi-x95', 'kpi-dep', 'kpi-mun', 'scope',
                                   'map-note', 'line-note', 'violent-note', 'pie-note', 'causes-note', 'stacked-note', 'hist-note']],
    Input('department', 'value'), Input('month', 'value'), Input('sex', 'value'), Input('cause-level', 'value'))
def update_dashboard(department, month, sex, level):
    df = filter_data(department, month, sex)
    s = summarize(df, level)
    figs = figures(s, geo)
    place = 'Colombia' if department == 'ALL' else departments.set_index('COD_DEPARTAMENTO').loc[department, 'DEPARTAMENTO']
    scope = f"{place} / {'Todo 2019' if month == 'ALL' else MONTHS[int(month)-1] + ' de 2019'} / {'Todos los sexos' if sex == 'ALL' else SEXES[int(sex)]} · Los filtros se aplican a todos los gráficos."
    total = s['total']
    if total:
        top_dep = s['departments'].sort_values(['casos', 'COD_DEPARTAMENTO'], ascending=[False, True]).iloc[0]
        dep_note = f"{top_dep.DEPARTAMENTO} registra {number(top_dep.casos)} muertes, el {top_dep.casos / total:.1%} de la selección. Los valores son conteos, no tasas."
        monthly = s['monthly']
        line_note = (f"El mayor conteo mensual corresponde a {MONTHS[monthly.idxmax()-1].lower()} ({number(monthly.max())} muertes). Los meses tienen distinta duración."
                     if month == 'ALL' else 'Sólo el mes seleccionado está incluido; los demás meses quedan fuera del filtro y se muestran en cero.')
        v = s['violent']
        violent_note = (f"{v.iloc[0].MUNICIPIO} encabeza esta selección con {number(v.iloc[0].casos)} casos X95. El ranking compara cantidades, no tasas de violencia."
                        if len(v) else 'No se encontraron registros con código X95 en esta selección.')
        observed = s['municipalities']
        eligible = municipalities if department == 'ALL' else municipalities[municipalities.COD_DEPARTAMENTO.eq(department)]
        zero_count = len(eligible) - len(observed)
        pie_note = f"Se muestran {len(s['smallest'])} municipios con menor conteo positivo. Hay {zero_count} territorios del catálogo sin registros en esta selección; no aparecen como porciones. Empates: código DANE ascendente."
        causes_note = f"Las diez causas suman {number(s['causes'].head(10).casos.sum())} casos ({s['causes'].head(10).casos.sum()/total:.1%} de la selección). Agrupación: {'categoría CIE-10 de tres caracteres' if int(level)==3 else 'código original del archivo'}."
        counts = df.groupby('SEXO', observed=True).casos.sum()
        stacked_note = ' · '.join(f'{name}: {number(counts.get(code, 0))}' for code, name in SEXES.items()) + '. El sexo corresponde al registro del archivo.'
        ages = s['ages']
        hist_note = f"{ages.idxmax()} concentra {number(ages.max())} muertes ({ages.max()/total:.1%}). Edad desconocida: {number(ages.get('Edad desconocida', 0))}. La distribución no mide el riesgo de morir por edad."
    else:
        dep_note = line_note = violent_note = pie_note = causes_note = stacked_note = hist_note = 'No hay registros que cumplan estos filtros. Prueba otra combinación o restablece los filtros.'
    return figs + [s['causes'].head(10).to_dict('records'), number(total), number(s['x95']),
                   str(len(s['departments'])), number(len(s['municipalities'])), scope,
                   dep_note, line_note, violent_note, pie_note, causes_note, stacked_note, hist_note]


@app.callback(Output('download', 'data'), Input('export', 'n_clicks'),
              State('department', 'value'), State('month', 'value'), State('sex', 'value'),
              State('cause-level', 'value'), prevent_initial_call=True)
def download_causes(clicks, department, month, sex, level):
    if not clicks:
        return no_update
    from src.analysis import cause_totals
    causes = cause_totals(filter_data(department, month, sex), level)
    return dcc.send_data_frame(causes.to_csv, 'causas_mortalidad_2019.csv', index=False, encoding='utf-8-sig')


@server.get('/healthz')
def health():
    return {'status': 'ok', 'year': 2019}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8050)), debug=False)
