import csv
import json
from pathlib import Path
from typing import Optional

from src.mantenedor import MODELOS_DIR, ESTADISTICA_DIR, CROSS_VALIDATION_DIR, COMPARATIVOS_DIR
from src.mantenedor import MODELS_DIR as MODELS_BASE_DIR


class ReportRepository:
    @staticmethod
    def _read_csv(file_path: Path) -> Optional[list[dict]]:
        if not file_path.exists():
            return None
        try:
            with open(file_path, newline="", encoding="utf-8") as f:
                return [dict(r) for r in csv.DictReader(f)]
        except Exception:
            return None

    @staticmethod
    def _read_txt(file_path: Path) -> Optional[str]:
        if not file_path.exists():
            return None
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception:
            return None

    def get_ranking(self) -> Optional[list[dict]]:
        return self._read_csv(MODELOS_DIR / "ranking_modelos.csv")

    def get_best_model(self) -> Optional[dict]:
        """Read modelo_final.json — the single source of truth for best model."""
        path = MODELS_BASE_DIR / "modelo_final" / "modelo_final.json"
        if not path.exists():
            return None
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def get_cross_validation(self) -> Optional[list[dict]]:
        return self._read_csv(CROSS_VALIDATION_DIR / "cross_validation_resultados.csv")

    def get_cross_validation_by_fold(self) -> Optional[list[dict]]:
        return self._read_csv(CROSS_VALIDATION_DIR / "cross_validation_por_fold.csv")

    def get_model_comparison_ranking(self) -> Optional[list[dict]]:
        return self._read_csv(MODELOS_DIR / "ranking_modelos.csv")

    def get_model_comparison(self) -> Optional[list[dict]]:
        return self._read_csv(COMPARATIVOS_DIR / "comparacion_general_modelos.csv")

    def get_effect_size(self) -> Optional[list[dict]]:
        return self._read_csv(ESTADISTICA_DIR / "tamano_efecto.csv")


    def get_bootstrap_intervals(self) -> Optional[list[dict]]:
        return self._read_csv(ESTADISTICA_DIR / "intervalos_confianza_bootstrap.csv")

    def get_mcnemar_results(self) -> Optional[list[dict]]:
        return self._read_csv(ESTADISTICA_DIR / "mcnemar_resultados.csv")

    def get_mcnemar_holm(self) -> Optional[list[dict]]:
        return self._read_csv(ESTADISTICA_DIR / "mcnemar_holm_posthoc.csv")

    def get_cochran_q(self) -> Optional[dict]:
        data = self._read_csv(ESTADISTICA_DIR / "cochran_q_resultado.csv")
        return data[0] if data else None
