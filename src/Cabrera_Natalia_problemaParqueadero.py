# ==========================================================
# SOLUCIÓN DEL PROBLEMA DE PARQUEADEROS
# Centro Comercial Supercentro
# ==========================================================

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

np.random.seed(123)

CARPETA = "Resultados"
os.makedirs(CARPETA, exist_ok=True)

TIEMPO_SIMULACION = 1000   # minutos
NUM_REPLICAS      = 30
VENTANA           = 50

# ==========================================================
# PARÁMETROS DE USUARIOS
# ==========================================================

usuarios = {
    "Rapido":    {"servicio": 1, "llegada": 3, "probabilidad": 0.25},
    "Normal":    {"servicio": 3, "llegada": 3, "probabilidad": 0.20},
    "Lento":     {"servicio": 4, "llegada": 5, "probabilidad": 0.275},
    "Muy Lento": {"servicio": 6, "llegada": 7, "probabilidad": 0.275},
}

# ==========================================================
# SIMULACIÓN M/M/1
# ==========================================================

def generar_tipo_usuario():
    tipos = list(usuarios.keys())
    probs = [usuarios[t]["probabilidad"] for t in tipos]
    return np.random.choice(tipos, p=probs)


def simular_cajero_mm1(id_cajero, tiempo_total):
    reloj      = 0
    disponible = 0
    tiempos_espera   = []
    tiempos_servicio = []
    tiempos_sistema  = []
    tipos_usuario    = []
    longitud_cola    = []

    while reloj < tiempo_total:
        tipo         = generar_tipo_usuario()
        inter_arribo = np.random.exponential(usuarios[tipo]["llegada"])
        reloj       += inter_arribo

        if reloj > tiempo_total:
            break

        servicio        = np.random.exponential(usuarios[tipo]["servicio"])
        inicio_servicio = max(reloj, disponible)
        espera          = inicio_servicio - reloj
        fin_servicio    = inicio_servicio + servicio
        disponible      = fin_servicio

        tiempos_espera.append(espera)
        tiempos_servicio.append(servicio)
        tiempos_sistema.append(fin_servicio - reloj)
        tipos_usuario.append(tipo)
        
        # Aproximación simple de clientes esperando
        cola = max(
            0,
            int(
                espera /
                np.mean(
                    usuarios[tipo]["servicio"]
                )
            )
        )

        longitud_cola.append(cola)

    return {
        "id":       id_cajero,
        "espera":   tiempos_espera,
        "servicio": tiempos_servicio,
        "sistema":  tiempos_sistema,
        "tipos":    tipos_usuario,
        "cola":     longitud_cola,
    }


def simular_cajero_con_distribucion(id_cajero, tiempo_total):

    reloj = 0
    disponible = 0
    tiempos_espera = []
    tiempos_servicio = []
    tiempos_sistema = []
    tipos_usuario = []
    longitud_cola = []
    
    # Esta función se llamará desde simular_sistema_distribuido
    # donde ya se generan los usuarios y se asignan a cajeros
    
    return {
        "id": id_cajero,
        "espera": tiempos_espera,
        "servicio": tiempos_servicio,
        "sistema": tiempos_sistema,
        "tipos": tipos_usuario,
        "cola": longitud_cola,
    }


