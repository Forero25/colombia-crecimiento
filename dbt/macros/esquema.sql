-- Usa el nombre de esquema tal cual (staging, marts) en lugar de public_staging.
{% macro generate_schema_name(custom_schema_name, node) -%}
  {{ custom_schema_name if custom_schema_name else target.schema }}
{%- endmacro %}
