# tp_modelado_y_optimizacion

## Etapa 3: generación manual de columnas

La implementación manual está en `etapa3.py`:

- `resolver_GC(path_instancia, segundos, variante="primal", imprimir_archivo=False)` ejecuta la variante manual primal o dual.
- `catalogo_inicial`, `crear_modelo_gc`, `resolver_GC_relajado`, `resolver_GC_pricing` y `resolver_GC_entero` exponen las fases para pruebas individuales.

## Etapa 4: generación nativa de columnas

La implementación nativa está separada en `etapa4.py`; `resolver_GC_nativo(path_instancia, segundos, imprimir_archivo=False)` integra un `Pricer` de PySCIPOpt y luego resuelve el MIP entero final.

Las instancias para ambas etapas se generan con `generate_instance.py`, usando `generar_instancia(..., incluir_tradeoff=True)`. `leer_instancia_gc` carga los coeficientes decimales `ALPHA` y `K`. Los diseños candidatos deben tener consumos no negativos y satisfacer `sum(alpha[i][j] * a[i][j]) >= k[j] * c[j]`. Por requisito, ni `w` ni `gamma` participan en las etapas 3 y 4. `generacion_columnas.py` mantiene los nombres de importación anteriores por compatibilidad.

Pruebas separadas: `python -m unittest tests_etapa3 -v` y `python -m unittest tests_etapa4 -v`. Ejecutar toda la suite: `python -m unittest discover -v`.

## Ejecución conjunta

`main.py` prueba las etapas sobre todos los archivos `instancias/*.txt` y muestra cada ejecución:

- `python main.py --segundos 60`
- `python main.py --etapa 3 --variante ambas --segundos 30`
- `python main.py --etapa 4 --segundos 30`
- `python main.py --instancias instancias --exportar`