# VineGuard-AI-Diagnostico-Uvas

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](#LICENSE)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-orange)](#app.py)

**VineGuard-AI-Diagnostico-Uvas** es una plataforma basada en Inteligencia Artificial y Deep Learning para la detección temprana y precisa de afecciones foliares en cultivos de vid. Mediante el uso de un framework multimodelo de Redes Neuronales Convolucionales (CNN) y un módulo de validación estadística rigurosa (métrica MCC y pruebas de McNemar), esta solución optimiza los tiempos de diagnóstico agrícola de forma notable, permitiendo generar reportes en formato PDF con recomendaciones agronómicas personalizadas para cada caso detectado.

---

## 🎯 Características Principales

* **Diagnóstico Multimodelo:** Evaluación simultánea empleando cuatro arquitecturas de red convolucional (CNN personalizada, MobileNetV2, EfficientNetB0 y DenseNet121).
* **Validación Estadística Avanzada:** Evaluación del rendimiento mediante el Coeficiente de Correlación de Matthews (MCC) y test de McNemar para contrastar la significancia entre modelos.
* **Informes Automatizados:** Generación instantánea de reportes técnicos detallados en formato PDF con acciones de mitigación recomendadas.
* **Interfaz Interactiva:** Aplicación web dinámica construida con Streamlit que facilita el diagnóstico individual y el análisis estadístico masivo.

---

## 📂 Arquitectura del Repositorio

La distribución del código y los recursos del proyecto se detalla a continuación:

```text
VineGuard-AI-Diagnostico-Uvas/
├── dataset/                     # Directorios de datos clasificados
│   ├── train/                   # Set de entrenamiento
│   ├── val/                     # Set de validación
│   └── test/                    # Set de pruebas
├── models/                      # Modelos compilados y gráficos de métricas
│   ├── class_names.npy          # Etiquetas de las clases
│   ├── cnn_simple.h5            # Modelo CNN propio
│   ├── mobilenetv2.h5           # Modelo basado en MobileNetV2
│   ├── efficientnetb0.h5        # Modelo basado en EfficientNetB0
│   └── densenet121.h5           # Modelo basado en DenseNet121
├── src/                         # Módulos y scripts principales
│   ├── prepare_dataset.py       # Preprocesamiento y división del dataset
│   ├── train_model_1_cnn.py     # Script de entrenamiento: CNN Simple
│   ├── train_model_2_mobilenet.py # Script de entrenamiento: MobileNetV2
│   ├── train_model_3_efficientnetb0_fixed.py # Script de entrenamiento: EfficientNetB0
│   ├── train_densenet121.py    # Script de entrenamiento: DenseNet121
│   ├── mantenedor.py           # Gestión de rutas y clases del sistema
│   └── app.py                  # Código fuente de la interfaz Streamlit
├── requirements.txt             # Dependencias del proyecto
└── README.md                    # Documentación del sistema (este archivo)
```

---

## ⚙️ Instalación y Configuración

Siga los siguientes pasos para configurar y ejecutar el entorno de desarrollo localmente:

### 1. Clonar el repositorio y configurar el entorno virtual
```bash
git clone https://github.com/AnonyMovsJs/Diagnostico-Uvas-CNN-IA.git
cd Diagnostico-Uvas-CNN-IA
python -m venv venv
```

* **En Linux/macOS:**
  ```bash
  source venv/bin/activate
  ```
* **En Windows:**
  ```bash
  venv\Scripts\activate
  ```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

---

## 🚀 Guía de Uso y Entrenamiento

### Entrenamiento de Modelos
Para iniciar el ciclo de entrenamiento de los clasificadores con su dataset:

1. Coloque y extraiga las imágenes del dataset en la carpeta `dataset/`. (Recomendado: [PlantVillage Grape en Kaggle](https://www.kaggle.com/datasets/piyushmishra1999/plantvillage-grape)).
2. Ejecute de manera secuencial los scripts correspondientes:
   ```bash
   python prepare_dataset.py
   python train_model_1_cnn.py
   python train_model_2_mobilenet.py
   python train_model_3_efficientnetb0_fixed.py
   python train_densenet121.py
   ```
Cada ejecución generará su respectivo modelo guardado en la carpeta `models/` junto con sus gráficos de evolución del entrenamiento.

### Lanzamiento de la Aplicación Web
Para ejecutar la consola de diagnóstico interactiva:
```bash
streamlit run app.py
```

La interfaz cuenta con cuatro secciones de trabajo:
* **Diagnóstico Individual:** Carga de imágenes (JPG/PNG) para clasificación multimodelo simultánea y descarga del reporte PDF.
* **Análisis Estadístico:** Visualización comparativa de curvas de entrenamiento y puntajes MCC.
* **Validación McNemar:** Ejecución de pruebas estadísticas no paramétricas de McNemar para evaluar discrepancias entre clasificadores.
* **Información Agronómica:** Catálogo detallado de patologías evaluadas con pautas de intervención sugeridas.

---

## 💻 Ejecución en la Nube (Google Colab)

Si prefiere ejecutar el entrenamiento o pruebas sin configurar recursos locales, puede usar nuestro cuaderno interactivo:

[![Abrir en Google Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1b6mvepHBPD60txpCcEhLC-7mRYNWNTPw?usp=sharing)

---

## 🔬 Rendimiento y Resultados Obtenidos

El entrenamiento y validación se realizaron empleando el dataset **PlantVillage Grape**, que agrupa las muestras en 4 clases diferenciadas:
* *Black rot* (Podredumbre negra)
* *Esca* (Esca de la vid)
* *Leaf blight* (Tizón de la hoja)
* *Healthy* (Hojas sanas)

### Precisión Registrada por Modelo:
* **CNN Personalizada:** ~96.8% (Tiempo promedio: ~285 ms)
* **MobileNetV2:** ~98.0% (Tiempo promedio: ~826 ms)
* **EfficientNetB0:** ~95.1% (Tiempo promedio: ~937 ms)
* **DenseNet121:** ~98.0% (Tiempo promedio: ~1.7 s)

El sistema integra un algoritmo de consenso de predicciones que eleva la robustez final del diagnóstico ante imágenes con ruido o capturadas en condiciones de iluminación no controladas.

---

## 📚 Referencias Bibliográficas

1. Mishra, P. *PlantVillage Grapevine Disease Dataset*. Kaggle.
2. Sandler, M. et al. *MobileNetV2: Inverted Residuals and Linear Bottlenecks*, CVPR 2018.
3. Tan, M. & Le, Q. *EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks*, ICML 2019.
4. Huang, G. et al. *Densely Connected Convolutional Networks*, CVPR 2017.

## Créditos y adaptación

Este proyecto fue desarrollado con fines académicos como una adaptación, reorganización y mejora de una base previa relacionada con el diagnóstico de enfermedades en hojas de uva mediante redes neuronales convolucionales.

La presente versión incorpora una estructura propia de carpetas, preparación automatizada del dataset, scripts de entrenamiento separados por arquitectura, validación estadística, generación de reportes PDF y adaptación de la interfaz en Streamlit para el contexto del trabajo académico.

El dataset utilizado corresponde a imágenes de hojas de vid clasificadas en las categorías Black rot, Esca, Leaf blight y Healthy.