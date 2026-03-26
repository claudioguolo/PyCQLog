from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AdifRecord:
    fields: dict[str, str]

    def get(self, key: str, default: str = "") -> str:
        return self.fields.get(key.upper(), default)


class AdifParser:
    def parse(self, content: str) -> list[AdifRecord]:
        upper = content.upper()
        eoh_index = upper.find("<EOH>")
        if eoh_index >= 0:
            content = content[eoh_index + 5 :]

        records: list[AdifRecord] = []
        current: dict[str, str] = {}
        index = 0

        while index < len(content):
            if content[index] != "<":
                index += 1
                continue

            end = content.find(">", index)
            if end == -1:
                break

            token = content[index + 1 : end].strip()
            token_upper = token.upper()

            if token_upper == "EOR":
                if current:
                    records.append(AdifRecord(fields=current))
                    current = {}
                index = end + 1
                continue

            parts = token.split(":")
            if len(parts) < 2:
                index = end + 1
                continue

            field_name = parts[0].strip().upper()
            try:
                field_length = int(parts[1].strip())
            except ValueError:
                index = end + 1
                continue

            value_start = end + 1
            value_end = value_start + field_length
            value = content[value_start:value_end]
            current[field_name] = value.strip()
            index = value_end

        if current:
            records.append(AdifRecord(fields=current))

        return records
