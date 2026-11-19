-- La región viene con espacios al final en la API; si el recorte falla, Latinoamérica queda vacía.
select 1 where (select count(*) from {{ ref('stg_paises') }} where latinoamerica) < 30
