# tp_modelado_y_optimizacion

## Etapas 3 y 4: generacion de columnas

Las funciones de esta etapa estan en `generacion_columnas.py`:

- `resolver_GC(path_instancia, segundos, variante="primal", imprimir_archivo=False)` ejecuta la version manual primal o dual.
- `resolver_GC_nativo(path_instancia, segundos, imprimir_archivo=False)` ejecuta la version con `Pricer` de PySCIPOpt.
- Ambas funciones retornan `(objetivo, cantidad_restricciones, cantidad_variables)` del MIP final.
- `catalogo_inicial`, `crear_modelo_gc`, `resolver_GC_relajado`, `resolver_GC_pricing` y `resolver_GC_entero` permiten usar y probar cada fase por separado.

Las instancias de GC mantienen las lineas de datos existentes y agregan `ALPHA i j valor` para cada recurso/diseno y `K j valor` para cada diseno; `GAMMA valor` se acepta para compatibilidad con el generador. La lectura de GC se realiza con `leer_instancia_gc`. Los candidatos deben tener consumos no negativos y satisfacer `sum(alpha[i][j] * a[i][j]) >= k[j] * c[j]`. Conforme al pedido para estas etapas, no se usan `w`, `gamma` ni la capacidad de potencia.

Pruebas de esta etapa: `python -m unittest tests_generacion_columnas -v`.