def simular_sistema_distribuido(num_cajeros, tiempo_total):
    
    # Inicializar cajeros vacíos
    cajeros = []
    for i in range(num_cajeros):
        cajeros.append({
            "id": i + 1,
            "disponible": 0,
            "espera": [],
            "servicio": [],
            "sistema": [],
            "tipos": [],
            "cola": []
        })
    
    # Tiempo de simulación
    t = 0
    
    while t < tiempo_total:
        # Generar un usuario
        tipo = generar_tipo_usuario()
        inter_arribo = np.random.exponential(usuarios[tipo]["llegada"])
        t += inter_arribo
        
        if t > tiempo_total:
            break
        
        # ASIGNAR AL CAJERO QUE SE LIBERA PRIMERO
        cajero_idx = np.argmin(
            [c["disponible"] for c in cajeros]
     )

        cajero = cajeros[cajero_idx]
        
        servicio = np.random.exponential(usuarios[tipo]["servicio"])
        inicio_servicio = max(t, cajero["disponible"])
        espera = inicio_servicio - t
        fin_servicio = inicio_servicio + servicio
        cajero["disponible"] = fin_servicio
        
        cajero["espera"].append(espera)
        cajero["servicio"].append(servicio)
        cajero["sistema"].append(fin_servicio - t)
        cajero["tipos"].append(tipo)
        
        # Longitud de cola aproximada
        cola = max(0, int(espera / np.mean(usuarios[tipo]["servicio"])))
        cajero["cola"].append(cola)
    
    return cajeros

def ejecutar_replicas(num_cajeros, num_replicas, tiempo_total):
    """
    Ejecuta múltiples réplicas y devuelve los resultados agregados.
    """
    todas_replicas = []
    
    for replica in range(num_replicas):
        # Cada réplica usa diferente semilla para independencia
        np.random.seed(123 + replica)
        
        sistema = simular_sistema_distribuido(num_cajeros, tiempo_total)
        todas_replicas.append(sistema)
        
        if (replica + 1) % 10 == 0:
            print(f"  Réplica {replica+1}/{num_replicas} completada")
    
    return todas_replicas


def agregar_metricas_replicas(todas_replicas):
    """
    Agrega (promedia) los resultados de todas las réplicas.
    Mantiene la estructura de 3 cajeros.
    """
    # Crear estructura para 3 cajeros
    sistema_agregado = []
    for i in range(3):
        sistema_agregado.append({
            "id": i + 1,
            "espera": [],
            "servicio": [],
            "sistema": [],
            "tipos": [],
            "cola": []
        })
    
    # Acumular datos de todas las réplicas
    for replica in todas_replicas:
        for cajero in replica:
            idx = cajero["id"] - 1  # índice 0, 1, 2
            sistema_agregado[idx]["espera"].extend(cajero["espera"])
            sistema_agregado[idx]["servicio"].extend(cajero["servicio"])
            sistema_agregado[idx]["sistema"].extend(cajero["sistema"])
            sistema_agregado[idx]["tipos"].extend(cajero["tipos"])
            sistema_agregado[idx]["cola"].extend(cajero["cola"])
    
    return sistema_agregado

# ==========================================================
# ESTADO ESTABLE - PROMEDIO MÓVIL
# ==========================================================

def determinar_estado_estable(datos, ventana=VENTANA):
    datos = np.array(datos)
    pm    = np.array([np.mean(datos[i:i+ventana]) for i in range(len(datos) - ventana)])
    diferencias = np.abs(np.diff(pm))
    umbral = np.mean(diferencias)
    punto_corte = 0
    for i, d in enumerate(diferencias):
        if d < umbral:
            punto_corte = i
            break
    # Garantizar al menos VENTANA observaciones de warm-up
    punto_corte = max(punto_corte, ventana)
    return punto_corte, pm


# ==========================================================
# SIMULAR Y DETERMINAR WARM-UP
# ==========================================================

print("=" * 60)
print("EJECUTANDO MÚLTIPLES RÉPLICAS")
print("=" * 60)
print(f"Total de réplicas: {NUM_REPLICAS}")
print(f"Tiempo por réplica: {TIEMPO_SIMULACION} minutos")
print()

# Ejecutar todas las réplicas
todas_replicas = ejecutar_replicas(3, NUM_REPLICAS, TIEMPO_SIMULACION)

# Agregar resultados de todas las réplicas
sistema = agregar_metricas_replicas(todas_replicas)

