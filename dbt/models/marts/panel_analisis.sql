-- Universo del análisis: países con mediana de población >= 1 millón en 2015-2024.
with tam as (
  select iso3, percentile_cont(0.5) within group (order by poblacion) as pob_mediana
  from {{ ref('panel') }} where anio between 2015 and 2024 group by iso3
)
select p.* from {{ ref('panel') }} p join tam using (iso3) where tam.pob_mediana >= 1000000
