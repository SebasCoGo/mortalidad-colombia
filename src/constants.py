"""Categorías de la consigna. No se infieren edades individuales."""

MONTHS = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
          'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
SEXES = {1: 'Hombres', 2: 'Mujeres', 3: 'Indeterminado'}
AGES = [
    ('Mortalidad neonatal', 0, 4, 'Menor de 1 mes'),
    ('Mortalidad infantil', 5, 6, '1 a 11 meses'),
    ('Primera infancia', 7, 8, '1 a 4 años'),
    ('Niñez', 9, 10, '5 a 14 años'),
    ('Adolescencia', 11, 11, '15 a 19 años'),
    ('Juventud', 12, 13, '20 a 29 años'),
    ('Adultez temprana', 14, 16, '30 a 44 años'),
    ('Adultez intermedia', 17, 19, '45 a 59 años'),
    ('Vejez', 20, 24, '60 a 84 años'),
    ('Longevidad / Centenarios', 25, 28, '85 a 100+ años'),
    ('Edad desconocida', 29, 29, 'Sin información'),
]
AGE_LABELS = [a[0] for a in AGES]
AGE_MAP = {code: label for label, lo, hi, _ in AGES for code in range(lo, hi + 1)}
COLORS = ['#137c78', '#e4a53a', '#7e91c8', '#d57969', '#63a7b0',
          '#ad96ba', '#c3af77', '#547b9e', '#98b49a', '#d7a58b']


def number(value):
    return f'{int(value):,}'.replace(',', '.')