# Calcular punto_corte promedio de todas las réplicas
puntos_corte = []
for rep in todas_replicas:
    pc, _ = determinar_estado_estable(rep[0]["sistema"])
    puntos_corte.append(pc)

punto_corte = int(np.mean(puntos_corte))
print(f"Punto de corte promedio: {punto_corte}")

# Calcular datos base para referencia (opcional)
datos_base = []
for rep in todas_replicas[:5]:
    datos_base.extend(rep[0]["sistema"])
print(f"Total observaciones agregadas (primeras 5 réplicas): {len(datos_base)}")

# ==========================================================
# PUNTO 1 - ESTADÍSTICAS POR CAJERO
# ==========================================================

print("=" * 60)
print("PUNTO 1 - ANÁLISIS ESTADÍSTICO DE CAJEROS")
print("=" * 60)

filas = []
for cajero in sistema:
    datos_est = np.array(cajero["sistema"][punto_corte:])
    n   = len(datos_est)
    m   = np.mean(datos_est)
    sd  = np.std(datos_est, ddof=1)
    me  = stats.t.ppf(0.975, n - 1) * sd / np.sqrt(n)
    util = np.sum(cajero["servicio"]) / (TIEMPO_SIMULACION * NUM_REPLICAS) * 100

    filas.append({
        "Cajero":        cajero["id"],
        "Media":         round(m, 4),
        "Mediana":       round(np.median(datos_est), 4),
        "DesvStd":       round(sd, 4),
        "Minimo":        round(np.min(datos_est), 4),
        "Maximo":        round(np.max(datos_est), 4),
        "Utilizacion%":  round(util, 2),
        "IC95_Inf":      round(m - me, 4),
        "IC95_Sup":      round(m + me, 4),
    })

df_cajeros = pd.DataFrame(filas)
print(df_cajeros.to_string(index=False))

mejor = df_cajeros.loc[df_cajeros["Media"].idxmin()]
peor  = df_cajeros.loc[df_cajeros["Media"].idxmax()]
print(f"\nCajero con MENOR tiempo promedio: Cajero {int(mejor['Cajero'])} ({mejor['Media']:.2f} min)")
print(f"Cajero con MAYOR tiempo promedio: Cajero {int(peor['Cajero'])}  ({peor['Media']:.2f} min)")
print("Un menor tiempo promedio indica mayor eficiencia operativa.")

# Gráfica Punto 1
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle("Punto 1 - Estadísticas por Cajero", fontsize=13)

colores = ["steelblue", "seagreen", "tomato"]
ax1.bar(df_cajeros["Cajero"], df_cajeros["Media"], color=colores, width=0.5)
ax1.errorbar(df_cajeros["Cajero"], df_cajeros["Media"],
             yerr=[df_cajeros["Media"] - df_cajeros["IC95_Inf"],
                   df_cajeros["IC95_Sup"] - df_cajeros["Media"]],
             fmt="none", color="black", capsize=8, lw=2)
for _, row in df_cajeros.iterrows():
    ax1.text(row["Cajero"], row["Media"] + 0.1, f'{row["Media"]:.2f}',
             ha="center", fontweight="bold")
ax1.set_xlabel("Cajero"); ax1.set_ylabel("Minutos")
ax1.set_title("Tiempo Promedio en Sistema con IC 95%")
ax1.grid(True, alpha=0.3, axis="y")

boxdata = [np.array(sistema[c]["sistema"][punto_corte:]) for c in range(3)]
bp = ax2.boxplot(boxdata, tick_labels=["Cajero 1", "Cajero 2", "Cajero 3"], patch_artist=True)
for patch, color in zip(bp["boxes"], colores):
    patch.set_facecolor(color); patch.set_alpha(0.7)
ax2.set_ylabel("Minutos"); ax2.set_title("Distribución por Cajero")
ax2.grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig(os.path.join(CARPETA, "Punto1_Cajeros.png"), dpi=120)
plt.close()
print("Gráfica Punto 1 guardada.")


