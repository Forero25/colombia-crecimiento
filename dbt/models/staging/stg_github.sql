-- Innovation Graph: promedio anual de desarrolladores y suma anual de repositorios y pushes por país.
with d as (select iso2_code as iso2, year as anio, avg(developers) as desarrolladores, count(*) as trimestres
           from {{ source('raw', 'gh_developers') }} group by 1, 2),
     r as (select iso2_code as iso2, year as anio, sum(repositories) as repositorios from {{ source('raw', 'gh_repositories') }} group by 1, 2),
     g as (select iso2_code as iso2, year as anio, sum(git_pushes) as pushes from {{ source('raw', 'gh_git_pushes') }} group by 1, 2)
select p.iso3, d.anio, d.desarrolladores, r.repositorios, g.pushes, d.trimestres
from d
join {{ ref('stg_paises') }} p on p.iso2 = d.iso2
left join r on r.iso2 = d.iso2 and r.anio = d.anio
left join g on g.iso2 = d.iso2 and g.anio = d.anio
