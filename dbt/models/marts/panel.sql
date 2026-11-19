-- Panel país-año en formato ancho: una fila por país y año, una columna por indicador.
with ancho as (
  select iso3, anio,
    max(valor) filter (where indicador = 'NY.GDP.MKTP.KD.ZG') as crec_pib,
    max(valor) filter (where indicador = 'NY.GDP.PCAP.KD.ZG') as crec_pib_pc,
    max(valor) filter (where indicador = 'NY.GDP.PCAP.PP.KD') as pib_pc_ppa,
    max(valor) filter (where indicador = 'NY.GDP.MKTP.KD') as pib,
    max(valor) filter (where indicador = 'NV.AGR.TOTL.ZS') as agro_pib,
    max(valor) filter (where indicador = 'NV.IND.TOTL.ZS') as industria_pib,
    max(valor) filter (where indicador = 'NV.IND.MANF.ZS') as manufactura_pib,
    max(valor) filter (where indicador = 'NV.SRV.TOTL.ZS') as servicios_pib,
    max(valor) filter (where indicador = 'NE.TRD.GNFS.ZS') as comercio_pib,
    max(valor) filter (where indicador = 'NE.GDI.TOTL.ZS') as inversion_pib,
    max(valor) filter (where indicador = 'TX.VAL.FUEL.ZS.UN') as export_combustibles,
    max(valor) filter (where indicador = 'TX.VAL.MMTL.ZS.UN') as export_minerales,
    max(valor) filter (where indicador = 'TX.VAL.TECH.MF.ZS') as export_alta_tec,
    max(valor) filter (where indicador = 'BX.KLT.DINV.WD.GD.ZS') as ied_pib,
    max(valor) filter (where indicador = 'FS.AST.PRVT.GD.ZS') as credito_pib,
    max(valor) filter (where indicador = 'FP.CPI.TOTL.ZG') as inflacion,
    max(valor) filter (where indicador = 'SP.POP.TOTL') as poblacion,
    max(valor) filter (where indicador = 'SP.POP.GROW') as crec_poblacion,
    max(valor) filter (where indicador = 'SP.POP.1564.TO.ZS') as pob_15_64,
    max(valor) filter (where indicador = 'SP.URB.TOTL.IN.ZS') as urbana,
    max(valor) filter (where indicador = 'SL.TLF.CACT.ZS') as participacion_laboral,
    max(valor) filter (where indicador = 'SL.UEM.TOTL.ZS') as desempleo,
    max(valor) filter (where indicador = 'SE.TER.ENRR') as terciaria,
    max(valor) filter (where indicador = 'IT.NET.USER.ZS') as internet,
    max(valor) filter (where indicador = 'GB.XPD.RSDV.GD.ZS') as id_pib,
    max(valor) filter (where indicador = 'IC.BUS.NDNS.ZS') as densidad_empresas,
    max(valor) filter (where indicador = 'IC.BUS.NREG') as empresas_nuevas,
    max(valor) filter (where indicador = 'GE.EST') as efectividad_gobierno,
    max(valor) filter (where indicador = 'RQ.EST') as calidad_regulatoria,
    max(valor) filter (where indicador = 'RL.EST') as estado_derecho,
    max(valor) filter (where indicador = 'CC.EST') as control_corrupcion
  from {{ ref('stg_indicadores') }}
  group by iso3, anio
)
select a.*, p.pais, p.region, p.ingreso, p.latinoamerica,
       g.desarrolladores, g.repositorios, g.pushes,
       1000.0 * g.desarrolladores / nullif(a.poblacion, 0) as desarrolladores_por_mil,
       w.pib_real, w.capital_real, w.empleo, w.horas, w.capital_humano, w.participacion_trabajo, w.ptf
from ancho a
join {{ ref('stg_paises') }} p using (iso3)
left join {{ ref('stg_github') }} g using (iso3, anio)
left join {{ ref('stg_pwt') }} w using (iso3, anio)