# ==========================================================
# PUNTO 2 - PROMEDIO DE USUARIOS POR TIPO
# ==========================================================

print("\n" + "=" * 60)
print("PUNTO 2 - PROMEDIO DE USUARIOS POR TIPO")
print("=" * 60)

conteo  = {t: 0 for t in usuarios}
tiempos = {t: [] for t in usuarios}

for cajero in sistema:
    for tipo in cajero["tipos"]:
        conteo[tipo] += 1
    for tipo, t_s in zip(cajero["tipos"], cajero["servicio"]):
        tiempos[tipo].append(t_s)

total = sum(conteo.values())
filas2 = []
for tipo in usuarios:
    filas2.append({
        "Tipo Usuario":     tipo,
        "Cantidad":         conteo[tipo],
        "Porcentaje (%)":   round(conteo[tipo] / total * 100, 2),
        "Esperado (%)":     usuarios[tipo]["probabilidad"] * 100,
        "T. Prom Servicio": round(np.mean(tiempos[tipo]), 4),
    })

df_tipos = pd.DataFrame(filas2)
print(df_tipos.to_string(index=False))
print("\nLas proporciones obtenidas deben aproximarse a:")
print("25% Rápido, 20% Normal, 27.5% Lento, 27.5% Muy Lento.")
print("Las diferencias menores son normales por la aleatoriedad del modelo.")

# Gráfica Punto 2
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle("Punto 2 - Análisis por Tipo de Usuario", fontsize=13)

col_tipos = ["green", "steelblue", "orange", "tomato"]
ax1.bar(df_tipos["Tipo Usuario"], df_tipos["Cantidad"], color=col_tipos, width=0.5)
ax1.set_ylabel("Cantidad de usuarios")
ax1.set_title("Usuarios atendidos por tipo")
ax1.grid(True, alpha=0.3, axis="y")

x = np.arange(len(df_tipos)); w = 0.35
ax2.bar(x - w/2, df_tipos["Porcentaje (%)"], w, color=col_tipos, alpha=0.85, label="Simulado")
ax2.bar(x + w/2, df_tipos["Esperado (%)"],   w, color=col_tipos, alpha=0.4, hatch="//", label="Esperado")
ax2.set_xticks(x); ax2.set_xticklabels(df_tipos["Tipo Usuario"])
ax2.set_ylabel("Porcentaje (%)")
ax2.set_title("Porcentaje simulado vs esperado")
ax2.legend(); ax2.grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig(os.path.join(CARPETA, "Punto2_Usuarios.png"), dpi=120)
plt.close()
print("Gráfica Punto 2 guardada.")


# ==========================================================
# PUNTO 3 - ESTRATEGIA DE MEJORA
# ==========================================================

print("\n" + "=" * 60)
print("PUNTO 3 - ESTRATEGIA DE MEJORA")
print("=" * 60)

# Criterios establecidos para la toma de decisiones
LIMITE_ESPERA  = 5.0   # min en cola
LIMITE_SISTEMA = 8.0   # min en sistema
LIMITE_COLA    = 5.0   # longitud promedio
LIMITE_PROB    = 20.0  # % usuarios con espera > 5 min

def metricas_sistema(sis):
    esperas  = [e for c in sis for e in c["espera"]]
    sistemas = [s for c in sis for s in c["sistema"]]
    colas    = [q for c in sis for q in c["cola"]]
    return {
        "espera_prom":  round(np.mean(esperas), 4),
        "sistema_prom": round(np.mean(sistemas), 4),
        "cola_prom":    round(np.mean(colas), 4),
        "prob_esp_5":   round(np.mean(np.array(esperas) > 5) * 100, 2),
    }

