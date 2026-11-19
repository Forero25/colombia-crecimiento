select iso3, iso2, pais, trim(region) as region, trim(ingreso) as ingreso,
       nullif(lat, '')::double precision as lat, nullif(lon, '')::double precision as lon,
       trim(region) = 'Latin America & Caribbean' as latinoamerica
from {{ source('raw', 'paises') }}
where length(iso3) = 3
