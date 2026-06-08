# Simulación del Sistema de Cobro de Parqueaderos – Centro Comercial Supercentro

## Descripción

Este proyecto desarrolla una simulación de eventos discretos para analizar el funcionamiento del sistema de cobro del parqueadero del Centro Comercial Supercentro.

La simulación permite estudiar el comportamiento de los usuarios que llegan al sistema, evaluar el desempeño de los cajeros y determinar si la capacidad instalada es suficiente para atender la demanda. El modelo considera diferentes tipos de usuarios con tiempos de llegada y servicio distintos, representados mediante distribuciones exponenciales.

El estudio incluye análisis estadístico, determinación del estado estable, validación del modelo y generación automática de reportes gráficos y tablas de resultados.

---

## Objetivo 

Analizar el desempeño del sistema de cobro del parqueadero mediante simulación de eventos discretos para determinar si la cantidad actual de cajeros es suficiente para atender la demanda de usuarios.

---

## Descripción del Modelo

El sistema considera cuatro tipos de usuarios:

| Tipo de Usuario | Tiempo Medio entre Llegadas (min) | Tiempo Medio de Servicio (min) | Probabilidad |
|-----------------|-----------------------------------|--------------------------------|-------------|
| Rápido | 3 | 1 | 25.0% |
| Normal | 3 | 3 | 20.0% |
| Lento | 5 | 4 | 27.5% |
| Muy Lento | 7 | 6 | 27.5% |

Las llegadas y los tiempos de servicio se generan mediante distribuciones exponenciales.

Cada usuario es asignado automáticamente al cajero que se encuentra disponible primero, buscando equilibrar la carga de trabajo entre los servidores.

---

## Tecnologías Utilizadas

- Python 3
- NumPy
- Pandas
- Matplotlib
- SciPy
- OpenPyXL

---

## Estructura del Proyecto

```text
problema-parqueadero-mm1/
│
├── src/
│   └── Cabrera_Natalia_problemaParqueadero.py
│
├── Resultados/
│   ├── Punto1_Cajeros.png
│   ├── Punto2_Usuarios.png
│   ├── Punto3_Estrategia.png
│   ├── Punto4_VCV.png
│   ├── Punto5_AntesDespues.png
│   └── Resultados_Parqueadero.xlsx
│
└── README.md
```

---

## Contenido del Repositorio

El repositorio contiene:

- Código fuente completo de la simulación.
- Implementación del modelo de colas utilizado para representar el sistema.
- Funciones para generación de usuarios y asignación de cajeros.
- Procedimiento para determinar el estado estable.
- Análisis estadístico de resultados.
- Validación mediante comparación con resultados teóricos M/M/1.
- Generación automática de gráficas.
- Exportación de resultados a Excel.

---

## Instalación

### Clonar el repositorio

```bash
git clone https://github.com/natalia200711/problema-parqueadero-mm1.git
```

### Ingresar al proyecto

```bash
cd problema-parqueadero-mm1
```

### Instalar dependencias

```bash
pip install numpy pandas matplotlib scipy openpyxl
```

---

## Ejecución

Desde la carpeta raíz del proyecto ejecutar:

```bash
python src/parqueadero_mm1.py
```

También puede ejecutarse desde la carpeta src:

```bash
python parqueadero_mm1.py
```

---

## Resultados Generados

Al finalizar la ejecución se crea automáticamente la carpeta:

```text
Resultados/
```

con los siguientes archivos:

| Archivo | Descripción |
|----------|------------|
| Punto1_Cajeros.png | Estadísticas descriptivas por cajero |
| Punto2_Usuarios.png | Distribución de usuarios por tipo |
| Punto3_Estrategia.png | Evaluación de los criterios de desempeño |
| Punto4_VCV.png | Verificación, calibración y validación |
| Punto5_AntesDespues.png | Eliminación del período transitorio |
| Resultados_Parqueadero.xlsx | Consolidado de resultados en Excel |

Además, en consola se muestran:

- Punto de corte para estado estable.
- Estadísticas de cada cajero.
- Distribución de usuarios por categoría.
- Indicadores de desempeño del sistema.
- Resultados de validación.
- Comparación antes y después del período transitorio.

---

## Autora

Natalia Cabrera Anaya
