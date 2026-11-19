-- Matrículas nuevas del RUES por mes y cámara. Se separan las sociedades (personas jurídicas con ánimo de lucro),
-- las personas naturales y las entidades sin ánimo de lucro (ESAL), que no son emprendimiento comercial.
with base as (
  select to_date(ym || '01', 'YYYYMMDD') as mes, camara_comercio as camara,
         categoria_matricula, coalesce(organizacion_juridica, '') as org, n
  from {{ source('raw', 'rues_mensual') }}
  where ym ~ '^(200[5-9]|20[12][0-9])(0[1-9]|1[0-2])$'
)
select mes, extract(year from mes)::int as anio, camara,
  case
    when categoria_matricula = 'PERSONA NATURAL' then 'persona_natural'
    when upper(org) ~ '(ASOCIACI|FUNDACI|CORPORACI|COOPERATIV|PRECOOPERATIV|IGLESIA|JUNTA|SINDICAT|VEEDUR|FONDO DE EMPLEADOS|MUTUAL|ENTIDADES|INSTITUCIONES|FEDERACI|CONFEDERACI|EMPRESAS ASOCIATIVAS|VIVIENDA)' then 'esal'
    else 'sociedad'
  end as tipo,
  org ilike '%ACCIONES SIMPLIFICADAS%' as es_sas,
  n
from base
