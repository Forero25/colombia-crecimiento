-- Formato largo y limpio: un valor por país, indicador y año, solo para países (no agregados).
select b.iso3, b.indicador, b.anio, b.valor
from {{ source('raw', 'banco_mundial') }} b
join {{ ref('stg_paises') }} p using (iso3)
where b.valor is not null
