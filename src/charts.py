"""Figuras Plotly sin conexiones a servicios cartográficos externos."""
import plotly.graph_objects as go
import plotly.express as px
from .constants import COLORS, MONTHS, AGES

BASE = dict(template='plotly_white', font=dict(family='Arial, sans-serif', size=12, color='#344b58'),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=45, r=20, t=20, b=55),
            legend=dict(orientation='h', y=1.13, x=0), separators=',.')


def finish(fig, height=340):
    fig.update_layout(**BASE, height=height)
    fig.update_xaxes(showgrid=False, automargin=True)
    fig.update_yaxes(gridcolor='#edf1f3', zeroline=False, automargin=True)
    return fig


def empty(message='No hay registros para esta selección', height=340):
    fig = finish(go.Figure(), height)
    fig.add_annotation(text=message, x=.5, y=.5, xref='paper', yref='paper', showarrow=False)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def figures(s, geo):
    dep = s['departments']
    if dep.empty:
        map_fig = empty(height=440)
    else:
        map_fig = go.Figure(go.Choroplethmap(
            geojson=geo, featureidkey='properties.DPTO_CCDGO',
            locations=dep.COD_DEPARTAMENTO, z=dep.casos,
            customdata=dep[['DEPARTAMENTO']].values,
            colorscale=[[0, '#e5f2ee'], [.35, '#82bcb1'], [1, '#0c655f']],
            marker_line_color='white', marker_line_width=.8,
            colorbar=dict(title='Muertes', thickness=10, len=.7, x=.98),
            hovertemplate='<b>%{customdata[0]}</b><br>Muertes: %{z:,.0f}<extra></extra>'))
        finish(map_fig, 440)
        map_fig.update_layout(map=dict(style='white-bg', center=dict(lat=4.5, lon=-74), zoom=3.8),
                              margin=dict(l=0, r=0, t=0, b=0))
    line = go.Figure(go.Scatter(x=MONTHS, y=s['monthly'].tolist(), mode='lines+markers',
                    line=dict(color=COLORS[0], width=3), marker=dict(size=7),
                    fill='tozeroy', fillcolor='rgba(19,124,120,0.07)',
                    hovertemplate='%{x}<br>%{y:,.0f} muertes<extra></extra>'))
    finish(line, 440).update_layout(yaxis_title='Número de muertes', xaxis_title='Mes de 2019')
    line.update_xaxes(tickangle=-35)
    v = s['violent'].iloc[::-1].copy()
    if len(v):
        v['lugar'] = v.MUNICIPIO + ' · ' + v.DEPARTAMENTO
        violent = px.bar(v, x='casos', y='lugar', orientation='h', text='casos',
                         color_discrete_sequence=[COLORS[0]], custom_data=['COD_DANE'])
        finish(violent).update_layout(xaxis_title='Muertes con código X95*', yaxis_title=None)
        violent.update_traces(textposition='outside', cliponaxis=False,
            hovertemplate='%{y}<br>Código DANE: %{customdata[0]}<br>%{x:,.0f} casos<extra></extra>')
        violent.update_xaxes(range=[0, v.casos.max() * 1.22])
    else:
        violent = empty('Sin muertes con código X95 en esta selección')
    p = s['smallest'].copy()
    if len(p):
        p['lugar'] = p.MUNICIPIO + ' · ' + p.DEPARTAMENTO
        pie = go.Figure(go.Pie(labels=p.lugar, values=p.casos, hole=.62, sort=False,
                              marker=dict(colors=COLORS), textinfo='value',
                              hovertemplate='<b>%{label}</b><br>%{value} muertes<br>%{percent} de estos municipios<extra></extra>'))
        finish(pie, 380).update_layout(showlegend=True, legend=dict(orientation='v', x=1, y=1, font=dict(size=10)),
                                     margin=dict(l=5, r=5, t=5, b=10))
    else:
        pie = empty(height=380)
    sexes = s['sexes']
    if len(sexes):
        order = dep.sort_values(['casos', 'COD_DEPARTAMENTO']).DEPARTAMENTO.tolist()
        stacked = px.bar(sexes, x='casos', y='DEPARTAMENTO', color='sexo', orientation='h',
                         category_orders={'DEPARTAMENTO': order[::-1], 'sexo': ['Hombres', 'Mujeres', 'Indeterminado']},
                         color_discrete_map={'Hombres': '#137c78', 'Mujeres': '#e4a53a', 'Indeterminado': '#8c9caa'})
        finish(stacked, max(380, len(dep) * 23)).update_layout(barmode='stack', xaxis_title='Número de muertes',
                                                              yaxis_title=None, legend_title_text='')
        stacked.update_traces(hovertemplate='%{y}<br>%{x:,.0f} muertes<extra>%{fullData.name}</extra>')
    else:
        stacked = empty()
    labels = [f'{label}<br>{age}' for label, _, _, age in AGES]
    hist = go.Figure(go.Histogram(x=labels, y=s['ages'].tolist(), histfunc='sum',
                    marker_color=COLORS[0], hovertemplate='%{x}<br>%{y:,.0f} muertes<extra></extra>'))
    finish(hist, 430).update_layout(bargap=.12, xaxis_title='Etapa de vida · rango aproximado',
                                  yaxis_title='Número de muertes')
    hist.update_xaxes(type='category', categoryorder='array', categoryarray=labels, tickangle=-40)
    return [map_fig, line, violent, pie, stacked, hist]
