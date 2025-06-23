import pandas as pd

''' DECLARACIONES'''
# Rutas a los archivos CSV
detected_faces_path = "" # Quitado por privacidad
non_detected_faces_path = "" # Quitado por privacidad

''' ACCIONES '''
# Cargar CSV
detected_faces_df = pd.read_csv(detected_faces_path, delimiter=";")
non_detected_faces_df = pd.read_csv(non_detected_faces_path, delimiter=";")

# ****** DETECCIÓN ******
# Obtener la longitud de ambos datsets y calcular el porcentaje de imágenes en las que se ha detectado una cara
detected_faces_length = detected_faces_df.shape[0]
non_detected_faces_length = non_detected_faces_df.shape[0]
total_length = detected_faces_length + non_detected_faces_length
print(f"Imágenes generadas: {total_length}\n")
percentatge_detection = (detected_faces_length/total_length) * 100
print(f"Imágenes con rostro detectado: {detected_faces_length} --- Imágenes con rostro no detectado: {non_detected_faces_length} --- Porcentaje de detecciones totales {percentatge_detection:.3f}%\n")


# ****** RECONOCIMIENTO ******
# Número de imágenes con Same_Identity = True
recognised_faces_length = detected_faces_df[detected_faces_df["Same_Identity"]==True].shape[0]
# Número de imágenes con Same_Identity = False
non_recognised_faces_length = detected_faces_df[detected_faces_df["Same_Identity"]==False].shape[0]
# Obtener el porcentaje de imágenes reconocidas entre las detectadas
percentatge_recognition = (recognised_faces_length / detected_faces_length) * 100
percentatge_recognition_total = (recognised_faces_length / total_length) * 100
print(f" Imágenes con rostro reconocido: {recognised_faces_length} --- Imágenes con rostro no reconocido: {non_recognised_faces_length} --- Porcentaje de reconocimientos del total de imágenes en las que se ha detectado un rostro: {percentatge_recognition:.3f}% ---  Porcentaje de reconocimientos totales:{percentatge_recognition_total:.3f}%\n")



# ****** ESTADÍSTICAS ******

# PERSONAS
# Top 5 más reconocidas
top_recognised_people = (
    detected_faces_df[detected_faces_df["Same_Identity"]==True]
    .groupby("Person").size()
    .sort_values(ascending=False)
    .head(5)
)
print(f"TOP 5 personas más imágenes reconocidas (entre las detectadas): \n{top_recognised_people}", "\n")

# Top 5 menos reconocidas
top_non_recognised_people = (
    detected_faces_df[detected_faces_df["Same_Identity"]==True]
    .groupby("Person").size()
    .sort_values(ascending=True)
    .head(5)
)
print(f"TOP 5 personas con menos imágenes reconocidas (entre las detectadas): \n{top_non_recognised_people}", "\n")

# NODOS
# Top 10 configuraciones con más fallos en la detección
top_non_detected_configs = (
    non_detected_faces_df
    .groupby(["Node", "Parameter", "Value"])
    .size()
    .sort_values(ascending=False)
    .head(10)
)
print(f"TOP 10 configuraciones que más veces han fallado en la detección: \n{top_non_detected_configs}", "\n")
