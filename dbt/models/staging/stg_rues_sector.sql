select anio::int as anio,
       case when categoria_matricula = 'PERSONA NATURAL' then 'persona_natural' else 'juridica' end as tipo,
       nullif(ciiu2, '') as ciiu2, n
from {{ source('raw', 'rues_sector') }}
where anio ~ '^(200[5-9]|20[12][0-9])$'