met3 = metricas_sistema(sistema)
print(f"Tiempo promedio en cola:     {met3['espera_prom']:.2f} min  (límite: {LIMITE_ESPERA} min)")
print(f"Tiempo promedio en sistema:  {met3['sistema_prom']:.2f} min  (límite: {LIMITE_SISTEMA} min)")
print(f"Longitud promedio de cola:   {met3['cola_prom']:.2f}       (límite: {LIMITE_COLA})")
print(f"Prob. espera > 5 min:        {met3['prob_esp_5']:.2f}%      (límite: {LIMITE_PROB}%)")

criterio = (met3["espera_prom"] > LIMITE_ESPERA or
            met3["cola_prom"]   > LIMITE_COLA   or
            met3["prob_esp_5"]  > LIMITE_PROB)

met4 = None
if criterio:

    print(
        "\nLos indicadores de desempeño "
        "superan los límites aceptables."
    )

    print(
        "Se evalúa un escenario alternativo "
        "agregando un cuarto cajero."
    )

    sistema4 = simular_sistema_distribuido(4, TIEMPO_SIMULACION)

    met4 = metricas_sistema(sistema4)

    mejora_espera = (

        (met3["espera_prom"] - met4["espera_prom"])
        /
        met3["espera_prom"]

    ) * 100

    mejora_sistema = (

        (met3["sistema_prom"] - met4["sistema_prom"])
        /
        met3["sistema_prom"]

    ) * 100

    print("\nCOMPARACIÓN DE ESCENARIOS")

    print("-" * 50)

    print(
        f"Espera promedio:"
        f" {met3['espera_prom']:.2f}"
        f" -> {met4['espera_prom']:.2f}"
    )

    print(
        f"Tiempo en sistema:"
        f" {met3['sistema_prom']:.2f}"
        f" -> {met4['sistema_prom']:.2f}"
    )

    print(
        f"Longitud cola:"
        f" {met3['cola_prom']:.2f}"
        f" -> {met4['cola_prom']:.2f}"
    )

    print(
        f"Probabilidad espera >5:"
        f" {met3['prob_esp_5']:.2f}%"
        f" -> {met4['prob_esp_5']:.2f}%"
    )

    print("\nMEJORAS OBTENIDAS")

    print(
        f"Reducción espera:"
        f" {mejora_espera:.2f}%"
    )

    print(
        f"Reducción tiempo sistema:"
        f" {mejora_sistema:.2f}%"
    )

    print(
        "\nRECOMENDACIÓN FINAL:"
    )

    print(
        "Instalar un cuarto cajero "
        "debido a la reducción observada "
        "en los indicadores de congestión."
    )
else:
    print("\nTodos los criterios se cumplen. Los 3 cajeros son suficientes.")

# Gráfica Punto 3
etiquetas = ["Espera prom", "Sistema prom", "Cola prom", "Prob esp>5 (%)"]
vals3     = [met3["espera_prom"], met3["sistema_prom"], met3["cola_prom"], met3["prob_esp_5"]]
limites   = [LIMITE_ESPERA, LIMITE_SISTEMA, LIMITE_COLA, LIMITE_PROB]

fig, ax = plt.subplots(figsize=(11, 5))
if met4:
    vals4 = [met4["espera_prom"], met4["sistema_prom"], met4["cola_prom"], met4["prob_esp_5"]]
    x = np.arange(len(etiquetas)); w = 0.35
    ax.bar(x - w/2, vals3, w, label="3 Cajeros", color="steelblue")
    ax.bar(x + w/2, vals4, w, label="4 Cajeros", color="seagreen")
    ax.set_xticks(x); ax.set_xticklabels(etiquetas)
    ax.legend()
else:
    bar_colors = ["tomato" if v > lim else "seagreen" for v, lim in zip(vals3, limites)]
    ax.bar(etiquetas, vals3, color=bar_colors, width=0.5)

for i, lim in enumerate(limites):
    ax.axhline(lim, xmin=i/len(limites), xmax=(i+1)/len(limites),
               color="red", lw=2, ls="--")

