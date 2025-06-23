# FotografIA: Un análisis de un pipeline de generación de imágenes sintéticas fotorealistas

Este repositorio contiene el código fuente asociado al proyecto **FotografIA**, un estudio detallado sobre un pipeline de generación de imágenes fotorrealistas a partir de retratos artísticos, desarrollado en la plataforma [ComfyUI](https://github.com/comfyanonymous/ComfyUI).

El análisis se centra en estudiar el funcionamiento interno del pipeline, evaluando el impacto de sus componentes mediante técnicas de **ablación estructural** (omisión de nodos) y **ablación paramétrica** (modificación de parámetros). Se han llevado a cabo dos enfoques analíticos: uno **cualitativo**, basado en observaciones visuales, y otro **cuantitativo**, basado en una métrica de similitud facial.

## 📁 Estructura del repositorio
- Archivos PYTHON y JSON:
  - `run_comfyui_ablation_study.py` – Automatiza el estudio de ablación cuantitativo.
  - `face_comparison.py` – Compara rostros reales y generados mediante `Cosine Similarity`.
  - `optimal_config.py` – Extrae la configuración óptima uniparamétrica.
  - `stats_cuantitativo.py` – Resume estadísticamente los resultados cuantitativos.
  - `Original_Graphic.py` – Genera gráficos del pipeline original.
  - `Bypass_Graphic.py` – Gráficas del estudio de ablación estructural.
  - `Parameters_Graphic.py` – Gráficas del estudio de ablación paramétrica.
  - `Refacer.json` – Archivo de configuración del pipeline de ComfyUI.
- Carpetas:
  - `inputs_refacer/` – Retratos artísticos empleados como entrada.
  - `inputs_refacer_real/` – Fotografías reales de referencia.
  - `models/` – Modelos de reconocimiento/detección facial.
- Archivos CSV con resultados y errores detectados:
  - `results_face_comparison.csv` – Contiene los valores de similitud facial entre rostros reales y generados.
  - `failed_images.csv` – Lista las configuraciones que no generaron una imagen válida o sin rostro detectable.
  - `results_config_optima.csv` – Resultados obtenidos al evaluar la configuración óptima.
  - `failed_images_config_optima.csv` – Casos fallidos durante la evaluación de la configuración óptima.

## 🧠 Requisitos

1. Tener instalado [ComfyUI](https://github.com/comfyanonymous/ComfyUI).
2. Usar la extensión [ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager) para instalar automáticamente los nodos y modelos necesarios.
3. Importar el pipeline desde el archivo `Refacer.json`.
4. Instalar las dependencias de Python:

```bash
pip install -r requirements.txt
