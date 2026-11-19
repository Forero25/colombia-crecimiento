-- Penn World Table 11.0: PIB, capital, empleo, capital humano y productividad total de los factores (PTF).
select countrycode as iso3, year as anio, rgdpna as pib_real, rkna as capital_real, emp as empleo, avh as horas,
       hc as capital_humano, labsh as participacion_trabajo, rtfpna as ptf, pop as poblacion_pwt
from {{ source('raw', 'pwt') }}
where rgdpna is not null