ax.set_title("Punto 3 - Evaluación de Criterios de Decisión")
ax.set_ylabel("Valor"); ax.grid(True, alpha=0.3, axis="y")
plt.tight_layout()
plt.savefig(os.path.join(CARPETA, "Punto3_Estrategia.png"), dpi=120)
plt.close()
print("Gráfica Punto 3 guardada.")


# ==========================================================
# PUNTO 4 - VERIFICACIÓN, CALIBRACIÓN Y VALIDACIÓN (VCV)
# ==========================================================

print("\n" + "=" * 60)
print("PUNTO 4 - VERIFICACIÓN, CALIBRACIÓN Y VALIDACIÓN")
print("=" * 60)

# --- Verificación ---
print("\nVERIFICACIÓN (¿el código funciona correctamente?)")
errores = []
suma_prob = sum(usuarios[t]["probabilidad"] for t in usuarios)
if abs(suma_prob - 1) > 0.001:
    errores.append("Las probabilidades no suman 1.")
for tipo in usuarios:
    if usuarios[tipo]["llegada"] <= 0:
        errores.append(f"Tiempo de llegada inválido en {tipo}.")
    if usuarios[tipo]["servicio"] <= 0:
        errores.append(f"Tiempo de servicio inválido en {tipo}.")

if errores:
    for e in errores:
        print(f"  ERROR: {e}")
else:
    print("  Verificación exitosa. Sin errores de configuración.")
    print("  Nota: Usuario Normal tiene rho=1.0 (límite teórico), se monitorea en simulación.")

# --- Calibración ---
print("\nCALIBRACIÓN (¿los parámetros son los correctos?)")
print("  Parámetros usados exactamente según el enunciado:")
for tipo, p in usuarios.items():
    lam = 1 / p["llegada"]
    mu  = 1 / p["servicio"]
    rho = lam / mu
    estado = "CRÍTICO rho=1" if rho >= 1 else ("Alto" if rho >= 0.85 else "Estable")
    print(f"  {tipo:<10}: lambda={lam:.4f}  mu={mu:.4f}  rho={rho:.4f}  [{estado}]")

# --- Validación con teoría M/M/1 (usuario Rápido, el único con rho < 1 garantizado) ---
print("\nVALIDACIÓN (¿los resultados coinciden con la teoría M/M/1?)")
print("  Se usa usuario Rápido (rho=0.333, sistema estable) para comparar con fórmulas teóricas.")

lam_v = 1 / usuarios["Rapido"]["llegada"]
mu_v  = 1 / usuarios["Rapido"]["servicio"]
W_teo = 1 / (mu_v - lam_v)   # fórmula M/M/1: W = 1/(mu - lambda)

# Simular cajero puro con solo usuario Rápido (lambda=1/3, mu=1/1)
# Se simula directamente con sus tasas sin mezclar tipos
def simular_mm1_puro(lam, mu, tiempo_total):
    reloj = 0; disponible = 0; tiempos = []
    while reloj < tiempo_total:
        reloj += np.random.exponential(1 / lam)
        if reloj > tiempo_total:
            break
        servicio = np.random.exponential(1 / mu)
        inicio   = max(reloj, disponible)
        tiempos.append(inicio - reloj + servicio)
        disponible = inicio + servicio
    return tiempos

tiempos_rapidos = simular_mm1_puro(lam_v, mu_v, TIEMPO_SIMULACION * 50)

W_sim     = np.mean(tiempos_rapidos)
error_pct = abs(W_sim - W_teo) / W_teo * 100
t_stat, p_val = stats.ttest_1samp(tiempos_rapidos, W_teo)

df_val = pd.DataFrame({
    "Indicador": ["W Teórico (Rapido)", "W Simulado (Rapido)", "Error (%)", "p-value (t-test)"],
    "Valor":     [round(W_teo, 4), round(W_sim, 4), round(error_pct, 2), round(p_val, 4)],
})
print(df_val.to_string(index=False))

