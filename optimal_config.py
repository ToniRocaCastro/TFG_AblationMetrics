import pandas as pd
from sklearn.model_selection import KFold

''' DECLARACIONES'''
csv_path = "" # Quitado por privacidad
group_cols = ["Node", "Parameter", "Value"]
n_folds = 3
alpha = 0.02
all_best_configs = []

''' ACCIONES '''
if __name__ == '__main__':
    # Leer resultados
    df_results = pd.read_csv(csv_path, delimiter=";")

    # Filtrar solo configuraciones de tipo "parameter"
    df_params = df_results[df_results["Type"] == "parameters"]

    # Obtener nombres únicos de personas
    persons = df_params['Person'].unique()

    # Repetir para cada fold
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)
    for fold, (train_idx, test_idx) in enumerate(kf.split(persons)):

        # División por persona
        train_persons = persons[train_idx]
        test_persons = persons[test_idx]
        df_train = df_params[df_params['Person'].isin(train_persons)]
        df_test = df_params[df_params['Person'].isin(test_persons)]

        # ****** PARAMS ******
        # Calcular medias en TRAIN
        train_stats = (
            df_train
            .groupby(group_cols)["Cosine_Similarity"]
            .mean()
            .reset_index()
            .rename(columns={"Cosine_Similarity": "cosine_train"})
        )

        # Obtener mejor configuración en TRAIN
        best_train = (
            train_stats
            .sort_values(by=["Node", "Parameter", "cosine_train"], ascending=[True, True, False])
            .groupby(["Node", "Parameter"], group_keys=False)
            .head(1)
            .copy()
        )

        # Media en Test para esas configuraciones
        test_stats = (
            df_test
            .groupby(group_cols)["Cosine_Similarity"]
            .mean()
            .reset_index()
            .rename(columns={"Cosine_Similarity": "cosine_test"})
        )

        # Juntar train y test
        merged = best_train.merge(test_stats, on=group_cols, how="left")
        merged["fold"] = fold
        all_best_configs.append(merged)

    # Unir todos los folds
    df_all = pd.concat(all_best_configs, ignore_index=True)

    summary = (
        df_all
        .groupby(group_cols)
        .agg(
            avg_cosine_test = ("cosine_test", "mean"),
            std_cosine_test = ("cosine_test", "std"),
            count_test_evals = ("fold", "count")
        )
        .reset_index()
    )

    # Calcular score penalizado por varianza
    summary["score"] = summary["avg_cosine_test"] + alpha * (summary["count_test_evals"] / n_folds)

    # Separar configuraciones óptimas por criterio
    mejores_configs = (
        summary
        .sort_values(by=["Node", "Parameter", "score"], ascending=[True, True, False])
        .groupby(["Node", "Parameter"], group_keys=False)
        .head(1)
        .reset_index(drop=True)
    )

    # Añadir configuración de bypass por nodo
    df_bypass = df_results[df_results["Type"] == "bypass"]

    bypass_summary = (
        df_bypass
        .groupby("Node")["Cosine_Similarity"]
        .mean()
        .reset_index()
        .rename(columns={"Cosine_Similarity": "bypass_cosine"})
    )

    # Comparar con las mejores configuraciones
    comparativa = (
        mejores_configs
        .merge(bypass_summary, on="Node", how="left")
        .assign(bypass_better=lambda df: df["bypass_cosine"] > df["avg_cosine_test"])
    )

    # Mostrar resultados obtenidos
    print("\n*******  Comparativa con configuración bypass: ******* ")
    print(comparativa[["Node", "Parameter", "Value", "avg_cosine_test", "bypass_cosine", "bypass_better"]].to_string(index=False))
    print("\n******* Mejores configuraciones por estabilidad: ******* ")
    print(mejores_configs.to_string(index=False))









