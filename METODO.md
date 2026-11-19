## La pregunta

¿Le ha ido bien a Colombia? La respuesta depende de con quién se compare. Este proyecto compara a Colombia con los países que más se le parecen por su estructura económica (sus "gemelos"), con América Latina y con el mundo. Después pregunta si la creación de empresas y startups explica o anticipa el crecimiento, y termina con un pronóstico evaluado con honestidad.

## Arquitectura

- **Ingesta (Python):** Banco Mundial (WDI y WGI), Penn World Table 11.0, RUES en datos.gov.co y GitHub Innovation Graph.
- **Base de datos:** PostgreSQL en un contenedor. Los datos crudos van al esquema `raw`.
- **Transformación (dbt):** modelos `staging` y `marts` con pruebas de unicidad, nulos y rangos plausibles. Las pruebas encontraron, por ejemplo, que Islas Caimán registra más de 200 empresas nuevas por cada 1.000 adultos: son sociedades de papel de un centro financiero offshore. Por eso el universo de análisis son los países con más de un millón de habitantes.
- **Orquestación:** Docker Compose levanta PostgreSQL y corre todo el pipeline. GitHub Actions lo ejecuta cada mes.
- **Análisis (Python):** scikit-learn y statsmodels. Los resultados quedan en `resultados/`, y esta app los lee.

## Los gemelos de Colombia

Para cada país promedié doce rasgos de su estructura entre 2015 y 2024: ingreso por persona, peso de la agricultura, la manufactura y los servicios, apertura comercial, inversión, dependencia de combustibles y minerales, población en edad de trabajar, urbanización, crédito privado, calidad institucional e internet. Después:

1. Estandaricé los rasgos para que todos pesen igual.
2. Reduje la información a unos pocos ejes con componentes principales.
3. Medí la distancia entre países. Los gemelos son los más cercanos a Colombia.
4. Para saber si un gemelo es real o un accidente del método, repetí el cálculo 500 veces, quitando cada vez tres rasgos y el 10 % de los países al azar. Un gemelo "estable" aparece entre los diez más cercanos en al menos el 75 % de las repeticiones.

## Crecimiento comparado

- **Trayectoria:** ingreso por persona (PPA) con índice 2000 = 100. Para cada grupo se usa la mediana, que no se deja arrastrar por un caso extremo.
- **Convergencia:** los países pobres suelen crecer más rápido. Una regresión entre países (crecimiento 2000-2024 contra ingreso inicial, inversión, instituciones y crecimiento de la población) dice cuánto "debía" crecer Colombia, y el residuo mide si creció más o menos de lo esperado.
- **Contabilidad del crecimiento (Penn World Table):** el crecimiento del producto por trabajador se divide en lo que aportó más capital por trabajador, más capital humano y el resto, la productividad total de los factores (PTF). Ejemplo: si el producto por trabajador creció 1,1 % al año y el capital aportó 0,8 y el capital humano 0,5, la productividad restó 0,2.

## Emprendimiento

- **Posición:** comparo la densidad de empresas nuevas y los desarrolladores en GitHub de Colombia con lo esperado para su nivel de ingreso.
- **Panel con efectos fijos:** el panel tiene 143 países y unos 2.000 países-año. Los efectos fijos de país quitan lo que es propio de cada país y no cambia (su cultura empresarial, su geografía). Los de año quitan los choques mundiales (la crisis de 2008, la pandemia). Lo que queda compara a cada país consigo mismo. Pruebo en las dos direcciones: si la densidad de hoy anticipa el crecimiento de los tres años siguientes, y si el crecimiento de hoy anticipa más empresas.
- **RUES:** de los más de 9 millones de registros públicos del RUES solo pedí conteos agregados (por mes, cámara, tipo y sector); ningún dato personal sale de datos.gov.co. Los totales de sociedades quedan alrededor de 3 % por encima de los que publica Confecámaras, con la misma tendencia.

## Pronóstico

Para cada año de prueba entre 2012 y 2024, los modelos se entrenan solo con lo que se sabía antes de ese año (evaluación hacia adelante) y predicen el crecimiento de todos los países. Comparo cuatro:

- un ingenuo: el promedio de los últimos cinco años del país;
- una regresión ridge;
- gradient boosting;
- gradient boosting sin las variables de emprendimiento, para saber si estas aportan.

El intervalo del pronóstico es conformal: suma y resta al pronóstico el error que el modelo superó solo el 20 % de las veces en la evaluación.

## Glosario

- **PPA (paridad de poder adquisitivo):** convierte ingresos a una moneda común que compra lo mismo en todos los países.
- **Componentes principales:** combinaciones de los rasgos originales que resumen la mayor parte de sus diferencias en pocos ejes.
- **Clúster:** grupo de países parecidos encontrado por el algoritmo, sin decirle cuáles.
- **Efectos fijos:** controles que comparan a cada país consigo mismo a lo largo del tiempo.
- **Valor p:** probabilidad de ver un resultado así de grande si en realidad no hubiera relación. Por encima de 0,05 no se puede descartar el azar.
- **Error absoluto medio:** cuántos puntos porcentuales se equivoca el pronóstico, en promedio.
- **PTF (productividad total de los factores):** la parte del crecimiento que no explican ni más máquinas ni más educación; refleja cómo de bien se usan.
- **dbt:** herramienta para transformar datos con SQL versionado y probado.