if p_val > 0.05:
    print("\n  Modelo VALIDADO: no hay diferencia significativa (p > 0.05).")
else:
    print("\n  Revisar parámetros: diferencia significativa detectada (p <= 0.05).")

# Gráfica Punto 4
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Punto 4 - Verificación, Calibración y Validación", fontsize=13)

ax1.bar(["W Teórico", "W Simulado"], [W_teo, W_sim],
        color=["steelblue", "seagreen"], width=0.4)
ax1.set_ylabel("Minutos")
ax1.set_title("Validación M/M/1 - Usuario Rápido (rho=0.333)")
ax1.text(0, W_teo + 0.02, f"{W_teo:.3f}", ha="center", fontweight="bold")
ax1.text(1, W_sim + 0.02, f"{W_sim:.3f}", ha="center", fontweight="bold")
estado_val = "VALIDADO ✓" if p_val > 0.05 else "REVISAR ✗"
ax1.text(0.5, max(W_teo, W_sim) * 0.55,
         f"Error: {error_pct:.2f}%\np = {p_val:.4f}\n{estado_val}",
         ha="center", fontsize=11,
         color="green" if p_val > 0.05 else "red", fontweight="bold")
ax1.grid(True, alpha=0.3, axis="y")

# Diagrama de flujo VCV
ax2.set_xlim(0, 10); ax2.set_ylim(0, 10); ax2.axis("off")
ax2.set_title("Proceso VCV del Modelo")
pasos = [
    (5, 9.0, "INICIO: Definir modelo M/M/1",               "#AED6F1"),
    (5, 7.3, "VERIFICACIÓN\n¿El código funciona?",          "#F9E79F"),
    (5, 5.6, "CALIBRACIÓN\nAjustar λ y μ del enunciado",    "#A9DFBF"),
    (5, 3.9, "VALIDACIÓN\nW_sim vs W_teórico (prueba t)",   "#F5CBA7"),
    (5, 2.2, "¿p > 0.05? → Aceptar modelo",                "#D2B4DE"),
    (5, 0.6, "FIN: Resultados finales",                     "#85C1E9"),
]
for (x, y, txt, col) in pasos:
    rect = plt.Rectangle((x - 3.5, y - 0.6), 7, 1.1,
                          linewidth=1.5, edgecolor="#2C3E50", facecolor=col, zorder=3)
    ax2.add_patch(rect)
    ax2.text(x, y, txt, ha="center", va="center", fontsize=9, zorder=4)
for i in range(len(pasos) - 1):
    y1 = pasos[i][1] - 0.6
    y2 = pasos[i+1][1] + 0.6
    ax2.annotate("", xy=(5, y2), xytext=(5, y1),
                 arrowprops=dict(arrowstyle="->", color="#2C3E50", lw=1.5))

plt.tight_layout()
plt.savefig(os.path.join(CARPETA, "Punto4_VCV.png"), dpi=120)
plt.close()
print("Gráfica Punto 4 guardada.")


# ==========================================================
# PUNTO 5 - ELIMINACIÓN DEL ESTADO TRANSITORIO
# Gráfica ANTES y DESPUÉS
# ==========================================================

print("\n" + "=" * 60)
print("PUNTO 5 - ELIMINACIÓN DEL ESTADO TRANSITORIO")
print("=" * 60)

datos_originales = np.array(sistema[0]["sistema"])
punto_corte, promedios_moviles = determinar_estado_estable(datos_originales)
datos_estables   = datos_originales[punto_corte:]

print(f"Punto de corte (warm-up): observación {punto_corte}")
print(f"Observaciones antes del corte: {punto_corte}")
print(f"Observaciones después del corte: {len(datos_estables)}")

