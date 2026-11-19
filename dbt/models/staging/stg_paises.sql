select iso3, iso2, pais, region, ingreso,
       nullif(lat, '')::double precision as lat, nullif(lon, '')::double precision as lon,
       region = 'Latin America & Caribbean' as latinoamerica
from {{ source('raw', 'paises') }}
where length(iso3) = 3
