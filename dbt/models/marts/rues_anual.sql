-- Creación de empresas en Colombia por año y tipo. El año en curso queda marcado como incompleto.
select anio, tipo, sum(n) as nuevas, sum(n) filter (where es_sas) as nuevas_sas,
       count(distinct mes) as meses
from {{ ref('stg_rues') }}
group by anio, tipo