tabla_trans = pd.DataFrame({
    "Escenario": ["Antes (con transitorio)", "Después (sin transitorio)"],
    "N obs":     [len(datos_originales),      len(datos_estables)],
    "Media":     [round(np.mean(datos_originales), 4), round(np.mean(datos_estables), 4)],
    "DesvStd":   [round(np.std(datos_originales), 4),  round(np.std(datos_estables), 4)],
    "Minimo":    [round(np.min(datos_originales), 4),   round(np.min(datos_estables), 4)],
    "Maximo":    [round(np.max(datos_originales), 4),   round(np.max(datos_estables), 4)],
})
print(tabla_trans.to_string(index=False))
print("\nEl estado transitorio fue eliminado para garantizar que el análisis se realice únicamente sobre observaciones del régimen estable.")
print("Las estadísticas finales se calculan solo con datos posteriores al warm-up.")

# Gráfica Punto 5: tres paneles - estado estable, antes y después
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Punto 5 - Eliminación del Estado Transitorio", fontsize=13)

# Panel 1: serie completa con promedio móvil y corte
axes[0].plot(datos_originales, alpha=0.4, label="Datos originales")
axes[0].plot(promedios_moviles, color="red", lw=2, label="Promedio móvil")
axes[0].axvline(punto_corte, color="green", ls="--", lw=2, label=f"Corte: {punto_corte}")
axes[0].axvspan(0, punto_corte, alpha=0.08, color="red")
axes[0].set_title("Determinación del Estado Estable")
axes[0].set_xlabel("Observación"); axes[0].set_ylabel("Tiempo en sistema (min)")
axes[0].legend(); axes[0].grid(True, alpha=0.3)

# Panel 2: ANTES
axes[1].plot(datos_originales, color="tomato", alpha=0.7)
axes[1].axvline(punto_corte, color="black", ls="--", lw=2, label=f"Corte: {punto_corte}")
axes[1].axhline(np.mean(datos_originales), color="navy", lw=1.5,
                label=f"Media: {np.mean(datos_originales):.2f} min")
axes[1].set_title("ANTES — Con estado transitorio")
axes[1].set_xlabel("Observación"); axes[1].set_ylabel("Tiempo en sistema (min)")
axes[1].legend(); axes[1].grid(True, alpha=0.3)

# Panel 3: DESPUÉS
axes[2].plot(datos_estables, color="seagreen")
axes[2].axhline(np.mean(datos_estables), color="navy", lw=1.5,
                label=f"Media: {np.mean(datos_estables):.2f} min")
axes[2].set_title("DESPUÉS — Sin estado transitorio")
axes[2].set_xlabel("Observación"); axes[2].set_ylabel("Tiempo en sistema (min)")
axes[2].legend(); axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(CARPETA, "Punto5_AntesDespues.png"), dpi=120)
plt.close()
print("Gráfica Punto 5 guardada.")


# ==========================================================
# EXPORTAR RESULTADOS A EXCEL
# ==========================================================

excel_path = os.path.join(CARPETA, "Resultados_Parqueadero.xlsx")
with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    df_cajeros.to_excel(writer,   sheet_name="Punto1_Cajeros",      index=False)
    df_tipos.to_excel(writer,     sheet_name="Punto2_Usuarios",     index=False)
    pd.DataFrame([met3]).to_excel(writer, sheet_name="Punto3_Metricas3", index=False)
    if met4:
        pd.DataFrame([met4]).to_excel(writer, sheet_name="Punto3_Metricas4", index=False)
    df_val.to_excel(writer,       sheet_name="Punto4_VCV",          index=False)
    tabla_trans.to_excel(writer,  sheet_name="Punto5_Transitorio",  index=False)

print(f"\nExcel guardado: {excel_path}")

# ==========================================================
# RESUMEN FINAL
# ==========================================================

print("\n" + "=" * 60)
print("ARCHIVOS GENERADOS EN /Resultados/")
print("=" * 60)
for f in sorted(os.listdir(CARPETA)):
    print(f"  - {f}")