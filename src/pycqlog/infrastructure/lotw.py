from __future__ import annotations
import subprocess
from pathlib import Path


class TqslRunner:
    def __init__(self, executable_path: str = "tqsl", station_location: str = "") -> None:
        self._executable_path = executable_path.strip() or "tqsl"
        self._station_location = station_location.strip()

    def build_tq8(self, adif_path: Path, output_tq8: Path) -> tuple[bool, str]:
        if not adif_path.exists():
            return False, f"ADIF file not found: {adif_path}"

        # Standard TQSL automation to generate .tq8 without uploading
        cmd = [self._executable_path, "-batch", "-a", "out", "-o", str(output_tq8)]
        if self._station_location:
            cmd.extend(["-l", self._station_location])
            
        cmd.append(str(adif_path))

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                output = result.stdout.strip() or result.stderr.strip()
                return True, output or f"Sucesso. Arquivo assinado: {output_tq8.name}"
            else:
                return False, result.stderr.strip() or result.stdout.strip() or "Erro desconhecido no TQSL."
        except FileNotFoundError:
            return False, f"TQSL nao encontrado em '{self._executable_path}'. Verifique o caminho na aba Configs > Integrations > LoTW."
        except Exception as e:
            return False, f"Falha ao executar TQSL: {e}"
